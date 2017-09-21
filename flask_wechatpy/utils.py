
def config_with_app(app):
    config = app.config
    config.setdefault('WECHAT_APPID', None)
    config.setdefault('WECHAT_SECRET', None)
    config.setdefault('WECHAT_TYPE', 0)
    config.setdefault('WECHAT_SESSION_TYPE', None)
    config.setdefault('WECHAT_SESSION_PREFIX', 'flask-wechatpy')
    config.setdefault('WECHAT_AUTO_RETRY', True)
    config.setdefault('WECHAT_TIMEOUT', None)
    return app.config
