import re
import time
from typing import Optional

import flask
import orjson
from werkzeug.exceptions import TooManyRequests

LIMIT_EXPR = re.compile(
    r"""
    \s*([0-9]+)
    \s*(/)
    *\s*(hour|minute|second|day|month|year)?\s*""",
    re.IGNORECASE | re.VERBOSE,
)

TIME_UNITS = dict(
    day=60 * 60 * 24,
    month=60 * 60 * 24 * 30,
    year=60 * 60 * 24 * 30 * 12,
    hour=60 * 60,
    minute=60,
    second=1,
)


class TokenBucket:
    def __init__(self, tokens, refill_period, capacity=None, last_check=None):
        self.tokens: int = tokens
        self.capacity: int = capacity if capacity is not None else tokens
        self.refill_period = refill_period
        self.last_check = last_check or time.monotonic()

    def token_count(self):
        current_time = time.monotonic()
        time_passed = current_time - self.last_check
        token_delta = int(time_passed//self.refill_period)

        if(token_delta + int(self.capacity) >= int(self.tokens)):
            self.capacity = self.tokens
            self.last_check = current_time
        else:
            self.capacity += token_delta
            self.last_check = self.last_check + \
                token_delta * float(self.refill_period)

        try_again_seconds = self.refill_period - \
            (current_time - self.last_check)

        return self.capacity, try_again_seconds

    def consume(self, num_tokens: int):
        self.capacity = int(self.capacity) - num_tokens


class RateLimiter(object):
    def __init__(self, app: Optional[flask.Flask] = None, limit: str = None):
        self.app = app
        self.limit: str = limit
        self.tokens: int = None
        self.refill_period: int = None
        self.storage = None

    def init_app(self, app: flask.Flask):
        self.app = app
        config = app.config
        self.limit = self.limit or config.get('RATELIMIT_DEFAULT', None)
        self.storage = app.extensions['redis']

        if self.limit is not None:
            self._parse_limit(self.limit)
        else:
            raise ValueError('Limit can not be None')

        if not hasattr(app, 'extensions'):
            app.extensions = {}

        app.before_request(self._check_request_token)

        app.extensions['rate_limiter'] = self

    def _check_request_token(self):
        remote_addr = flask.request.remote_addr
        endpoint = flask.request.endpoint or ''
        method = flask.request.method

        try:
            self._get_token(remote_addr, endpoint, method)
        except Exception as error:
            raise error

    def _get_token(self, remote_addr, endpoint, method):
        limit_key = self._build_limit_key(remote_addr, endpoint, method)
        current_bucket = self.storage.get(limit_key)

        if current_bucket:
            data = orjson.loads(current_bucket)
            token_bucket = TokenBucket(**data)
        else:
            token_bucket = TokenBucket(self.tokens, self.refill_period)

        remaining_token, try_again_seconds = token_bucket.token_count()

        if int(remaining_token) < 1:
            raise TooManyRequests(
                f'Rate limit exceeded, '
                f'try again in {try_again_seconds:.3f} seconds')

        token_bucket.consume(1)
        self.storage.set(limit_key, orjson.dumps(token_bucket.__dict__))

    def _build_limit_key(self, remote_addr, endpoint, method):
        return ':'.join((
            str(remote_addr),
            str(endpoint),
            str(method),
            str(self.limit)
        ))

    def _parse_limit(self, limit):
        match = LIMIT_EXPR.match(limit)
        amount, _, time_unit = match.groups()
        self.tokens = amount
        self.refill_period = TIME_UNITS[time_unit] / int(amount)
