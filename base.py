
from .utils import config_with_app


class WeChatBase(object):

    def __init__(self, app=None):
        self.app = app

        if app:
            self._wechat = self.init_app(app)
        else:
            self._wechat = None

    def init_app(self, app):
        _wechat = self.init_with_config(config_with_app(app))
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['wechatpy'] = self
        self._wechat = _wechat
        return _wechat

    def init_with_config(self, config):
        session_interface = self._init_session(config)

        if config['WECHAT_TYPE'] == 17:
            from wechatpy.component import WeChatComponent
            self._is_component = True
            return WeChatComponent(
                config['WECHAT_APPID'],
                config['WECHAT_SECRET'],
                config['WECHAT_TOKEN'],
                config['WECHAT_AES_KEY'],
                session=session_interface,
            )

        if config['WECHAT_TYPE'] == 0:
            from wechatpy import WeChatClient
        else:
            from wechatpy.enterprise import WeChatClient

        return WeChatClient(
            config['WECHAT_APPID'],
            config['WECHAT_SECRET'],
            session=session_interface,
            timeout=config['WECHAT_TIMEOUT'],
            auto_retry=config['WECHAT_AUTO_RETRY'],
        )

    def _init_session(self, config):
        if config['WECHAT_SESSION_TYPE'] == 'redis':
            from wechatpy.session.redisstorage import RedisStorage
            from redis import Redis

            if config.get('WECHAT_SESSION_REDIS_URL'):
                redis = Redis.from_url(config['WECHAT_SESSION_REDIS_URL'])
            else:
                redis = Redis(
                    host=config.get('WECHAT_SESSION_REDIS_HOST', 'localhost'),
                    port=config.get('WECHAT_SESSION_REDIS_PORT', 6379),
                    db=config.get('WECHAT_SESSION_REDIS_DB', 0),
                    password=config.get('WECHAT_SESSION_REDIS_PASS', None)
                )
            prefix = config['WECHAT_SESSION_PREFIX']
            self._redis_prefix = prefix
            self._redis = redis
            session_interface = RedisStorage(redis, prefix=prefix)

        elif config['WECHAT_SESSION_TYPE'] == 'memcached':
            from wechatpy.session.memcachedstorage import MemcachedStorage
            mc = self._get_mc_client(config['WECHAT_SESSION_MEMCACHED'])
            session_interface = MemcachedStorage(mc, prefix=config['WECHAT_SESSION_PREFIX'])

        elif config['WECHAT_SESSION_TYPE'] == 'leancloud':
            from .storage import LeanCloudStorage
            session_interface = LeanCloudStorage()

        else:
            from wechatpy.session.memorystorage import MemoryStorage
            session_interface = MemoryStorage()
        return session_interface

    def __getattr__(self, name):
        return getattr(self._wechat, name)
