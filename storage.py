
from leancloud import Query, Object, LeanCloudError
from wechatpy.session import SessionStorage


class LeanCloudStorage(SessionStorage):

    class_name = 'WeChatStorage'

    def get(self, key, default=None):
        try:
            return Query(self.class_name).equal_to('key', key).first().get('value')
        except LeanCloudError:
            return None

    def set(self, key, value, ttl=None):
        try:
            obj = Query(self.class_name).equal_to('key', key).first()
        except LeanCloudError:
            obj = Object.extend(self.class_name)()
        obj.set('key', key)
        obj.set('value', value)
        obj.save()

    def delete(self, key):
        Query(self.class_name).equal_to('key', key).first().destroy()
