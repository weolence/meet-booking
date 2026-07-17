class TokenError(Exception):
    """Base class for token parsing and validation errors."""


class InvalidAccessTokenError(TokenError):
    def __init__(self) -> None:
        super().__init__("Invalid access token.")