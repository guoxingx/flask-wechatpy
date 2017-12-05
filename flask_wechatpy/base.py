
from .utils import config_with_app


class WeChatBase(object):

    def __init__(self, app=None, config=None):

        self._wechat = None

        if app:
            config = config_with_app(app)

        if not config:
            raise AttributeError()

        self.init_with_config(config)
        self.bind_app(app)

    def adjust_aes_key(self, aes_key):
        lens = len(aes_key)
        lenx = lens - (lens % 4 if lens % 4 else 4)
        try:
            import base64
            return base64.decodestring(aes_key[:lenx])
        except:
            return aes_key

    def init_with_config(self, config):
        if not isinstance(config, dict):
            raise AttributeError()

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
            session_interface = RedisStorage(redis, prefix=config['WECHAT_SESSION_PREFIX'])

        elif config['WECHAT_SESSION_TYPE'] == 'memcached':
            from wechatpy.session.memcachedstorage import MemcachedStorage
            mc = self._get_mc_client(config['WECHAT_SESSION_MEMCACHED'])
            session_interface = MemcachedStorage(mc, prefix=config['WECHAT_SESSION_PREFIX'])

        elif config['WECHAT_SESSION_TYPE'] == 'leancloud':
            from .leancloudstorage import LeanCloudStorage
            session_interface = LeanCloudStorage()

        else:
            from wechatpy.session.memorystorage import MemoryStorage
            session_interface = MemoryStorage()

        if config['WECHAT_TYPE'] == 17:
            from wechatpy.component import WeChatComponent
            self._wechat = WeChatComponent(
                config['WECHAT_APPID'],
                config['WECHAT_SECRET'],
                config['WECHAT_TOKEN'],
                config['WECHAT_AES_KEY'],
                session=session_interface,
            )
            return

        if config['WECHAT_TYPE'] == 0:
            from wechatpy import WeChatClient
        else:
            from wechatpy.enterprise import WeChatClient

        self._wechat = WeChatClient(
            config['WECHAT_APPID'],
            config['WECHAT_SECRET'],
            session=session_interface,
            timeout=config['WECHAT_TIMEOUT'],
            auto_retry=config['WECHAT_AUTO_RETRY'],
        )

    def bind_app(self, app):
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['wechatpy'] = self

    def __getattr__(self, name):
        return getattr(self._wechat, name)
