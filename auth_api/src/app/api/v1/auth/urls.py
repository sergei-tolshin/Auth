from flask import Blueprint

from .views import LoginAPI, LogoutAPI, TokenRefreshAPI, TokenVerifyAPI

router = Blueprint('auth', __name__, url_prefix='/auth')

router.add_url_rule('/login/',
                    view_func=LoginAPI.as_view('login'))
router.add_url_rule('/logout/',
                    view_func=LogoutAPI.as_view('logout'))
router.add_url_rule('/token/refresh/',
                    view_func=TokenRefreshAPI.as_view('token_refresh'))
router.add_url_rule('/token/verify/',
                    view_func=TokenVerifyAPI.as_view('token_verify'))
