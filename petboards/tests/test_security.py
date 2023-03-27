import falcon
from falcon import testing

import pytest

from .util import *

from datetime import timedelta

from petboards.security import JWT
from petboards.app import create_app

@pytest.fixture
def client(fake_user_store, fake_message_store, fake_board_store) -> testing.TestClient:
    app = create_app(fake_user_store, fake_message_store, fake_board_store)
    return testing.TestClient(app) 

def test_unauthorized_requests(client: testing.TestClient):
    result = client.simulate_get(f'/users')
    
    assert result.status == falcon.HTTP_UNAUTHORIZED

    user_id = '00000000-eb92-416e-b155-65cfa448966b'
    result = client.simulate_get(f'/users/{user_id}')

    assert result.status == falcon.HTTP_UNAUTHORIZED

def test_token_expiry(client: testing.TestClient):
    expired_token = JWT.create('regular_user', timedelta(seconds=-1))

    result = client.simulate_get(
        '/users',
        json={
            'token': expired_token
        }
    )

    assert result.status == falcon.HTTP_UNAUTHORIZED
