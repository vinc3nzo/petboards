from sqlalchemy.orm import sessionmaker, Session
import sqlalchemy as sa

from .user import UserStore
from .app import create_app
from .board import BoardStore, MessageStore
from .persistency import Base

import os
import sys

if os.getenv('PETBOARDS_SECRET') is None:
    print('The environment variable \'PETBOARDS_SECRET\', which is used as a secret for the Json Web Token, is not set. Please, consider setting it before running the application.', file=sys.stderr)
    sys.exit(1)

db_engine = sa.create_engine('sqlite:///data/sqlite3.db', echo=True)
smaker = sessionmaker(db_engine, expire_on_commit=False, class_=Session)
session = smaker()

user_store = UserStore(session)
message_store = MessageStore(session)
board_store = BoardStore(session)

Base.metadata.create_all(db_engine)

app = create_app(user_store, message_store, board_store)