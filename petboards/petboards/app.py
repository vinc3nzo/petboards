import falcon

from .user import UserStore, UserResource
from .auth import AuthResource
from .board import MessageStore, BoardStore, BoardResource, MessageResource

def create_app(user_store: UserStore, message_store: MessageStore, board_store: BoardStore) -> falcon.App:
    users = UserResource(user_store)
    messages = MessageResource(message_store, board_store, user_store)
    boards = BoardResource(board_store, user_store)
    auth = AuthResource(user_store)

    app = falcon.App()
    app.add_route('/auth/login', auth, suffix='login')
    app.add_route('/auth/register', auth, suffix='register')

    app.add_route('/users', users)
    app.add_route('/users/{user_id:uuid}', users, suffix='one')

    app.add_route('/boards', boards)
    app.add_route('/boards/{board_id:uuid}', boards, suffix='one')

    app.add_route('/boards/{board_id:uuid}/messages', messages)
    app.add_route('/boards/{board_id:uuid}/messages/{message_id:uuid}', messages, suffix='one')

    return app