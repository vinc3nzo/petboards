import falcon
from falcon import testing

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker, Session

from petboards.user import UserStore
from petboards.models import User, Board, Message
from petboards.app import create_app
from petboards.security import JWT
from petboards.persistency import Base
from petboards.board import MessageStore, BoardStore

import pytest
import uuid

@pytest.fixture()
def client():
    db_engine = sa.create_engine('sqlite:///data/test_sqlite3.db', echo=True)
    smaker = sessionmaker(db_engine, expire_on_commit=False, class_=Session)
    session = smaker()

    Base.metadata.drop_all(db_engine)

    user_store = UserStore(session)
    message_store = MessageStore(session)
    board_store = BoardStore(session)

    Base.metadata.create_all(db_engine)

    user_1 = User('regular_user', 'password', 'Forum', 'Roamer')
    user_2 = User('inspire', 'letmein', 'Igor', 'Voytenko')
    user_3 = User('botai', '1234', 'Boris', 'Trushin')

    board_1 = Board('В интернете опять кто-то неправ!', user_3)
    board_1.board_id = uuid.UUID('478708b3-1be3-4377-8e39-b2adf004cd1d')
    board_2 = Board('хочу обсудить очень важный вопрос....', user_1)
    board_3 = Board('появился другой вопрос', user_1)

    message_1 = Message('Возьми и разберись в Этом!!', user_2, board_1)
    message_1.message_id = uuid.UUID('c2df51f6-57cc-4838-9318-5980d4fdab9a')

    message_2 = Message('Плохая идея', user_1, board_1)
    message_4 = Message('а хотя...', user_1, board_1)
    message_3 = Message('и что такое?', user_3, board_3)

    session.add(user_1)
    session.add(user_2)
    session.add(user_3)

    session.add(board_1)
    session.add(board_2)
    session.add(board_3)

    session.add(message_1)
    session.add(message_2)
    session.add(message_4)
    session.add(message_3)

    session.commit()

    app = create_app(user_store, message_store, board_store)

    yield testing.TestClient(app)

    Base.metadata.drop_all(db_engine)

def test_registration(client: testing.TestClient):
    result = client.simulate_post(
        '/auth/register',
        json={
            'username': 'vinc3nzo',
            'password': 'letmein',
            'first_name': 'Евгений',
            'last_name': 'Мангасарян'
        }
    )

    assert result.status == falcon.HTTP_201
    
def test_login(client):
    result = client.simulate_post(
        '/auth/register',
        json={
            'username': 'vinc3nzo',
            'password': 'letmein',
            'first_name': 'Евгений',
            'last_name': 'Мангасарян'
        }
    )

    result = client.simulate_post(
        '/auth/login',
        json={
            'username': 'vinc3nzo',
            'password': 'letmein'
        }
    )

    assert result.status == falcon.HTTP_200
    assert 'token' in result.json

def test_users_fetch(client: testing.TestClient):
    token = JWT.create('inspire')
    
    result = client.simulate_get(
        '/users',
        params={
            'page': 0,
            'elements': 10
        },
        json={
            'token': token
        }
    )

    assert result.status == falcon.HTTP_200
    assert result.json[0]['username'] == 'botai'

def test_all_boards_fetch(client: testing.TestClient):
    token = JWT.create('botai')

    result = client.simulate_get(
        '/boards',
        params={
            'page': 0,
            'elements': 10
        },
        json={
            'token': token
        }
    )

    assert result.status == falcon.HTTP_200
    assert result.json[0]['topic'] == 'В интернете опять кто-то неправ!'

def test_one_board_fetch(client: testing.TestClient):
    token = JWT.create('regular_user')

    known_board_id = '478708b3-1be3-4377-8e39-b2adf004cd1d'

    result = client.simulate_get(
        f'/boards/{known_board_id}',
        json={
            'token': token
        }
    )

    assert result.status == falcon.HTTP_200
    assert result.json['created_by']['username'] == 'botai'

