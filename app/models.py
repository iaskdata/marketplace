from hashlib import md5
import re
from app import db
from app import app
from config import WHOOSH_ENABLED

import sys
if sys.version_info >= (3, 0):
    enable_search = False
else:
    enable_search = WHOOSH_ENABLED
    if enable_search:
        import flask.ext.whooshalchemy as whooshalchemy

"""
categories = db.Table(
    'categories',
    db.Column('user_id', db.Integer, db.ForeignKey('user.user_id')),
    db.Column('category_id', db.Integer, db.ForeignKey('category.user_id'))
)
"""

class Category(db.Model):
    category_id = db.Column(db.Integer, index = True, primary_key = True)
    category = db.Column(db.String(20))

"""
    The base class for users.
    Experts and non-experts (who pay to talk to experts) inherit from this class. 
"""
class BaseUser(db.Model):
    """
    categories = db.relationship('User',
                               secondary=followers,
                               primaryjoin=(followers.c.follower_id == id),
                               secondaryjoin=(followers.c.followed_id == id),
                               backref=db.backref('followers', lazy='dynamic'),
                               lazy='dynamic')
    """

    user_id = db.Column(db.Integer, index = True, primary_key = True)
    email = db.Column(db.String(120), index=True, unique=True)
    last_seen = db.Column(db.DateTime)
    name = db.Column(db.String(10), index = True)
    company = db.Column(db.String(50), index = True)
    title = db.Column(db.String(20), index = True)  #CEO, VP, etc.
    about_me = db.Column(db.String(500))

class Customer(BaseUser):
    phone_number = db.Column(db.String(20), index=True, unique=True)

class Expert(BaseUser):
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    education = db.Column(db.String(50))
    skills = db.Column(db.String(500))
    rating = db.Column(db.Float)
    wanted_count = db.Column(db.Integer)  #the number of thumb-ups this guy has received (both answers and articles)
    phone_rate = db.Column(db.Float)
    expert_flag = db.Column(db.Boolean)
    category_1_index = db.Column(db.Integer)  #the category hierarchy is specified in the expert_categories.txt file
    category_2_index = db.Column(db.Integer)

    @staticmethod
    def make_valid_nickname(nickname):
        return re.sub('[^a-zA-Z0-9_\.]', '', nickname)

    @staticmethod
    def make_unique_nickname(nickname):
        if User.query.filter_by(nickname=nickname).first() is None:
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if User.query.filter_by(nickname=new_nickname).first() is None:
                break
            version += 1
        return new_nickname

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def avatar(self, size):
        return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % \
            (md5(self.email.encode('utf-8')).hexdigest(), size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        return Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id).order_by(
                    Post.timestamp.desc())

    def __repr__(self):  # pragma: no cover
        return '<User %r>' % (self.nickname)


class Post(db.Model):
    __searchable__ = ['body']

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    language = db.Column(db.String(5))

    def __repr__(self):  # pragma: no cover
        return '<Post %r>' % (self.body)


if enable_search:
    whooshalchemy.whoosh_index(app, Post)