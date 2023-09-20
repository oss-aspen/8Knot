import os

redis_host = "{}".format(os.getenv("REDIS_SERVICE_HOST", "redis-cache"))
redis_port = "{}".format(os.getenv("REDIS_SERVICE_PORT", "6379"))
redis_password = "{}@".format(os.getenv("REDIS_PASSWORD", ""))

REDIS_URL = f"redis://:{redis_password}{redis_host}:{redis_port}"

print(REDIS_URL)
