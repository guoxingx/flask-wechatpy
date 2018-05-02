
import random
import string

from flask import current_app, request


def config_with_app(app):
    config = app.config
    config.setdefault('WECHAT_APPID', None)
    config.setdefault('WECHAT_SECRET', None)
    config.setdefault('WECHAT_TYPE', 0)
    config.setdefault('WECHAT_SESSION_TYPE', None)
    config.setdefault('WECHAT_SESSION_PREFIX', 'flask-wechatpy')
    config.setdefault('WECHAT_AUTO_RETRY', True)
    config.setdefault('WECHAT_TIMEOUT', None)
    config.setdefault('WECHAT_USE_MP_NICKNAME', True)
    config.setdefault('WECHAT_COMPONENT_TEST_APPID', 'a-test-appid')
    config.setdefault('WECHAT_COMPONENT_TEST_NICKNAME', 'test')
    config.setdefault('WECHAT_COMPONENT_TEST_OPENID', 'test_openid')
    return app.config


def config_value(key, default=None):
    return current_app.config.get(key, default)


def get_random_openid():
    return ''.join([random.choice(string.ascii_letters + '0123456789') for i in range(32)])


def load_mp_appid(appid_key, kw):
    mpappid = kw.get(appid_key) or request.args.get(appid_key)
    return mpappid
