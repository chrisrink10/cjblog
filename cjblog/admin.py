"""cjblog :: admin module

Renders most of the pages of cjrink.com/admin.

Author: Christopher Rink (chrisrink10 at gmail dot com)"""
import datetime
import functools
import importlib

from flask import (Blueprint,
                   current_app,
                   render_template,
                   session,
                   abort,
                   redirect,
                   url_for,
                   request)
import cjblog.config as config
import cjblog.database as database
import cjblog.util as util


admin = Blueprint("admin", __name__, url_prefix='/admin')


def login_required(func):
    """Checks whether the user has a valid session."""
    def decorator(*args, **kwargs):
        if 'username' not in session or 'key' not in session:
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

    return functools.update_wrapper(decorator, func)


@admin.route('/')
@login_required
def home():
    """Render the administrator home page."""
    return render_template("admin.html",
                           admin=True,
                           released=database.get_articles(with_body=False,
                                                          with_links=False,
                                                          released=True),
                           unreleased=database.get_articles(with_body=False,
                                                            released=False),
                           adm_page_list=database.get_pages(with_body=False,
                                                            released=None,
                                                            only_links=False))


@admin.route('/config', methods=['GET'])
@login_required
def edit_config():
    return render_template("config.html",
                           admin=True,
                           page_size=config.PAGE_SIZE,
                           session_expire=config.SESSION_EXPIRE,
                           session_prune_age=config.SESSION_PRUNE_AGE,
                           page_list=database.get_pages(with_body=False,
                                                        released=None))


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
        data['page_size'] = int(request.form['page_size'])
        data['session_expire'] = int(request.form['session_expire'])
        data['session_prune_age'] = int(request.form['session_prune_age'])
        if (data['session_expire'] < 1 or
                data['session_prune_age'] < 1 or
                data['page_size'] < 1):
            raise ValueError

        database.save_config(data)
    except TypeError:
        error = str("Page size, session expire and session prune age must be "
                    "integer values.")
    except ValueError:
        error = str("Page size, session expire, and session prune age must be "
                    "integer values greater than or equal to 1.")
    except util.CompileError:
        error = str("There was an error compiling the configuration options you"
                    " selected. Please try again.")
    else:
        # If no exception occurred, reload the configuration file
        importlib.reload(config)

    return render_template("config.html",
                           admin=True,
                           error=error,
                           page_size=config.PAGE_SIZE,
                           session_expire=config.SESSION_EXPIRE,
                           session_prune_age=config.SESSION_PRUNE_AGE,
                           page_list=database.get_pages(with_body=False,
                                                        released=None))


@admin.route('/article/create', methods=['GET'])
@login_required
def create_article():
    """Render the article creation page."""
    return render_template("edit_article.html",
                           admin=True,
                           article={'title': ""},
                           create=True,
                           page_list=database.get_pages(with_body=False,
                                                        released=None))


@admin.route('/article/create', methods=['POST'])
@login_required
def save_new_article():
    """Save a new article and then redirect to the edit page for that
    new article."""
    new_id = database.create_article(request.form['title'],
                                     request.form['title_link'],
                                     request.form['title_alt'],
                                     request.form['date'],
                                     request.form['body'],
                                     1 if 'released' in request.form else 0,
                                     request.form['tags'])
    return redirect(url_for("admin.edit_article", article_id=new_id))


@admin.route('/article/delete/<int:article_id>')
@login_required
def delete_article(article_id):
    """Delete an article and then redirect home."""
    database.delete_article(article_id)
    return redirect(url_for('admin.home'))


@admin.route('/article/edit/<int:article_id>', methods=['GET'])
@login_required
def edit_article(article_id):
    """Render the article editing page."""
    article = database.get_article(article_id, render=False)
    return render_template("edit_article.html",
                           admin=True,
                           article=article,
                           edit=True,
                           page_list=database.get_pages(with_body=False,
                                                        released=None))


@admin.route('/article/edit/<int:article_id>', methods=['POST'])
@login_required
def save_article(article_id):
    """Save changes to an article."""
    database.save_article(article_id,
                          request.form['title'],
                          request.form['title_link'],
                          request.form['title_alt'],
                          request.form['date'],
                          request.form['body'],
                          1 if 'released' in request.form else 0,
                          request.form['tags'])
    return redirect(url_for("admin.edit_article", article_id=article_id))


@admin.route('/page/create', methods=['GET'])
@login_required
def create_page():
    """Render the page creation page."""
    return render_template("edit_page.html",
                           admin=True,
                           page={'title': ""},
                           create=True,
                           page_list=database.get_pages(with_body=False,
                                                        released=None))


@admin.route('/page/create', methods=['POST'])
@login_required
def save_new_page():
    """Save a new page and then redirect to the edit page for that new page."""
    new_id = database.create_page(1 if 'released' in request.form else 0,
                                  request.form['pg_order'],
                                  request.form['title'],
                                  1 if 'incl_link' in request.form else 0,
                                  request.form['body'])
    return redirect(url_for("admin.edit_page", page_id=new_id))


@admin.route('/page/delete/<int:page_id>')
@login_required
def delete_page(page_id):
    """Delete a page and then redirect home."""
    database.delete_page(page_id)
    return redirect(url_for('admin.home'))


@admin.route('/page/edit/<int:page_id>', methods=['GET'])
@login_required
def edit_page(page_id):
    """Render the page editing page."""
    page = database.get_page(page_id, render=False)
    return render_template("edit_page.html",
                           admin=True,
                           page=page,
                           edit=True,
                           page_list=database.get_pages(with_body=False,
                                                        released=None))


@admin.route('/page/edit/<int:page_id>', methods=['POST'])
@login_required
def save_page(page_id):
    """Save changes to a page."""
    database.save_page(page_id,
                       1 if 'released' in request.form else 0,
                       request.form['pg_order'],
                       request.form['title'],
                       1 if 'incl_link' in request.form else 0,
                       request.form['body'])
    return redirect(url_for("admin.edit_page", page_id=page_id))


@admin.route('/tomarkdown', methods=['POST'])
@login_required
def to_markdown():
    """Given some body text in Markdown, return valid HTML."""
    body = request.data.decode('utf8')
    return util.mkdown(body)


@admin.route('/now')
def current_date():
    """Returns a properly formatted date for now."""
    return database.date_to_str(datetime.datetime.today().timestamp())
