class DB:
    def put(self,key,value):
        print "PUT: " +key+" "+ value
        pass
    def get(self,key):
        pass

class RedisDB(DB):
    def __init__(self, redis):
        self.redis=redis
    def put(self,key,value):
        self.redis.put(key,value)
    def get(self,key):
        return self.redis.get(key)
