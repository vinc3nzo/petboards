import uuid
import bcrypt

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, relationship

from typing import List
from datetime import datetime

from .persistency import Base

class User(Base):
    __tablename__ = 'users'

    user_id = sa.Column(sa.Uuid, primary_key=True, autoincrement=False)
    username = sa.Column(sa.String(128), unique=True, nullable=False)
    _password = sa.Column(sa.LargeBinary, nullable=False)
    first_name = sa.Column(sa.String(128))
    last_name = sa.Column(sa.String(128))
    registered = sa.Column(sa.DateTime())
    last_login = sa.Column(sa.DateTime())
    boards: Mapped[List['Board']] = relationship('Board', back_populates='created_by')

    def __init__(self, username: str, password: str, first_name: str, last_name: str):
        self.user_id = uuid.uuid4()
        self.username: str = username
        self._password: bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.first_name: str = first_name
        self.last_name: str = last_name
        self.registered: datetime = datetime.utcnow()
        self.last_login: datetime = self.registered

    def serialize(self) -> dict:
        return {
            'user_id': str(self.user_id),
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'registered': self.registered.timestamp(),
            'last_login': self.last_login.timestamp(),
            'boards': [
                {
                    'board_id': str(b.board_id),
                    'topic': b.topic,
                    'created_at': b.created_at.timestamp(),
                    'first_message': {
                        'message_id': str(b.messages[0].message_id),
                        'text': b.messages[0].text,
                        'author_id': str(b.messages[0].author_id),
                        'timestamp': b.messages[0].timestamp.timestamp(),
                        'last_edited': b.messages[0].last_edited.timestamp()
                    } if len(b.messages) > 0 else None
                }
                for b in self.boards
            ]
        }

class Message(Base):
    __tablename__ = 'messages'

    message_id = sa.Column(sa.Uuid, primary_key=True, autoincrement=False)
    text = sa.Column(sa.String(2048), nullable=False)
    timestamp = sa.Column(sa.DateTime(), nullable=False)
    last_edited = sa.Column(sa.DateTime(), nullable=True)

    author_id = sa.Column(sa.ForeignKey('users.user_id'))
    author: Mapped['User'] = relationship('User')

    board_id = sa.Column(sa.ForeignKey('boards.board_id'))
    board: Mapped['Board'] = relationship('Board', back_populates='messages')

    def __init__(self, text: str, author: User, board: 'Board'):
        self.message_id = uuid.uuid4()
        self.text = text
        self.author = author
        self.board = board
        self.timestamp = datetime.utcnow()
        self.last_edited = self.timestamp

    def serialize(self) -> dict:
        return {
            'message_id': str(self.message_id),
            'text': self.text,
            'author_id': str(self.author_id),
            'board_id': str(self.board_id),
            'timestamp': self.timestamp.timestamp(),
            'last_edited': self.last_edited.timestamp()
        }
    

class Board(Base):
    __tablename__ = 'boards'

    board_id = sa.Column(sa.Uuid, primary_key=True, autoincrement=False)
    topic = sa.Column(sa.String(256), nullable=False)
    created_at = sa.Column(sa.DateTime(), nullable=False)

    creator_id = sa.Column(sa.ForeignKey('users.user_id'))
    created_by: Mapped['User'] = relationship('User', back_populates='boards')

    messages: Mapped[List['Message']] = relationship('Message', back_populates='board')

    def __init__(self, topic: str, created_by: User):
        self.board_id = uuid.uuid4()
        self.topic = topic
        self.created_by = created_by
        self.created_at = datetime.utcnow()
        self.messages = []

    def serialize(self) -> dict:
        return {
            'board_id': str(self.board_id),
            'topic': self.topic,
            'created_at': self.created_at.timestamp(),
            'created_by': {
                'user_id': str(self.created_by.user_id),
                'username': self.created_by.username,
                'first_name': self.created_by.first_name,
                'last_name': self.created_by.last_name,
                'registered': self.created_by.registered.timestamp(),
                'last_login': self.created_by.last_login.timestamp(),
            },
            'first_message': {
                'message_id': str(self.messages[0].message_id),
                'text': self.messages[0].text,
                'author_id': str(self.messages[0].author_id),
                'timestamp': self.messages[0].timestamp.timestamp(),
                'last_edited': self.messages[0].last_edited.timestamp()
            } if len(self.messages) > 0 else None
        }