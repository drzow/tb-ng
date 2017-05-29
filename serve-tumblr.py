#!/usr/bin/env python3
"""Serve backed up tumblr
"""
import os.path
import copy
import os
import __main__ as main
import operator

from flask import Flask
from flask import render_template
from flask import send_from_directory
import yaml

# Work properly with symlink in path
thisdir = os.path.dirname(os.path.realpath(main.__file__))
app = Flask(__name__, root_path=thisdir)

# Index
print('> Indexing content...')

class DefaultDict(dict):
    def __init__(self, default):
        self.default = default
        super().__init__(self)

    def __getitem__(self, key):
        v = self.get(key, None)
        if v == None:
            self[key] = copy.copy(self.default)
            v = self.get(key)
        return v

def sortdict(d):
    return sorted(d.items(), key=operator.itemgetter(1), reverse=True)

days = os.listdir('posts')
months = DefaultDict(0)
days_in_month = DefaultDict([])
tags = DefaultDict(0)
post_by_tag = DefaultDict([])

days.sort(reverse=True)

for day in days:
    if day[0] == '.': continue
    # Add Month to index
    months[(day[:4], day[5:7])] += 1
    # Index it by month
    days_in_month[day[:7]].append(day)
    # Index posts
    for post in os.listdir('posts/{}'.format(day)):
        if post[0] == '.':
            continue
        fname = 'posts/{}/{}'.format(day, post)
        data = yaml.load(open(fname, 'r').read())
        for tag in data.get('tags', []):
            tags[tag] += 1
            post_by_tag[tag].append((day, post[:-5], data['url'].split('/')[-1]))

@app.route("/")
def index():
    return render_template('index.html', months=months.items(), tags=sortdict(tags))

@app.route('/tagged/<tag>')
def tag_page(tag):
    return render_template('tag.html', tag=tag, posts=post_by_tag[tag])

@app.route('/posts/<day>')
def post_by_day(day):
    posts = []
    t_posts = os.listdir('posts/{}'.format(day))
    for p in t_posts:
        if p[0] == '.': continue
        fname = 'posts/{}/{}'.format(day, p)
        data = yaml.load(open(fname, 'r').read())
        posts.append((day, p[:-5], data['url'].split('/')[-1]))
    return render_template('day.html', day=day, posts=posts)

@app.route('/posts/<day>/<id>')
def post(day, id):
    fname = 'posts/{}/{}.yaml'.format(day, id)
    post = yaml.load(open(fname, 'r').read())
    return render_template('post.html', post=post)

@app.route("/month/<year>/<month>")
def month(year, month):
    return render_template(
        'month.html',
        month=(year, month),
        days=days_in_month['{}-{}'.format(year, month)])

@app.route('/images/<path:f>')
def image(f):
    base = '{}/images'.format(os.getcwd())
    print(base)
    return send_from_directory(base, f)

if __name__ == "__main__":
    app.run()
