from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from flaskr.auth import login_required
from flaskr.db import get_db

import math

bp = Blueprint('blog', __name__)


@bp.route('/')
def index():
    # Receive two parameters ?page=1&per_page=5

    # Current page
    page = request.args.get('page', 1, type=int)

    # Number of rows to fetch from the database
    limit = request.args.get('per_page', 5, type=int)

    # Number of rows to skip
    offset = (page - 1) * limit

    db = get_db()
    all_posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, featured'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
        ' LIMIT ' + str(offset) + ', ' + str(limit)
    ).fetchall()

    return render_template('blog/index.html', posts=all_posts)


@bp.route('/<int:id>/')
def details(id):
    db = get_db()
    post = get_post(id, check_author=False)
    return render_template('blog/post_details.html', post=post)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        featured = 0 if request.form.get('featured') is None else 1
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id, featured)'
                ' VALUES (?, ?, ?, ?)',
                (title, body, g.user['id'], featured)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')


def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username, featured'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        featured = 0 if request.form.get('featured') is None else 1
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?, featured = ?'
                ' WHERE id = ?',
                (title, body, featured, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    mark_checked = "checked" if post["featured"] == 1 else ""

    return render_template('blog/update.html', post=post, mark_checked=mark_checked)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))
