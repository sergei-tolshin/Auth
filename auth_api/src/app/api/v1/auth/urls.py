from flask import Blueprint

from .views import (CheckAPI, LoginAPI, LogoutAPI, TokenRefreshAPI,
                    TokenVerifyAPI, OauthAPI, OauthCallbackAPI)

router = Blueprint('auth', __name__, url_prefix='/auth')

router.add_url_rule('/login/',
                    view_func=LoginAPI.as_view('login'))
router.add_url_rule('/logout/',
                    view_func=LogoutAPI.as_view('logout'))
router.add_url_rule('/token/refresh/',
                    view_func=TokenRefreshAPI.as_view('token_refresh'))
router.add_url_rule('/token/verify/',
                    view_func=TokenVerifyAPI.as_view('token_verify'))
router.add_url_rule('/check/<uuid:user_id>',
                    view_func=CheckAPI.as_view('check'))
router.add_url_rule('/oauth/<provider>/',
                    view_func=OauthAPI.as_view('oauth'))
router.add_url_rule('/oauth/callback/<provider>/',
                    view_func=OauthCallbackAPI.as_view('callback'))
