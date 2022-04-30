from flask import Blueprint

from .views import (AccountAPI, ChangeEmailAPI, ChangePasswordAPI, JournalAPI,
                    RegisterAPI, SessionsAPI, TOTPDeviceAPI)

router = Blueprint('account', __name__, url_prefix='/account')

router.add_url_rule('/register/',
                    view_func=RegisterAPI.as_view('register'),
                    methods=['POST'])
router.add_url_rule('/',
                    view_func=AccountAPI.as_view('me'),
                    methods=['GET', 'PATCH'])

router.add_url_rule('/change-email/',
                    view_func=ChangeEmailAPI.as_view('change_email'),
                    methods=['POST'])
router.add_url_rule('/change-password/',
                    view_func=ChangePasswordAPI.as_view('change_password'),
                    methods=['POST'])

router.add_url_rule('/journal/',
                    view_func=JournalAPI.as_view('journal'),
                    methods=['GET'])

router.add_url_rule('/sessions/',
                    defaults={'session_id': None},
                    view_func=SessionsAPI.as_view('sessions'),
                    endpoint='without_id',
                    methods=['GET', 'DELETE'])
router.add_url_rule('/sessions/<session_id>',
                    view_func=SessionsAPI.as_view('sessions'),
                    endpoint='with_id',
                    methods=['GET', 'DELETE'])

router.add_url_rule('/otp/',
                    view_func=TOTPDeviceAPI.as_view('otp'),
                    methods=['GET', 'POST', 'DELETE'])