def test_board_creation(client: testing.TestClient):
    token = JWT.create('botai')

    result = client.simulate_post(
        '/boards',
        json={
            'token': token,
            'topic': 'Новая стена'
        }
    )

    assert result.status == falcon.HTTP_201
    assert result.headers['location'] is not None

def test_fetch_all_messages(client: testing.TestClient):
    token = JWT.create('regular_user')

    known_board_id = '478708b3-1be3-4377-8e39-b2adf004cd1d'

    result = client.simulate_get(
        f'/boards/{known_board_id}/messages',
        params={
            'page': 0,
            'elements': 10 
        },
        json={
            'token': token
        }
    )

    assert result.status == falcon.HTTP_200
    assert result.json[1]['text'] == 'Плохая идея'

def test_send_message(client: testing.TestClient):
    token = JWT.create('inspire')

    known_board_id = '478708b3-1be3-4377-8e39-b2adf004cd1d'

    result = client.simulate_post(
        f'/boards/{known_board_id}/messages',
        json={
            'token': token,
            'text': 'Тестовое сообщение!!'
        }
    )

    assert result.status == falcon.HTTP_201
    assert 'location' in result.headers

def test_edit_message(client: testing.TestClient):
    token = JWT.create('inspire')

    known_board_id = '478708b3-1be3-4377-8e39-b2adf004cd1d'
    known_message_id = 'c2df51f6-57cc-4838-9318-5980d4fdab9a'

    result = client.simulate_patch(
        f'/boards/{known_board_id}/messages/{known_message_id}',
        json={
            'token': token,
            'text': 'Измененное сообщение!'
        }
    )

    assert result.status == falcon.HTTP_200
    
    result = client.simulate_get(
        f'/boards/{known_board_id}/messages/{known_message_id}',
        json={
            'token': token
        }
    )

    assert result.status == falcon.HTTP_200
    assert result.json['text'] == 'Измененное сообщение!'

def test_edit_someones_message(client: testing.TestClient):
    token = JWT.create('regular_user')

    known_board_id = '478708b3-1be3-4377-8e39-b2adf004cd1d'
    known_message_id = 'c2df51f6-57cc-4838-9318-5980d4fdab9a'

    result = client.simulate_patch(
        f'/boards/{known_board_id}/messages/{known_message_id}',
        json={
            'token': token,
            'text': 'Измененное сообщение!'
        }
    )

    assert result.status == falcon.HTTP_UNAUTHORIZED
    
    result = client.simulate_get(
        f'/boards/{known_board_id}/messages/{known_message_id}',
        json={
            'token': token
        }
    )

    assert result.status == falcon.HTTP_200
    assert result.json['text'] == 'Возьми и разберись в Этом!!'

def test_delete_message(client: testing.TestClient):
    token = JWT.create('inspire')

    known_board_id = '478708b3-1be3-4377-8e39-b2adf004cd1d'
    known_message_id = 'c2df51f6-57cc-4838-9318-5980d4fdab9a'

    result = client.simulate_delete(
        f'/boards/{known_board_id}/messages/{known_message_id}',
        json={
            'token': token
        }
    )

    assert result.status == falcon.HTTP_200
    
    result = client.simulate_get(
        f'/boards/{known_board_id}/messages/{known_message_id}',
        json={
            'token': token
        }
    )

    assert result.status == falcon.HTTP_NOT_FOUND

def test_delete_someones_message(client: testing.TestClient):
    token = JWT.create('botai')

    known_board_id = '478708b3-1be3-4377-8e39-b2adf004cd1d'
    known_message_id = 'c2df51f6-57cc-4838-9318-5980d4fdab9a'

    result = client.simulate_delete(
        f'/boards/{known_board_id}/messages/{known_message_id}',
        json={
            'token': token
        }
    )

    assert result.status == falcon.HTTP_UNAUTHORIZED
    
    result = client.simulate_get(
        f'/boards/{known_board_id}/messages/{known_message_id}',
        json={
            'token': token
        }
    )

    assert result.status == falcon.HTTP_200
    assert result.json['text'] == 'Возьми и разберись в Этом!!'
