
import time
import random
import urllib
import logging
import functools
import xmltodict

from flask import request, url_for, redirect
from wechatpy.component import ComponentVerifyTicketMessage
from wechatpy.component import ComponentUnauthorizedMessage
from wechatpy.crypto import PrpCrypto
from wechatpy.utils import to_text
from wechatpy import parse_message, create_reply

from ..base import WeChatBase
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

    def component_notify(self):
        """
        receive component ticket and unauthorized message.
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kw):
                logging.debug('wechat component called.')
                data = xmltodict.parse(to_text(request.data))['xml']

                appid = str(data.get('AppId'))
                encrypt = str(data.get('Encrypt'))
                if not appid == self.component_appid:
                    return 'fail'

                decrypt = PrpCrypto(self.crypto.key).decrypt(encrypt, self.crypto._id)

                message = xmltodict.parse(to_text(decrypt))['xml']
                if message.get('InfoType') == ComponentVerifyTicketMessage.type:
                    logging.debug('receive wechat component ticket message.')
                    o = ComponentVerifyTicketMessage(message)
                    self.session.set(o.type, o.verify_ticket, 600)
                    logging.debug('update component ticket success: {}'.format(self.component_verify_ticket))

                elif message.get('InfoType') == ComponentUnauthorizedMessage.type:
                    pass

                res = func(*args, **kw)
                if res and res.lower() != 'success':
                    return 'fail'
                return 'success'

            return wrapper
        return decorator

    def component_authcall(self, callback_endpoint, **callback_endpoint_params):
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
                redirect_url = urllib.quote_plus(request.url_root[:-1] + redirect_url)
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
        def decorator(func, appid_key='app_id'):
            @functools.wraps(func)
            def wrapper(*args, **kw):

                mpappid = kw.get(appid_key) or request.args.get(appid_key)
                if not mpappid:
                    raise AttributeError('{} not fount in router or url params.'.format(appid_key))

                logging.debug('receive component mp notify: {}'.format(request.data))
                data = xmltodict.parse(to_text(request.data))['xml']
                signature = request.args.get('msg_signature')
                timestamp = request.args.get('timestamp')
                nonce = request.args.get('nonce')

                message = self.crypto.decrypt_message(data, signature, timestamp, nonce)
                message = parse_message(message)
                client = self.get_client_by_appid(mpappid)

                request.wechat_msg = {
                    'component_mp_content': message.content,
                    'component_client': client,
                    'component_mp_message': message,
                }
                return func(*args, **kw)

            return wrapper
        return decorator

    def component_user_login(self, redirect_endpoint, appid_key='appid',
            **redirect_endpoint_params):
        """
        decorator for request wechat user authorization info.

        request.wechat_msg.get('user')
        """
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kw):

                mpappid = kw.get(appid_key) or request.args.get(appid_key)
                if not mpappid:
                    raise AttributeError('{} not fount in router or url params.'.format(appid_key))

                redirect_uri = url_for(redirect_endpoint, appid=mpappid, **redirect_endpoint_params)
                redirect_uri = request.url_root[:-1] + redirect_uri
                oauth = ComponentOAuth(mpappid, self.component_appid, redirect_uri)
                if request.args.get('code'):
                    try:
                        openid = oauth.fetch_access_token(request.args.get('code')).get('openid')
                        request.wechat_msg = {'user': {'openid': openid}}
                        return func(*args, **kw)
                    except Exception:
                        pass

                return redirect(oauth.authorize_url)

            return wrapper
        return decorator

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
