
from leancloud import Query, Object, LeanCloudError


class LeanCloudStorage(object):

    class_name = 'WeChatStorage'

    def __init__(self):
        pass

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

    def __getitem__(self, key):
        self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        self.delete(key)
