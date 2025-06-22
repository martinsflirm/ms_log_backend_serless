class SimpleCache:
    def __init__(self):
        self.cache = {}

    def get(self, key):
        if key in self.cache:
            value, expiry_time = self.cache[key]
            if expiry_time is None or time.time() < expiry_time:
                return value
            else:
                del self.cache[key]
        return None

    def set(self, key, value, expiry_seconds=None):
        expiry_time = None
        if expiry_seconds is not None:
            expiry_time = time.time() + expiry_seconds
        self.cache[key] = (value, expiry_time)

    def delete(self, key):
        if key in self.cache:
            del self.cache[key]


Local_Cache = SimpleCache()
