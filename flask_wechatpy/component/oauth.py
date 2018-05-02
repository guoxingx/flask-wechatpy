#!coding: utf-8

from __future__ import absolute_import, unicode_literals

import requests
from six.moves.urllib.parse import quote

from wechatpy.utils import json
from wechatpy.exceptions import WeChatOAuthException


class ComponentOAuth(object):
    """微信公众平台 OAuth 网页授权 """

    API_BASE_URL = 'https://api.weixin.qq.com/'
    OAUTH_BASE_URL = 'https://open.weixin.qq.com/connect/'

    def __init__(self, app_id, component_appid, component_access_token, redirect_uri,
                 scope='snsapi_base', state=''):
        """

        :param app_id: 微信公众号 app_id
        :param redirect_uri: OAuth2 redirect URI
        :param scope: 可选，微信公众号 OAuth2 scope，默认为 ``snsapi_base``
        :param state: 可选，微信公众号 OAuth2 state
        """
        self.app_id = app_id
        self.component_appid = component_appid
        self.component_access_token = component_access_token
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.state = state
        self._http = requests.Session()

    def _request(self, method, url_or_endpoint, **kwargs):
        if not url_or_endpoint.startswith(('http://', 'https://')):
            url = '{base}{endpoint}'.format(
                base=self.API_BASE_URL,
                endpoint=url_or_endpoint
            )
        else:
            url = url_or_endpoint

        if isinstance(kwargs.get('data', ''), dict):
            body = json.dumps(kwargs['data'], ensure_ascii=False)
            body = body.encode('utf-8')
            kwargs['data'] = body

        res = self._http.request(
            method=method,
            url=url,
            **kwargs
        )
        try:
            res.raise_for_status()
        except requests.RequestException as reqe:
            raise WeChatOAuthException(
                errcode=None,
                errmsg=None,
                client=self,
                request=reqe.request,
                response=reqe.response
            )
        result = json.loads(res.content.decode('utf-8', 'ignore'), strict=False)

        if 'errcode' in result and result['errcode'] != 0:
            errcode = result['errcode']
            errmsg = result['errmsg']
            raise WeChatOAuthException(
                errcode,
                errmsg,
                client=self,
                request=res.request,
                response=res
            )

        return result

    def _get(self, url, **kwargs):
        return self._request(
            method='get',
            url_or_endpoint=url,
            **kwargs
        )

    @property
    def authorize_url(self):
        """获取授权跳转地址

        :return: URL 地址
        """
        redirect_uri = quote(self.redirect_uri, safe='')
        url_list = [
            self.OAUTH_BASE_URL,
            'oauth2/authorize?appid=',
            self.app_id,
            '&redirect_uri=',
            redirect_uri,
            '&response_type=code&scope=',
            self.scope
        ]
        if self.state:
            url_list.extend(['&state=', self.state])
        url_list.extend(['&component_appid=', self.component_appid])
        url_list.append('#wechat_redirect')
        return ''.join(url_list)

    # def fetch_access_token(self, code):
    def get_openid(self, code):
        """获取 access_token

        :param code: 授权完成跳转回来后 URL 中的 code 参数
        :return: JSON 数据包
        """
        res = self._get(
            'sns/oauth2/component/access_token',
            params={
                'appid': self.app_id,
                'code': code,
                'component_appid': self.component_appid,
                'component_access_token': self.component_access_token,
                'grant_type': 'authorization_code'
            }
        )
        self.access_token = res['access_token']
        self.open_id = res['openid']
        self.refresh_token = res['refresh_token']
        self.expires_in = res['expires_in']
        return res

    def refresh_access_token(self, refresh_token):
        """刷新 access token

        :param refresh_token: OAuth2 refresh token
        :return: JSON 数据包
        """
        res = self._get(
            'sns/oauth2/component/refresh_token',
            params={
                'appid': self.app_id,
                'grant_type': 'refresh_token',
                'component_appid': self.component_appid,
                'component_access_token': self.component_access_token,
                'refresh_token': refresh_token
            }
        )
        self.access_token = res['access_token']
        self.open_id = res['openid']
        self.refresh_token = res['refresh_token']
        self.expires_in = res['expires_in']
        return res

    def get_user_info(self, openid=None, access_token=None, lang='zh_CN'):
        """获取用户信息

        :param openid: 可选，微信 openid，默认获取当前授权用户信息
        :param access_token: 可选，access_token，默认使用当前授权用户的 access_token
        :param lang: 可选，语言偏好, 默认为 ``zh_CN``
        :return: JSON 数据包
        """
        openid = openid or self.open_id
        access_token = access_token or self.access_token
        return self._get(
            'sns/userinfo',
            params={
                'access_token': access_token,
                'openid': openid,
                'lang': lang
            }
        )
