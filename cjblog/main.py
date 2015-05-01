"""cjblog :: main module

Renders most of the pages of cjrink.com.

Author: Christopher Rink (chrisrink10 at gmail dot com)"""
import logging
import os

from flask import (Flask,
                   render_template,
                   request,
                   session,
                   redirect,
                   url_for,
                   abort,
                   Markup)

from cjblog.admin import admin
import cjblog.config as config
import cjblog.database as database


# Set up Flask
app = Flask(__name__,
            static_folder=os.path.join(config.APP_ROOT, 'static'),
            template_folder=os.path.join(config.APP_ROOT, 'templates'))

# For debugging, we'll leave these on
if config.DEBUG:
    app.debug = True
    app.logger.setLevel(logging.DEBUG)
    app.config['PROPAGATE_EXCEPTIONS'] = True

# Jinja2 template configuration
app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True


def paginate(page_num, by_tag=None):
    """Return start and page_size values"""
    if not isinstance(page_num, int):
        abort(404)
    page_num = page_num if page_num > 0 else 1

    # Return the number of articles and expected number of pages
    num_articles, pages = database.get_num_articles(released=True,
                                                    tag=by_tag)

    # Figure out which article starts the page
    start = config.PAGE_SIZE * (page_num - 1)
    if start > num_articles:
        start = num_articles % pages

    return start, pages


def check_logged_in():
    """Checks whether the user has a valid session."""
    if 'username' not in session or 'key' not in session:
        app.logger.debug("Could not find 'username' or 'key'.")
        session.clear()
        return False

    # Check whether session values are either expired or invalid
    valid, current = database.check_session(session['username'],
                                            session['key'])
    if not valid or not current:
        app.logger.debug("Invalid or outdated session.")
        session.clear()
        return False

    return True


@app.route('/', defaults={'page_num': 1})
@app.route('/<int:page_num>')
def home(page_num):
    """Renders the home page."""
    start, pages = paginate(page_num)
    articles = database.get_articles(start=start,
                                     with_body=True,
                                     with_links=True,
                                     released=True,
                                     tag_list=True)
    return render_template("article.html",
                           page_title="Home",
                           articles=articles,
                           pages=pages,
                           show_tags=True)


@app.route('/page/<int:page_id>', defaults={'page_title': None})
@app.route('/page/<page_title>', defaults={'page_id': None})
def show_page(page_id, page_title):
    """Shows an individual article."""
    page = database.get_page(page_id=page_id,
                             title_path=page_title,
                             render=True,
                             released=True)

    # Check if that article exists
    if page is None:
        abort(404)

    return render_template("page.html",
                           page=page,
                           show_tags=True)


@app.route('/post/<int:article_id>', defaults={'title_path': None})
@app.route('/post/<title_path>', defaults={'article_id': None})
def show_article(article_id, title_path):
    """Shows an individual article."""
    article = database.get_article(article_id=article_id,
                                   title_path=title_path,
                                   render=True,
                                   released=True)

    # Check if that article exists
    if article is None:
        abort(404)

    return render_template("article.html",
                           page_title=article["title"],
                           articles=[article],
                           show_tags=True)


@app.route('/tag/<tag_name>', defaults={'page_num': 1})
@app.route('/tag/<tag_name>/<int:page_num>')
def articles_by_tag(tag_name, page_num):
    """Display a list of articles by the tag name."""
    if tag_name is None:
        return redirect(url_for("home"))
    start, pages = paginate(page_num, by_tag=tag_name)
    articles = database.get_articles(start=start,
                                     with_body=True,
                                     with_links=True,
                                     released=True,
                                     tag=tag_name,
                                     tag_list=True)
    return render_template("article.html",
                           page_title="Tag: {}".format(tag_name),
                           articles=articles,
                           pages=pages,
                           show_tags=True)


@app.route('/articles')
def article_list():
    """Renders the article list."""
    articles = database.get_articles(with_links=False,
                                     with_body=False,
                                     released=True)
    tags = database.get_all_tags(released=True)
    return render_template("list.html",
                           articles=articles,
                           tags=tags)


@app.route('/login',
           methods=['GET'],
           defaults={'error': None})
def login(error):
    """Renders the login page."""
    # Redirect to admin home where these will be checked for validity
    if 'username' in session and 'key' in session:
        return redirect(url_for('admin.home'))
    if request.args.get('expired'):
        error = "Your session has expired. Please log in again."
    return render_template("login.html", error=error)


@app.route('/login', methods=['POST'])
def log_me_in():
    """Perform the actual login process and redirect to the appropriate page."""
    if database.check_login(request.form['username'], request.form['password']):
        session['username'] = request.form['username']
        session['key'] = os.urandom(32)
        database.create_session(session['username'], session['key'])
        return redirect(url_for('admin.home'))
    else:
        error = "Please enter a valid username and password."
        return render_template("login.html", error=error)


@app.route('/logout')
def logout():
    """Destroys the user's session and redirects to the login page."""
    if 'username' in session and 'key' in session:
        database.destroy_session(session['username'], session['key'])
    session.clear()
    return render_template("login.html")


@app.errorhandler(400)
def bad_request(e):
    """Renders a 400 Bad Request error message."""
    app.logger.error(e)
    return render_template("400.html"), 400


@app.errorhandler(403)
def forbidden(e):
    """Renders a 403 Forbidden error message."""
    app.logger.error(e)
    return render_template("403.html"), 403


@app.errorhandler(404)
def page_not_found(e):
    """Renders a 404 Page Not Found error message."""
    app.logger.error(e)
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    """Renders a 500 Internal Server Error error message."""
    app.logger.error(e)
    return render_template("500.html"), 500


@app.route('/js/<path:path>')
def js_file(path):
    """Returns the requested JavaScript resource."""
    return app.send_static_file(os.path.join('js', path))


@app.route('/css/<path:path>')
def css_file(path):
    """Returns the requested CSS resource."""
    return app.send_static_file(os.path.join('css', path))


@app.route('/img/<path:path>')
def img_file(path):
    """Returns the requested Image resource."""
    return app.send_static_file(os.path.join('img', path))


@app.context_processor
def jinja_context():
    """Make functions and common variables available to the Jinja2
    templating engine."""
    def sel(*args):
        """Return the first argument which returns True."""
        for arg in args:
            if arg:
                return arg

    return dict(
        sel=sel,
        admin=check_logged_in(),
        page_list=database.get_pages(released=True,
                                     render=False,
                                     with_body=False,
                                     only_links=True),
        header_title=Markup.escape(config.MAIN_TITLE),
        header_subtitle=Markup.escape(config.SUBTITLE),
        browser_title=Markup.escape(config.BROWSER_TITLE),
        footer_text=Markup(config.FOOTER_TEXT),
        sidebar_image=Markup.escape(config.IMAGE_LOCATION),
        sidebar_image_alt=Markup.escape(config.IMAGE_ALT)
    )


# This is used for sessions
app.secret_key = config.SECRET_KEY


# Register any additional Blueprints
app.register_blueprint(admin)


if __name__ == '__main__':
    app.run(debug=config.DEBUG)
