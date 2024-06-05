import json
import os

import redis

UNPROCESSED_DOCUMENTS = 'unprocessed_documents'
PROCESSED_DOCUMENTS = 'processed_documents'
ENTRYPOINT = 'entrypoint'


class RedisClient:
    def __init__(self, host=None, port=None):
        self.host = host or os.getenv('QUEUE_REPOSITORY_HOST', 'localhost')
        self.port = port or int(os.getenv('QUEUE_REPOSITORY_PORT', 6379))
        self.client = redis.StrictRedis(host=self.host, port=self.port, decode_responses=True)

    def set(self, key, value):
        self.client.set(key, json.dumps(value))

    def append(self, key, value):
        data = self.get(key)
        data.append(value)
        self.set(key, data)

    def get(self, key):
        data = self.client.get(key)
        return json.loads(data) if data else list()

    def delete(self, key):
        self.client.delete(key)

    def clear(self):
        self.client.flushall()

    def close(self):
        self.client.close()
