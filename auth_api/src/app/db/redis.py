import backoff

import redis


class Redis(object):
    def __init__(self, app=None, config_prefix='REDIS', **kwargs):
        self._client = None
        self.provider_class = redis.Redis
        self.provider_kwargs = kwargs
        self.config_prefix = config_prefix

        if app is not None:
            self.init_app(app)

    def init_app(self, app, **kwargs):
        redis_url = app.config.get(
            '{0}_URL'.format(self.config_prefix), 'redis://localhost:6379/0'
        )

        self.provider_kwargs.update(kwargs)
        self._client = self.provider_class.from_url(
            redis_url, **self.provider_kwargs
        )

        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions[self.config_prefix.lower()] = self

    @backoff.on_exception(backoff.expo,
                          redis.exceptions.RedisError,
                          max_tries=10)
    def ping(self):
        return self._client.ping()

    def __getattr__(self, name):
        self.ping()
        return getattr(self._client, name)

    def __getitem__(self, name):
        return self._client[name]

    def __setitem__(self, name, value):
        self._client[name] = value

    def __delitem__(self, name):
        del self._client[name]
