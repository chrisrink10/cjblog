"""cjblog :: admin module

Renders most of the pages of cjrink.com/admin.

Author: Christopher Rink (chrisrink10 at gmail dot com)"""
from datetime import datetime
from functools import update_wrapper
import traceback
from flask import (Blueprint,
                   current_app,
                   render_template,
                   session,
                   abort,
                   redirect,
                   url_for,
                   request)
import config
import database
import util


admin = Blueprint("admin", __name__, url_prefix='/admin')


def login_required(func):
    """Checks whether the user has a valid session."""
    def decorator(*args, **kwargs):
        if not 'username' in session or not 'key' in session:
            current_app.logger.debug("Could not find 'username' or 'key'.")
            session.clear()
            abort(403)

        # Check whether session values are either expired or invalid
        valid, current = database.check_session(session['username'],
                                                session['key'])
        if not valid:
            current_app.logger.debug("Invalid session submitted.")
            session.clear()
            abort(403)
        if not current:
            current_app.logger.debug("Expired session for '{}'".format(
                session['username']
            ))
            session.clear()
            return redirect(url_for("login", expired=True))
        return func(*args, **kwargs)

    return update_wrapper(decorator, func)


@admin.route('/')
@login_required
def home():
    """Render the administrator home page."""
    return render_template("home.html",
                           released=database.get_articles(with_body=False,
                                                          with_links=False,
                                                          released=True),
                           unreleased=database.get_articles(with_body=False,
                                                            released=False))


@admin.route('/config', methods=['GET'])
@login_required
def edit_config():
    return render_template("config.html",
                           sidebar_blurb_markdown=config.ABOUT_BLURB,
                           page_size=config.PAGE_SIZE,
                           session_expire=config.SESSION_EXPIRE,
                           session_prune_age=config.SESSION_PRUNE_AGE)


@admin.route('/config', methods=['POST'])
@login_required
def save_config():
    data = {}
    error = None
    try:
        data['main_title'] = request.form['main_title']
        data['subtitle'] = request.form['subtitle']
        data['browser_title'] = request.form['browser_title']
        data['footer_text'] = request.form['footer_text']
        data['image_location'] = request.form['image_location']
        data['image_alt'] = request.form['image_alt']
        data['about_blurb'] = request.form['about_blurb']
        data['page_size'] = int(request.form['page_size'])
        data['session_expire'] = int(request.form['session_expire'])
        data['session_prune_age'] = int(request.form['session_prune_age'])
        if data['session_expire'] < 1 or data['session_prune_age'] < 1 or data['page_size'] < 1:
            raise ValueError

        database.save_config(data)
    except TypeError:
        current_app.logger.debug(traceback.format_exc())
        error = "Session expire and session prune age must be integer values."
    except ValueError:
        current_app.logger.debug(traceback.format_exc())
        error = str("Session expire and session prune age must be integer "
                    "values greater than or equal to 1.")
    return render_template("config.html",
                           error=error,
                           sidebar_blurb_markdown=config.ABOUT_BLURB,
                           page_size=config.PAGE_SIZE,
                           session_expire=config.SESSION_EXPIRE,
                           session_prune_age=config.SESSION_PRUNE_AGE)


@admin.route('/create', methods=['GET'])
@login_required
def create_article():
    """Render the article creation page."""
    return render_template("edit.html",
                           article={'title': ""},
                           create=True)


@admin.route('/create', methods=['POST'])
@login_required
def save_new_article():
    """Render the article creation page."""
    new_id = database.create_article(request.form['title'],
                                     request.form['title_link'],
                                     request.form['title_alt'],
                                     request.form['date'],
                                     request.form['body'],
                                     1 if 'released' in request.form else 0,
                                     request.form['tags'])
    return redirect(url_for("admin.edit_article", article_id=new_id))


@admin.route('/delete/<int:article_id>')
@login_required
def delete_article(article_id):
    """Delete an article and then redirect home."""
    database.delete_article(article_id)
    return redirect(url_for('admin.home'))


@admin.route('/edit/<int:article_id>', methods=['GET'])
@login_required
def edit_article(article_id):
    """Render the article editing page."""
    article = database.get_article(article_id, render=False)
    return render_template("edit.html",
                           article=article,
                           edit=True)


@admin.route('/edit/<int:article_id>', methods=['POST'])
@login_required
def save_article(article_id):
    """Save changes to an article."""
    current_app.logger.debug(request.form)
    database.save_article(article_id,
                          request.form['title'],
                          request.form['title_link'],
                          request.form['title_alt'],
                          request.form['date'],
                          request.form['body'],
                          1 if 'released' in request.form else 0,
                          request.form['tags'])
    return redirect(url_for("admin.edit_article", article_id=article_id))


@admin.route('/links')
@login_required
def edit_links():
    """Render the sidebar links configuration page."""
    return render_template("links.html")


@admin.route('/links/add', methods=['POST'])
@login_required
def add_link():
    """Add a new sidebar link."""
    current_app.logger.debug(request.form)
    database.add_sidebar_link(article_id=request.form['article'],
                              external_link=request.form['external_link'],
                              link_text=request.form['link_text'],
                              link_alt=request.form['link_alt'])
    return redirect(url_for("admin.edit_links"))


@admin.route('/links/delete/<int:link_id>')
@login_required
def delete_link(link_id):
    """Delete a sidebar link."""
    database.delete_sidebar_link(link_id)
    return redirect(url_for("admin.edit_links"))


@admin.route('/tomarkdown', methods=['POST'])
@login_required
def to_markdown():
    """Given some body text in Markdown, return valid HTML."""
    body = request.data.decode('utf8')
    return util.mkdown(body)


@admin.route('/now')
def current_date():
    """Returns a properly formatted date for now."""
    return database.date_to_str(datetime.today().timestamp())
