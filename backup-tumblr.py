#!/usr/bin/env python3
"""Backup tumblr
"""
import hashlib
import json
import os
import os.path
import re

import requests
import yaml
from bs4 import BeautifulSoup

apiKey = 'WbsJ956UmHw5jX6dkt0EshzhUbbU2tZ3LrLk19QGlysmrZrMS2'
config = {
    'filter_tags': []
}
config.update(yaml.load(open('./config.yaml', 'r')))
print(config)

if 'state' not in config:
    config['state'] = {
        'start': 0,
        'newest': -1
    }

def download_image(url, post):
    try:
       filename = './images/{}/{}.{}'.format(
           post['date'][:10], hashlib.sha256(url.encode('ascii')).hexdigest(),
           url.split('.')[-1])
       print('> Download {}'.format(url))
       r = requests.get(url, stream=True)
       if r.status_code == 200:
           dirname = os.path.dirname(filename)
           if not os.path.exists(dirname):
               os.makedirs(dirname)
           with open(filename, 'wb') as f:
               for part in r:
                   f.write(part)
           return filename
       else:
           print('>> Fail postid: {} image: {}'.format(post['id'], url))
           return url
    except AttributeError:
       print('>> Fail postid: {} image: {}'.format(post['id'], url))
       return url

def process_caption(caption, post):
    soup = BeautifulSoup(caption, 'html.parser')
    for image in soup.find_all('img'):
        image['src'] = download_image(image['src'], post)
    for embeddedvid in soup.find_all('figure'):
        try:
            # Remove the surrounding quotes from the data-npf element of the tag
            data_npf = re.sub(r'^['"]+|["']+$', '', embeddedvid['data-npf'])
            # unescape any quotes in the remaining string
            data_npf = re.sub(r'\"', '"', data_npf)
            # decode the json content as a dictionary
            data_npf_dict = json.loads(data_npf)
            # extract the url, and download it
            data_npf_dict['url'] = download_image(data_npf_dict['url'], post)
            # propigate the url to media/url
            data_npf_dict['media']['url'] = data_npf_dict['url']
            # reconstruct the data_npf
            data_npf = "''" + json.dumps(data_npf_dict) + "''"
            # and stick the updated data_npf back into the figure tag
            embeddedvid['data-npf'] = data_npf
        except KeyError:
            next
    return soup.prettify(formatter="minimal")

first_id = None

while True:
    print('> Fetching posts with offset {}'.format(config['state']['start']))
    url = 'http://api.tumblr.com/v2/blog/{}/posts'.format(config['blog'])
    resp = requests.get(url, params={
        'offset': config['state']['start'],
        'tag': config.get('tag', None),
        'api_key': apiKey
    })
    if resp.status_code == 200:
        posts = resp.json()['response']['posts']
        if len(posts) == 0:
            # No more posts
            config['state']['start'] = 0
            break
        stop = False
        for post in posts:
            if post['id'] == config['state']['newest']:
                stop = True
                break
            if first_id is None and config['state']['start'] == 0:
                first_id = post['id']
            data = {
                'url': post['post_url'],
                'id': post['id'],
                'tags': post['tags'],
            }
            # Filter Tags
            skip = False
            for tag in config['filter_tags']:
                if tag not in post['tags']:
                    print('>> Skipping post as it is not tagged {}'.format(tag))
                    skip = True
            if skip:
                continue
            # Normalise posts into yaml format for easy re-rendering
            if post['type'] == 'photo':
                data['caption'] = process_caption(post['caption'], post)
                data['photos'] = []
                for photo in post['photos']:
                    data['photos'].append(
                        download_image(photo['original_size']['url'], post))
            elif post['type'] == 'text':
                data['caption'] = process_caption(post['body'], post)
            elif post['type'] == 'answer':
                data['question'] = {
                    'who': post['asking_name'],
                    'text': post['question'],
                }
                data['caption'] = process_caption(post['answer'], post)
            elif post['type'] == 'link':
                data['link'] = {
                    'to': post['url'],
                    'text': post['title'],
                }
                data['caption'] = process_caption(post['description'], post)
            elif post['type'] == 'video':
                data['video'] = {
                    'embed': post['player'][-1]['embed_code'],
                    'url': post.get('permalink_url', post.get('video_url', None)),
                }
                data['caption'] = process_caption(post['caption'], post)
                data['videofile'] = download_image(post.get('permalink_url', post.get('video_url', None)), post)
            else:
                print('> post type {} not handled'.format(post['type']))
            filename = './posts/{}/{}.yaml'.format(post['date'][:10], post['id'])
            dirname = os.path.dirname(filename)
            if not os.path.exists(dirname):
                os.makedirs(dirname)
            with open(filename, 'w') as f:
                f.write(yaml.dump(data))
        if stop:
            break
        config['state']['start'] += len(posts)
    else:
        print('> Tumblr returned {}'.format(resp.status_code))
        print(resp.headers)
        break

if first_id is not None:
    config['state']['newest'] = first_id

print('> Save state')
with open('./config.yaml', 'w') as f:
    f.write(yaml.dump(config))
