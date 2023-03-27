import falcon
import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Session

from .security import require_authorization
from .models import User

class UserStore:
    """
    Data access layer for `User` objects.
    """

    def __init__(self, db_session: Session):
        self._db = db_session

    def get_by_username(self, username: str) -> User | None:
        """
        Fetches the user by their `username` from the database.
        If the user doesn't exist, `None` is returned.
        """

        user = self._db.query(User).filter_by(username=username).first()

        return user

    def get(self, user_id: uuid.UUID) -> User | None:
        """
        Fetches the user by their `user_id` from the database.
        If the user doesn't exist, `None` is returned.
        """

        user = self._db.get(User, user_id)
        
        return user
    
    def get_all(self, page: int, elements: int) -> list[User]:
        """
        Fetches and returns records about `elements` users
        starting from page `page` in the table.
        """

        users = self._db.query(User).order_by(User.username).offset(page * elements).limit(elements).all()

        return users

    def save(self, user: User):
        """
        Saves the instance of `User` class into
        the database.
        """

        self._db.add(user)
        self._db.commit()

def validate_pagination_params(req, resp, resource, params):
    _PAGINATION_MAX_ELEMENTS = 50
    
    if 'page' not in req.params or 'elements' not in req.params:
        raise falcon.HTTPBadRequest
    
    page = int(req.params['page'])
    elements = int(req.params['elements'])

    if page < 0:
        raise falcon.HTTPBadRequest('page', 'The page index cannot be negative')

    if elements < 0:
        raise falcon.HTTPBadRequest('elements', 'The number of elements per page cannot be negative')
    if elements > _PAGINATION_MAX_ELEMENTS:
        raise falcon.HTTPBadRequest('elements', f'The maximum number of elements per page is {_PAGINATION_MAX_ELEMENTS}')

class UserResource:
    
    def __init__(self, user_store: UserStore):
        self._user_store = user_store

    @falcon.before(require_authorization)
    @falcon.before(validate_pagination_params)
    def on_get(self, req: falcon.Request, resp: falcon.Response):
        """
        Get all users (paginated query).
        """

        page = int(req.params['page'])
        elements = int(req.params['elements'])

        resp.content_type = falcon.MEDIA_JSON
        resp.media = [u.serialize() for u in self._user_store.get_all(page, elements)]
        resp.status = falcon.HTTP_200

    @falcon.before(require_authorization)
    def on_get_one(self, req: falcon.Request, resp: falcon.Response, user_id: uuid.UUID):
        """
        Get the user by their `user_id`.
        """
        
        user = self._user_store.get(user_id)
        if user is None:
            raise falcon.HTTPNotFound

        resp.content_type = falcon.MEDIA_JSON
        resp.media = user.serialize()
        resp.status = falcon.HTTP_200
    