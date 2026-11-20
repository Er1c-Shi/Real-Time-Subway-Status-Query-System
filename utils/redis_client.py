import redis
import sys
import os

# Add project root directory to Python path to import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from config import Config

class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host=Config.REDIS_HOST,
            port=Config.REDIS_PORT,
            db=Config.REDIS_DB,
            decode_responses=True
        )

    def add_to_stream(self, stream_name, data):
        try:
            self.client.xadd(stream_name, data)
        except Exception as e:
            print(f"Error adding to Redis stream: {e}")

    def read_from_stream(self, stream_name, group_name, consumer_name, block=0, count=100):
        try:
            return self.client.xreadgroup(
                group_name,
                consumer_name,
                {stream_name: ">"},
                count=count,
                block=block
            )
        except Exception as e:
            print(f"Error reading from Redis stream: {e}")
            return None

    def create_consumer_group(self, stream_name, group_name):
        try:
            self.client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                print(f"Consumer group \'{group_name}\' already exists.")
            else:
                raise e

redis_client = RedisClient()