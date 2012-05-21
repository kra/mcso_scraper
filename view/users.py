from flaskext.login import UserMixin

import bcrypt

def password_create(password):
    """Return hashed password entry from plaintext password."""
    return bcrypt.hashpw(password, bcrypt.gensalt())

class User(UserMixin):
    def __init__(self, id, name, password, active=True):
        self.id = id
        self.name = name
        self.password = password
        self.active = active

    def is_active(self):
        return self.active


# XXX testing
USERS = {
#    1: User(1, u"foo", password_create("foo")),
#    2: User(2, u"bar", password_create("bar")),
#    3: User(3, u"baz", password_create("baz"), False),
}

def get_user_id(id):
    # XXX testing
    return USERS.get(int(id))

def get_user_username(username):
    # XXX testing
    try:
        (user,) = [u for u in USERS.values() if u.name == username]
        return user
    except:
        return None

def auth_user(user, password):
    """Validate plaintext password matches the hashed password entry"""
    return bcrypt.hashpw(password, user.password) == user.password
