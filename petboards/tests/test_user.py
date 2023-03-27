import falcon
from falcon import testing

import pytest

from .util import *

from petboards.security import JWT
from petboards.app import create_app

@pytest.fixture
def client(fake_user_store, fake_message_store, fake_board_store) -> testing.TestClient:
    app = create_app(fake_user_store, fake_message_store, fake_board_store)
    return testing.TestClient(app) 

def test_user_login(client: testing.TestClient):
    password = 'password'
    username = 'regular_user'

    result = client.simulate_post(
        '/auth/login',
        json={
            'username': username,
            'password': password
        }
    )

    assert result.status == falcon.HTTP_200
    assert 'location' in result.headers
    assert 'token' in result.json
    assert JWT.validate(result.json['token']) == username

def test_invalid_credentials(client: testing.TestClient):
    password = 'invalid_password'
    username = 'botai'

    result = client.simulate_post(
        '/auth/login',
        json={
            'username': username,
            'password': password
        }
    )

    assert result.status == falcon.HTTP_NOT_FOUND
    assert 'token' not in result.json

def test_bad_login_request(client: testing.TestClient):
    password = None
    username = 'sdai_ege'

    result = client.simulate_post(
        '/auth/login',
        json={
            'username': username,
            'password': password
        }
    )

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert 'token' not in result.json

def test_user_registration(client: testing.TestClient):
    result = client.simulate_post(
        '/auth/register',
        json={
            'username': 'Newcomer',
            'password': 'letmein1234',
            'first_name': 'Gordon',
            'last_name': 'Freeman'
        }
    )

    assert 'error' not in result.json
    assert result.status == falcon.HTTP_201

    result = client.simulate_post(
        '/auth/login',
        json={
            'username': 'Newcomer',
            'password': 'letmein1234'
        }
    )

    assert result.status == falcon.HTTP_200
    assert 'location' in result.headers

def test_fetch_all_users(client: testing.TestClient):
    token = JWT.create('botai')

    # TODO

    result = client.simulate_get(
        f'/users',
        params={
            'page': 0,
            'elements': 20
        },
        json={
            'token': token
        }
    )

    assert result.status == falcon.HTTP_200
    assert type(result.json) == list

def test_fetch_user_by_user_id(client: testing.TestClient):
    known_user_id = '2423a6e6-eb92-416e-b155-65cfa448966b'
    token = JWT.create('sdai_ege')

    result = client.simulate_get(
        f'/users/{known_user_id}',
        json={
            'token': token
        })

    assert result.status == falcon.HTTP_200
    assert result.json['username'] == 'regular_user'

def test_fetch_non_existing_user_by_user_id(client: testing.TestClient):
    non_existing_user_id = '00000000-eb92-416e-b155-65cfa448966b'
    token = JWT.create('regular_user')

    result = client.simulate_get(
        f'/users/{non_existing_user_id}',
        json={
            'token': token
        }
    )

    assert result.status == falcon.HTTP_NOT_FOUND
    assert 'username' not in result.json

def test_fetch_user_by_invalid_user_id(client: testing.TestClient):
    invalid_uuid = 'hello-I-am-uu-id'
    token = JWT.create('botai')

    result = client.simulate_get(
        f'/users/{invalid_uuid}',
        json={
            'token': token
        }
    )
    
    assert result.status == falcon.HTTP_NOT_FOUND
    assert 'username' not in result.json
