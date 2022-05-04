import enum
import orjson

from flask import url_for, redirect, current_app, request
from rauth import OAuth2Service


class OAuthProvider(enum.Enum):
    yandex = enum.auto()


class OAuthSignIn:
    providers = None

    def __init__(self, provider_name):
        self.provider_name = provider_name
        credentials = current_app.config['OAUTH_CREDENTIALS'][provider_name]
        self.id = credentials['id']
        self.secret = credentials['secret']
        self.authorize_url = credentials['authorize_url']
        self.access_token_url = credentials['access_token_url']
        self.base_url = credentials['base_url']
        self.scope = credentials['scope']

    def authorize(self):
        pass

    def callback(self):
        pass

    def get_callback_url(self):
        return url_for('.callback', provider=self.provider_name,
                       _external=True)

    @classmethod
    def get_provider(cls, provider_name):
        if cls.providers is None:
            cls.providers = {}
            for provider_class in cls.__subclasses__():
                provider = provider_class()
                cls.providers[provider.provider_name] = provider
        return cls.providers[provider_name]


class YandexSignIn(OAuthSignIn):
    def __init__(self):
        super().__init__(OAuthProvider.yandex.name)
        self.service = OAuth2Service(
            name=OAuthProvider.yandex.name,
            client_id=self.id,
            client_secret=self.secret,
            authorize_url=self.authorize_url,
            access_token_url=self.access_token_url,
            base_url=self.base_url
        )

    def authorize(self):
        return redirect(self.service.get_authorize_url(
            scope=self.scope,
            response_type='code',
            redirect_uri=self.get_callback_url())
        )

    def callback(self):
        def decode_json(payload):
            return orjson.loads(payload.decode('utf-8'))

        if 'code' not in request.args:
            return None

        oauth_session = self.service.get_auth_session(
            data={'code': request.args['code'],
                  'grant_type': 'authorization_code',
                  'redirect_uri': self.get_callback_url()},
            decoder=decode_json
        )

        user_info = oauth_session.get('info').json()
        _id = f'{OAuthProvider.yandex.name}$' + user_info.get('id')
        first_name = user_info.get('first_name')
        last_name = user_info.get('last_name')
        email = user_info.get('default_email').lower()

        return _id, email, first_name, last_name
