# tb-ng

Tumblr Backup Next Generation

This is a new version of tumblr-backup, a script I wrote in NodeJS to backup a tumblr.

This version is written in Python, and it is a lot better including the ability to
just backup a tag and have incermental backups.

## Get started

1. Install deps: `pip install -r requirements.txt`
2. Add `backup-tumblr.py` and `serve-tumblr.py` to your PATH.
3. Add a `config.yml` file to the directory you want to backup in
4. Run `backup-tumblr.py` and wait for it to finish

The config.yml file includes the following:

```yaml
blog: staff.tumblr.com
tag: ask
```

Now you will get two directories, posts and images.

You can serve them up using `serve-tumblr.py`

## How it works

Using the Tumblr API it fetches posts, and then reduces the JSON down to
something which works for most post types easily.

These are then saved as YAML files, and images are replaced for locally
downloaded copies.

The server loads the posts into a memory Sqlite database which allows
for easy querying. Flask is used to easily provide a frontend to
render posts with.
