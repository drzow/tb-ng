#!/usr/bin/env python3
"""Serve backed up tumblr
"""
import os.path
import os
import sqlite3
import json
import __main__ as main

from flask import Flask
from flask import render_template
from flask import request
from flask import send_from_directory
import yaml

# Work properly with symlink in path
thisdir = os.path.dirname(os.path.realpath(main.__file__))
app = Flask(__name__, root_path=thisdir)

# Index
print('> Indexing content...')
database = sqlite3.connect(':memory:')

class Post(sqlite3.Row):
    """Extension of sqlite3 row to include some generic tumblr stuff
    """
    @property
    def year(self):
        return self['month'].split('-')[0]

    @property
    def month_month(self):
        return self['month'].split('-')[1]

    @property
    def tags(self):
        """Find all of the tags this post is associated with
        """
        return [t['tag'] for t in database.execute(
            'SELECT tag FROM tags WHERE post_id = ?', [self['id']])]

    @property
    def photos(self):
        """Decode the photos associated with this post (if any)
        """
        return json.loads(self['photos']) or []

database.row_factory = Post

database.execute('CREATE TABLE posts (caption text, created date, month text, id text, photos text, url text)')
database.execute('CREATE TABLE tags (tag text, post_id text)')

days = os.listdir('posts')
for day in days:
    if day[0] == '.':
        continue
    month = '-'.join(day.split('-')[:2])
    # Index posts
    for post in os.listdir('posts/{}'.format(day)):
        if post[0] == '.':
            continue
        fname = 'posts/{}/{}'.format(day, post)
        data = yaml.load(open(fname, 'r').read())
        database.execute(
            'INSERT INTO posts (caption, created, month, id, photos, url) VALUES (?, ?, ?, ?, ?, ?)',
            [
                data.get('caption', ''),
                day,
                month,
                data.get('id', 0),
                json.dumps(data.get('photos', None)),
                data.get('url', '')])
        for tag in data.get('tags', []):
            database.execute(
                'INSERT INTO tags (tag, post_id) VALUES (?, ?)',
                [tag, data.get('id', 0)])

print('> Sqlite index complete')

def pagination(sql):
    """Paginate the response
    """
    return sql
    '''
    TODO: Implement properly
    sql += ' LIMIT 20'
    if 'from' in request.args:
        sql += ' OFFSET {:d}'.format(request.args.get('from'))
    return sql
    '''

@app.route("/")
def index():
    return render_template(
        'index.html',
        months=database.execute((
            'SELECT month, (SELECT COUNT(id) FROM posts WHERE month = p.month) '
            'AS count FROM posts p GROUP BY month ORDER BY month DESC')),
        tags=database.execute((
            'SELECT tag, (SELECT COUNT(post_id) FROM tags WHERE tag = t.tag) AS count '
            'FROM tags t GROUP BY tag ORDER BY count DESC')))

@app.route('/tagged/<tag>')
def tag_page(tag):
    return render_template(
        'tag.html',
        tag=tag,
        posts=database.execute(
            pagination(
                'SELECT * FROM posts JOIN tags ON tags.post_id = posts.id WHERE tags.tag = ?'),
            [tag]))

@app.route('/posts/<day>')
def post_by_day(day):
    return render_template(
        'day.html',
        day=day,
        posts=database.execute(
            pagination('SELECT * FROM posts WHERE created = ?'), [day]))

@app.route('/posts/<day>/<id>')
def post(day, id):
    return render_template('post.html', post=database.execute(
        'SELECT * FROM posts WHERE id = ?', [id]).fetchone())

@app.route("/month/<year>/<month>")
def month(year, month):
    return render_template(
        'month.html',
        month=(year, month),
        posts=database.execute(
            pagination('SELECT * FROM posts WHERE month = ? ORDER BY created DESC'),
            ['{}-{}'.format(year, month)]))

@app.route('/images/<path:f>')
def image(f):
    base = '{}/images'.format(os.getcwd())
    return send_from_directory(base, f)

if __name__ == "__main__":
    app.run()
