import falcon
from falcon import testing

import pytest
import uuid

from petboards.models import User

from unittest.mock import MagicMock

@pytest.fixture
def fake_user_store():
    user_1 = User('regular_user', 'password', 'Forum', 'Roamer')
    user_2 = User('inspire', 'letmein', 'Igor', 'Voytenko')
    user_3 = User('botai', '1234', 'Boris', 'Trushin')

    user_1.user_id = uuid.UUID('2423a6e6-eb92-416e-b155-65cfa448966b')

    all_users = {
        user_1.user_id: user_1,
        user_2.user_id: user_2,
        user_3.user_id: user_3
    }

    fake_user_store = MagicMock()

    # Note to self:
    # if I needed to, I could use `fake_user_store`
    # instead of `self` in these methods.

    def fake_get_all(page: int, elements: int) -> list[User]:
        if page * elements > len(all_users):
            return list(all_users.values())[0:0]
        elif page * elements + elements > len(all_users):
            return list(all_users.values())[page * elements:len(all_users)]
        else:
            return list(all_users.values())[page * elements:page * elements + elements]

        return future

    def fake_get_by_username(username: str) -> User | None:
        res = None
        for user in all_users.values():
            if user.username == username:
                res = user
                break

        return res

    def fake_save(user: User) -> None:
        all_users[user.user_id] = user
        return None

    def fake_get(user_id: uuid.uuid4) -> User | None:
        res = None
        if user_id in all_users:
            res = all_users[user_id]
        
        return res

    fake_user_store.get = fake_get
    fake_user_store.get_all = fake_get_all
    fake_user_store.get_by_username = fake_get_by_username
    fake_user_store.save = fake_save

    return fake_user_store

@pytest.fixture
def fake_message_store():
    return MagicMock()

@pytest.fixture
def fake_board_store():
    return MagicMock()