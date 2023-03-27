import falcon
import bcrypt

import re
from datetime import datetime

from .user import UserStore, User
from .security import JWT

def check_username(username: str) -> bool:
    if username is None:
        return False

    expr = re.compile(r'^[a-zA-Z0-9_]{1,128}$')
    if expr.fullmatch(username):
        return True
    
    return False

def check_password(password: str) -> bool:
    if password is None:
        return False

    return True

def check_first_name(first_name: str) -> bool:
    if first_name is None:
        return False

    expr = re.compile(r'^[a-zA-Zа-яА-Я]{,128}$')
    if expr.fullmatch(first_name):
        return True
    
    return False

def check_last_name(last_name: str) -> bool:
    if last_name is None:
        return False

    expr = re.compile(r'^[a-zA-Zа-яА-Я]{,128}$')
    if expr.fullmatch(last_name):
        return True
    
    return False

def validate_login_request(req, resp, resource, params):
    body = req.media
    if body is None or 'username' not in body or 'password' not in body or \
        not check_username(body['username']) or not check_password(body['password']):
        raise falcon.HTTPBadRequest

def validate_registration_request(req, resp, resource, params):
    body = req.media
    if body is None or 'username' not in body or 'password' not in body or \
        'first_name' not in body or 'last_name' not in body or \
        not check_username(body['username']) or not check_password(body['password']) or \
        not check_first_name(body['first_name']) or not check_last_name(body['last_name']):
        raise falcon.HTTPBadRequest

class AuthResource:

    def __init__(self, user_store: UserStore):
        """Creates a new `Auth` class instance."""

        self._user_store: UserStore = user_store
    
    @falcon.before(validate_login_request)
    def on_post_login(self, req: falcon.Request, resp: falcon.Response):
        """
        Checks the credentials provided, authorizes the user,
        and responds with a freshly created JWT token.
        """

        body = req.media
        username = body['username']
        password = body['password'].encode('utf-8')

        user = self._user_store.get_by_username(username)
        if user is None:
            raise falcon.HTTPNotFound(title='error', description='Invalid login or password')

        # Security precaution: don't tell whether it's wrong
        # username or password.
        if not bcrypt.checkpw(password, user._password):
            raise falcon.HTTPNotFound(title='error', description='Invalid login or password')
        
        user.last_login = datetime.utcnow()
        self._user_store.save(user)
        
        token = JWT.create(user.username)

        resp.location = f'/users/{user.user_id}'
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        resp.media = {
            'token': token
        }

    @falcon.before(validate_registration_request)
    def on_post_register(self, req: falcon.Request, resp: falcon.Response):
        """
        Registers a new user with the information provided
        in the request body. User is not logged in automatically
        after that.
        """
        
        body = req.media
        username = body['username']
        password = body['password']
        first_name = body['first_name']
        last_name = body['last_name']

        existing_user = self._user_store.get_by_username(username)

        if existing_user is not None:
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
            resp.media = {
                'error': 'The username is already taken'
            }
            return
        
        new_user = User(username, password, first_name, last_name)
        self._user_store.save(new_user)

        resp.status = falcon.HTTP_201
        resp.content_type = falcon.MEDIA_JSON
        resp.media = {}
