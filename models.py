# coding: UTF-8

from google.appengine.ext import db

from main import app


class Base(db.Model):
    status = db.IntegerProperty()
    created_at = db.DateTimeProperty(auto_now_add=True)
    updated_at = db.DateTimeProperty(auto_now_add=True)


class User(Base):
    name = db.StringProperty()
    email = db.EmailProperty()
    password = db.StringProperty()


class Topic(Base):
    title = db.StringProperty(multiline=True)
    author = db.ReferenceProperty(reference_class=User)
    parent_topic = db.SelfReferenceProperty()
    child_topics = db.ListProperty(item_type=db.Key)
    start = db.DateTimeProperty()
    end  = db.DateTimeProperty()


class Message(Base):
    content = db.StringProperty(multiline=True)
    author = db.ReferenceProperty(reference_class=User)
    topic = db.ReferenceProperty(reference_class=Topic)
