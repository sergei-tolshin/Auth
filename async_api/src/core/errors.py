class AuthenticationHeaderMissing(Exception):
    pass


class TokenHasExpired(Exception):
    pass


class UserNotFound(Exception):
    pass


class UserNotActive(Exception):
    pass


class AuthConnectorError(Exception):
    pass
