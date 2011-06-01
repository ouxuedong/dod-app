# coding: UTF-8

import logging
from datetime import datetime
from functools import wraps

from flask import Flask, request, session, g, redirect, url_for, abort
from flask import render_template, flash, Markup, jsonify
app = Flask(__name__)
app.config.from_object('settings')

from werkzeug.contrib.cache import GAEMemcachedCache
cache = GAEMemcachedCache()

from models import User, Topic, Message

def login_required(f):
    """
    redirects to the index page if the user has no session
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user is None:
            flash('Please log in.')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.before_request
def before_request():
    if 'user_key' in session:
        user_key = session['user_key']
        user = User.get(user_key)
        g.user = user
    else:
        g.user = None


@app.route('/')
def index():
    my_topics = []
    if g.user:
        my_topics = Topic.all().filter('author', g.user).order('-created_at').fetch(limit=50)
        my_main_topics = Topic.all().filter('author', g.user).filter('parent_topic', None).order('-created_at').fetch(limit=50)
    return render_template('index.html', my_topics=my_topics)


@app.route('/poll')
@login_required
def poll():
    messages = []
    topic_key = request.args.get('topic_key')
    if topic_key:
        topic = Topic.get(topic_key)
        if topic:
            offset = int(request.args.get('offset'))
            l = Message.all().filter('topic', topic).order('created_at').fetch(limit=100, offset=offset)
            messages = [{'content': m.content, 'email': m.author.email, 'created_at': pretty_date(m.created_at), 'topic_key': str(m.topic.key())} for m in l]
    return jsonify(messages=messages)

@app.route('/post', methods=['POST'])
@login_required
def post():
    content = ''
    content = request.form.get('content')
    topic_key = request.form.get('topic_key')
    if not topic_key:
        flash('Topic not found.')
    if not content:
        flash('Content required.')
    topic = Topic.get(topic_key) 
    message = Message(content=content, author=g.user, topic=topic)
    message.put()
    return redirect(url_for('discussion', topic_key=topic_key))


@app.route('/create_topic', methods=['GET', 'POST'])
@login_required
def create_topic():
    title = start = end = parent_topic_key = ''
    message = None
    
    if request.method == 'POST':
        title = request.form.get('title')
        if not title:
            flash('Title required.', 'error')
        else:
            topic = Topic(title=title, author=g.user)
            parent_topic_key = request.form.get('parent_topic_key')
            parent_topic = None
            if parent_topic_key:
                parent_topic = Topic.get(parent_topic_key)
                topic.parent_topic = parent_topic
            start = request.form.get('start')
            if start:
                try:
                    start = datetime.strptime(start, '%Y-%m-%d %H:%M')
                except ValueError:
                    start = datetime.now()
                topic.start = start
            end = request.form.get('end')
            if end:
                try:
                    end = datetime.strptime(end, '%Y-%m-%d %H:%M')
                    topic.end = end
                except ValueError:
                    pass
            new_topic_key = topic.put()
            if parent_topic:
                parent_topic.child_topics.append(new_topic_key)
                parent_topic.put()
            flash('Topic "%s" created.!' % title)
            return redirect(url_for('discussion', topic_key=new_topic_key))
    elif request.method == 'GET':
        message_key = request.args.get('message_key')
        if message_key:
            message = Message.get(message_key)
            parent_topic_key = str(message.topic.key())
            start = datetime.now().strftime('%Y-%m-%d %H:%M')
            title = 'On - %s' % message.content

    return render_template('index.html', title=title, start=start, end=end, 
                           parent_topic_key=parent_topic_key, message=message)


@app.route('/change_topic_name', methods=['POST'])
@login_required
def change_topic_name():
    title = request.form.get('title')
    topic_key = request.form.get('topic_key')
    if not title:
        flash('Title required.', 'error')
    if not topic_key:
        flash('Topic not found.', 'error')
    else:
        topic = Topic.get(topic_key)
        topic.title = title
        topic.put()
    return redirect(url_for('discussion', topic_key=topic_key))


@app.route('/discussion/<topic_key>')
@login_required
def discussion(topic_key):
    messages = None
    if topic_key:
        topic = Topic.get(topic_key)
        if not topic:
            flash('No topic found', 'error')
            return redirect(url_for('index'))
        child_topics = []
        for child_topic_key in topic.child_topics:
            child_topics.append(Topic.get(child_topic_key))
        messages = Message.all().filter('topic', topic).order('-created_at').fetch(limit=50)
    return render_template('discussion.html', messages=messages, topic=topic, child_topics=child_topics)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    new_email = new_password = ''
    if request.method == 'POST':
        new_email = request.form.get('new_email')
        new_password = request.form.get('new_password')

        if new_email and new_password:
            user = User(email=new_email, password=new_password)
            user_key = user.put()
            session['user_key'] = user_key
            g.user = user
            flash('Thanks for signing up, %s!' % user.email)
            return redirect(url_for('index'))
        else:
            flash('Email and password required', 'error')
    return render_template('index.html', new_email=new_email, new_password=new_password)


@app.route('/login', methods=['GET', 'POST'])
def login():
    email = password = ''
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.all().filter('email', email).filter('password', password).get()

        if user:
            session['user_key'] = str(user.key())
            g.user = user
            flash('Welcome %s!' % user.email)
            return redirect(url_for('index'))
        else:
            flash('Email and password not matched.', 'error')
    return render_template('index.html', email=email, password=password)


@app.route('/logout')
def logout():
    if 'user_key' in session:
        session.pop('user_key', None)
    return redirect(url_for('index'))


@app.template_filter('pretty_date')
def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc
    """
    now = datetime.now()
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time,datetime):
        diff = now - time
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return  "a minute ago"
        if second_diff < 3600:
            return str( second_diff / 60 ) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str( second_diff / 3600 ) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff/7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff/30) + " months ago"
    return str(day_diff/365) + " years ago"

if __name__ == '__main__':
    app.run(debug=app.config.get('DEBUG'))
