import falcon

import sqlalchemy as sa
from sqlalchemy.orm import Session

import uuid

from .security import require_authorization, JWT
from .models import Message, Board
from .user import UserStore

def validate_message_pagination_params(req, resp, resource, params):
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

class MessageStore():

    def __init__(self, db_session: Session):
        self._db = db_session

    def save(self, message: Message):
        """
        Updates/Adds a `message` into the database.
        """

        self._db.add(message)
        self._db.commit()

    def delete(self, message: Message):
        """
        Deletes a `message` from the database.
        """

        self._db.delete(message)
        self._db.commit()

class MessageResource():

    def __init__(self, message_store: MessageStore, board_store: 'BoardStore', user_store: UserStore):
        self._board_store = board_store
        self._user_store = user_store
        self._message_store = message_store
    
    @falcon.before(require_authorization)
    @falcon.before(validate_message_pagination_params)
    def on_get(self, req: falcon.Request, resp: falcon.Response, board_id: uuid.UUID):
        """
        Fetches all messages from the board with the ID `board_id`
        (paginated query).
        """

        board = self._board_store.get(board_id)
        if board is None:
            raise falcon.HTTPNotFound
        
        page = int(req.params['page'])
        elements = int(req.params['elements'])

        if page * elements >= len(board.messages):
            res = []
        elif page * elements + elements > len(board.messages):
            res = board.messages[page * elements:len(board.messages)]
        else:
            res = board.messages[page * elements:page * elements + elements]
        
        resp.media = [msg.serialize() for msg in res]
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

    @falcon.before(require_authorization)
    def on_get_one(self, req: falcon.Request, resp: falcon.Response, board_id: uuid.UUID, message_id: uuid.UUID):
        """
        Fetches the message by its `board_id` and `message_id`.
        """

        board = self._board_store.get(board_id)
        if board is None:
            raise falcon.HTTPNotFound
        
        message = None
        for msg in board.messages:
            if msg.message_id == message_id:
                message = msg

        if message is None:
            raise falcon.HTTPNotFound
        
        resp.media = message.serialize()
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

    @falcon.before(require_authorization)
    def on_post(self, req: falcon.Request, resp: falcon.Response, board_id: uuid.UUID):
        """
        Create a new `Message` instance, save it to the
        database and return its URI in the `location` header.
        """

        board = self._board_store.get(board_id)
        if board is None:
            raise falcon.HTTPNotFound
        
        body = req.media
        if 'text' not in body:
            raise falcon.HTTPBadRequest(title='text', description='The message cannot be empty')

        author_username = JWT.validate(body['token'])
        author = self._user_store.get_by_username(author_username)
        
        message = Message(body['text'], author, board)
        self._message_store.save(message)

        board.messages.append(message)

        resp.status = falcon.HTTP_201
        resp.media = {}
        resp.location = f'/boards/{board_id}/messages/{message.message_id}'

    @falcon.before(require_authorization)
    def on_patch_one(self, req: falcon.Request, resp: falcon.Response, board_id: uuid.UUID, message_id: uuid.UUID):
        """
        Edits the message with the ID `message_id` on board
        with the ID `board_id`, returning updated message
        in the response body.
        The client must be the one, who wrote the message.
        """

        board = self._board_store.get(board_id)
        if board is None:
            raise falcon.HTTPNotFound
        
        message = None
        for msg in board.messages:
            if msg.message_id == message_id:
                message = msg

        if message is None:
            raise falcon.HTTPNotFound

        body = req.media

        author_username = JWT.validate(body['token'])
        author = self._user_store.get_by_username(author_username)
        if message.author_id != author.user_id:
            raise falcon.HTTPUnauthorized

        if body is None or 'text' not in body:
            raise falcon.HTTPBadRequest
        
        message.text = body['text']
        self._message_store.save(message)
        
        resp.media = message.serialize()
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON

    @falcon.before(require_authorization)
    def on_delete_one(self, req: falcon.Request, resp: falcon.Response, board_id: uuid.UUID, message_id: uuid.UUID):
        """
        Deletes the message with the ID `message_id` on board
        with the ID `board_id`, returning updated message
        in the response body.
        The client must be the one, who wrote the message.
        """

        board = self._board_store.get(board_id)
        if board is None:
            raise falcon.HTTPNotFound
        
        message = None
        for msg in board.messages:
            if msg.message_id == message_id:
                message = msg

        if message is None:
            raise falcon.HTTPNotFound
        
        author_username = JWT.validate(req.media['token'])
        author = self._user_store.get_by_username(author_username)
        if message.author_id != author.user_id:
            raise falcon.HTTPUnauthorized
        
        board.messages.remove(message)
        self._message_store.delete(message)
        
        resp.media = {}
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        

def validate_board_pagination_params(req, resp, resource, params):
    _PAGINATION_MAX_ELEMENTS = 30
    
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


class BoardStore():

    def __init__(self, db_session: Session):
        self._db = db_session

    def get_all(self, page: int, elements: int) -> list[Board]:
        """
        Fetches `elements` number of records about the
        boards starting at page `page` sorted by their
        `created_at` property.
        """
        
        board = self._db.query(Board).order_by(Board.created_at).offset(page * elements).limit(elements).all()
        
        return board

    def get(self, board_id: uuid.UUID) -> Board | None:
        """
        Fetches a single record about the board with UUID `board_id`.
        """

        board = self._db.get(Board, board_id)

        return board

    def save(self, board: Board) -> None:
        """
        Adds/Saves the `board` object into the database.
        """

        self._db.add(board)
        self._db.commit()

class BoardResource():

    def __init__(self, board_store: BoardStore, user_store: UserStore):
        self._board_store = board_store
        self._user_store = user_store

    @falcon.before(require_authorization)
    def on_get_one(self, req: falcon.Request, resp: falcon.Response, board_id: uuid.UUID):
        """
        Fetches one record about the boards with the specified `uuid`.
        """

        board = self._board_store.get(board_id)
        if board is None:
            raise falcon.HTTPNotFound

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        resp.media = board.serialize()

    @falcon.before(require_authorization)
    @falcon.before(validate_board_pagination_params)
    def on_get(self, req: falcon.Request, resp: falcon.Response):
        """
        Fetches `elements` number of records about the
        boards starting at page `page` sorted by their
        `created_at` property.
        """

        page = int(req.params['page'])
        elements = int(req.params['elements'])

        boards = self._board_store.get_all(page, elements)

        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        resp.media = [b.serialize() for b in boards]

    @falcon.before(require_authorization)
    def on_post(self, req: falcon.Request, resp: falcon.Response):
        """
        Creates a new board and returns location to it
        in the `location` header.
        """

        body = req.media

        if body is None:
            raise falcon.HTTPBadRequest

        if 'topic' not in body or len(body['topic']) == 0:
            raise falcon.HTTPBadRequest('topic', 'The board\'s topic must be specified')

        topic: str = body['topic']
        username: str = JWT.validate(body['token'])
        
        user = self._user_store.get_by_username(username)
        board = Board(topic, user)
        
        self._board_store.save(board)

        resp.status = falcon.HTTP_201
        resp.content_type = falcon.MEDIA_JSON
        resp.location = f'/boards/{board.board_id}'
        resp.media = {}