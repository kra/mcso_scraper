from flask.ext.login import UserMixin

import bcrypt


class User(UserMixin):
    def __init__(self, id, name, password, active=True):
        self.id = id
        self.name = name
        self.password = password
        self.active = active

    def is_active(self):
        return self.active


def password_create(password):
    """Return hashed password entry from plaintext password."""
    return bcrypt.hashpw(password, bcrypt.gensalt())

def _user_row(conn, query, arg):
    rows = [r for r in conn.execute(query, (arg,))]
    if not rows:
        return None
    (row,) = rows
    return User(*row)

def get_user_id(conn, id):
    return _user_row(
        conn,
        'SELECT rowid, name, password, active FROM users WHERE rowid=?',
        id)

def get_user_username(conn, username):
    return _user_row(
        conn,
        'SELECT rowid, name, password, active FROM users WHERE name=?',
        username)

def auth_user(user, password):
    """Validate plaintext password matches the hashed password entry"""
    return bcrypt.hashpw(password, user.password) == user.password
