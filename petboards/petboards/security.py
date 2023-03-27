import os
import jwt
import falcon

from datetime import datetime, timedelta

_TOKEN_EXPIRATION_TIME = 24 * 60 * 60 # sec
_SECRET = os.getenv('PETBOARDS_SECRET')

class JWT:
    """
    Class, containing the set of static methods
    for JWT creation and validation.
    """

    @staticmethod
    def create(username: str, expiration: timedelta=timedelta(seconds=_TOKEN_EXPIRATION_TIME)) -> str:
        """
        Creates the JWT token with claim "username" set
        to `username` and "exp" set to `datetime.utcnow() + expiration`. Returns
        the token as a result.
        """

        if _SECRET is None:
            raise RuntimeError('jwt secret is not set (set the PETBOARDS_SECRET environment variable)')

        return jwt.encode(
            { 
                'username': username,
                'exp': datetime.utcnow() + expiration
            },
            _SECRET,
            algorithm='HS256'
        )
    
    @staticmethod
    def validate(token: str) -> str | None:
        """
        Validates the given `token` by checking the expiration
        time and returns `username` claim of the token if the token
        is valid, or `None` if the token is expired or invalid.
        """

        if _SECRET is None:
            raise RuntimeError('jwt secret is not set (set the PETBOARDS_SECRET environment variable)')

        try:
            decoded = jwt.decode(token, _SECRET, algorithms=['HS256'])
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

        return decoded['username']
    
def require_authorization(req, resp, resource, params):
    """
    Validation function, that may be used `falcon.before()`
    the responder in order to validate the JWT token.

    Raises `falcon.HTTPUnauthorized` if the token is absent or malformed.
    """

    try:
        body = req.media
        token = body['token']
    except:
        raise falcon.HTTPUnauthorized
    
    if JWT.validate(token) is None:
        raise falcon.HTTPUnauthorized