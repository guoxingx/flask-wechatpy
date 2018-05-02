
import time
import random
import functools
import xmltodict
import urllib.parse

from flask import request, url_for, redirect
from wechatpy.component import ComponentVerifyTicketMessage
from wechatpy.component import ComponentUnauthorizedMessage
from wechatpy.crypto import PrpCrypto
from wechatpy.utils import to_text
from wechatpy import parse_message, create_reply
from wechatpy.exceptions import WeChatOAuthException
from wechatpy.events import SubscribeEvent, UnsubscribeEvent, ViewEvent

from ..base import WeChatBase
from ..utils import config_value
from .oauth import ComponentOAuth


class Component(WeChatBase):

    def authcall_url(self, pre_auth_code, redirect_uri):
        """
        url for component authorization.

        param: pre_auth_code: string: pre_auth_code for component.
        param: redirect_url : string: auth result redirect url.

        return: url for auth
        """
        urls = [
            'https://mp.weixin.qq.com/cgi-bin/',
            'componentloginpage?',
            'component_appid=',
            self.component_appid,
            '&pre_auth_code=',
            pre_auth_code,
            '&redirect_uri=',
            redirect_uri
        ]
        return ''.join(urls)

    def nickname_key_appid(self, appid):
        """
        公众号nickname的存储键
        """
        return 'mpnickname-appid:{}'.format(appid)

    def nickname_key(self, nickname):
        """
        """
        return 'mpnickname:{}'.format(nickname)

    def set_mp_nickname(self, appid, nickname):
        """
        设置公众号的nickname，可以用来替代url上的appid
        """
        self.session.set(self.nickname_key_appid(appid), nickname)
        self.session.set(self.nickname_key(nickname), appid)

    def get_nickname_by_appid(self, appid):
        """
        """
        return self.session.get(self.nickname_key_appid(appid))

    def get_appid_by_nickname(self, nickname):
        """
        """
        return self.session.get(self.nickname_key(nickname))

    def get_appid(self, data):
        """
        获取appid, 如果启用了mp nickname将从存储中读取appid
        """
        appid_or_nickname = data.get('appid') or request.args.get('appid')
        if not appid_or_nickname:
            raise AttributeError('appid not fount in router or url params.')

        if len(appid_or_nickname) < 10 and config_value('WECHAT_USE_MP_NICKNAME'):
            nickname_key = self.nickname_key(appid_or_nickname)
            appid = self.session.get(nickname_key)
            if not appid:
                if appid_or_nickname in [self.test_mp_appid, self.test_mp_nickname]:
                    self.session.set(self.nickname_key_appid(self.test_mp_appid), self.test_mp_nickname)
                    self.session.set(self.nickname_key(self.test_mp_nickname), self.test_mp_appid)
                    appid = self.test_mp_appid
                else:
                    raise AttributeError('mp nickname key {} not exits.'.format(appid_or_nickname))
            return appid
        return appid_or_nickname

    @property
    def test_mp_appid(self):
        return config_value('WECHAT_COMPONENT_TEST_APPID')

    @property
    def test_mp_nickname(self):
        return config_value('WECHAT_COMPONENT_TEST_NICKNAME')

    @property
    def test_openid(self):
        return config_value('WECHAT_COMPONENT_TEST_OPENID')

    def component_notify(self):
        """
        receive component ticket and unauthorized message.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kw):
                print('wechat component called.')
                data = xmltodict.parse(to_text(request.data))['xml']
                encrypt = str(data.get('Encrypt'))
                try:
                    decrypt = PrpCrypto(self.crypto.key).decrypt(encrypt, self.crypto._id)
                except Exception as e:
                    print('wechat componet decrypt error: {}. info: {}'.format(e, request.data))
                    return 'fail'

                message = xmltodict.parse(to_text(decrypt))['xml']
                if message.get('InfoType') == ComponentVerifyTicketMessage.type:
                    print('receive wechat component ticket message.')
                    o = ComponentVerifyTicketMessage(message)
                    self.session.set(o.type, o.verify_ticket, 600)
                    print('update component ticket success: {}'.format(self.component_verify_ticket))

                    self.refresh_all_authorizer_token()

                elif message.get('InfoType') == ComponentUnauthorizedMessage.type:
                    print('receive wechat component mp unauthorized message.')
                    print(message)

                else:
                    print('receive unkown wechat component message.')
                    print(message)

                res = func(*args, **kw)
                if res and res.lower() != 'success':
                    return 'fail'
                return 'success'

            return wrapper
        return decorator

    def component_authcall(self, callback_endpoint, callback_endpoint_blueprint=None,
                           **callback_endpoint_params):
        """
        decorator for component authorization router.
        create pre_auth_code to start request and response to callback url.

        request.wechat_msg.get("component_auth_url") for authorization url.

        param: callback_endpoint: string: endpoint of callback url.
        param: **callback_params: params for callback endpoint.
        """

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kw):
                preauthcode = self.create_preauthcode().get('pre_auth_code')
                redirect_url = url_for(callback_endpoint, **callback_endpoint_params)
                redirect_url = urllib.parse.quote_plus(request.url_root[:-1] + redirect_url)
                url = self.authcall_url(preauthcode, redirect_url)
                request.wechat_msg = {'component_authcall_url': url}
                return func(*args, **kw)

            return wrapper
        return decorator

    def component_authcallback(self):
        """
        decorator for component authorization callback router.

        request.wechat_smg.get("component_client") for WeChatComponentClient object.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kw):
                auth_code = str(request.args.get('auth_code'))
                client = self.get_client_by_authorization_code(auth_code)
                request.wechat_msg = {'component_client': client}

                self.save_authorizer_appid(client.appid)

                return func(*args, **kw)

            return wrapper
        return decorator

    def component_mp_notify(self):
        """
        decorator for component authorized mp notify router.
        decrypt message and encrypt the response of router function.

        request.wechat_msg.get("component_mp_content")
        request.wechat_msg.get("component_client")
        """
        def wrapper(func):
            @functools.wraps(func)
            def decorator(*args, **kw):
                mpappid = self.get_appid(kw)

                data = xmltodict.parse(to_text(request.data))['xml']
                signature = request.args.get('msg_signature')
                timestamp = request.args.get('timestamp')
                nonce = request.args.get('nonce')

                try:
                    print('data: {}, signature: {}, token: {}, aes_key: {}, appid: {}.'.format(
                        data, signature, self.crypto.token, self.crypto.key, self.crypto._id))
                    message = self.crypto.decrypt_message(data, signature, timestamp, nonce)
                except Exception as e:
                    print('[component mp notify.] fail to decrypt message: {}, request.data: {}'.format(data, request.data))
                    raise e
                    request.wechat_msg = {
                        'component_mp_content': '',
                        'client': self.get_client_by_appid(mpappid),
                        'component_mp_message': ''
                    }
                    return func(*args, **kw)

                message = parse_message(message)
                client = self.get_client_by_appid(mpappid)

                if isinstance(message, UnsubscribeEvent):
                    content = 'unsubscribe'
                elif isinstance(message, SubscribeEvent):
                    content = 'subscribe'
                elif isinstance(message, ViewEvent):
                    content = 'view'
                else:
                    content = message.content

                request.wechat_msg = {
                    'component_mp_content': content,
                    'client': client,
                    'component_mp_message': message,
                }
                return func(*args, **kw)

            return decorator
        return wrapper

    def get_user(self):
        """
        get user wechat info.
        """
        def wrapper(func):
            @functools.wraps(func)
            def decorator(*args, **kw):
                mpappid = self.get_appid(kw)
                if mpappid == self.test_mp_appid:
                    request.wechat_msg = {
                        'user': {'openid': self.test_openid},
                        'appid': mpappid,
                        'test': True
                    }
                    return func(*args, **kw)

                redirect_url = request.url
                scope = 'snsapi_userinfo'
                oauth = ComponentOAuth(mpappid, self.component_appid, self.access_token, redirect_url, scope=scope)
                code = request.args.get('code')
                if code:
                    oauth.get_openid(code)
                    try:
                        user_info = oauth.get_user_info()
                        request.wechat_msg = {
                            'user': user_info,
                            'appid': mpappid,
                            'client': self.get_client_by_appid(mpappid),
                        }
                        return func(*args, **kw)
                    except WeChatOAuthException as e:
                        print('[wechat component get_user] fail to get user info.\
                              mpappid: {}, component_appid: {}, access_token: {}'.format(
                              mpappid, self.component_appid, self.access_token))
                        raise e

                return redirect(oauth.authorize_url)
            return decorator
        return wrapper

    def text(self, res):
        """
        response text message to authorized mp user.
        """
        return self._reply(res)

    def news(self, title, description, image, url):
        """
        response news message to authorized mp user.
        """
        res = {
            'title': title,
            'description': description,
            'image': image,
            'url': url
        }
        return self._reply([res])

    def _reply(self, res):
        message = request.wechat_msg.get('component_mp_message', None) if request.wechat_msg else None
        res_data = str(create_reply(res, message=message, render=True))

        nonce = ('%.9f' % random.random())[2:]
        timestamp = str(int(time.time()))
        return self.crypto.encrypt_message(res_data, nonce, timestamp)

    @property
    def authorizer_appid_list_key(self):
        return self._redis_prefix + ':mp_appid_list'

    def get_authorizer_refresh_token_key(self, appid):
        return '{}:{}_refresh_token'.format(self._redis_prefix, appid)

    def save_authorizer_appid(self, appid):
        self._redis.sadd(self.authorizer_appid_list_key, appid)

    def get_authorizer_appid_list(self):
        appid_list = self._redis.smembers(self.authorizer_appid_list_key)
        return [appid.decode() if isinstance(appid, bytes) else appid for appid in appid_list]

    def refresh_all_authorizer_token(self):
        """
        """
        appid_list = self.get_authorizer_appid_list()
        for appid in appid_list:
            key = self.get_authorizer_refresh_token_key(appid)
            refresh_token = self._redis.get(key)
            if not refresh_token:
                print('refresh_token for {} was lost. we are fucked.'.format(appid))

            ttl = self._redis.ttl(key)
            print('appid: {} - refresh_token: {} - ttl: {}'.format(appid, refresh_token, ttl))
            if ttl:
                if ttl < 3600:
                    res = self.get_client_by_appid(appid).fetch_access_token()
                    print('mp({}) fetch_access_token res: {}'.format(appid, res))
