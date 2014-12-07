"""cjblog :: database module

Performs all of the database manipulation for cjrink.com.

Author: Christopher Rink (chrisrink10 at gmail dot com)"""
from datetime import date
from math import ceil
import re

import bcrypt
from flask import current_app
from dateutil import parser
from sqlalchemy import (create_engine,
                        Table,
                        Column,
                        Integer,
                        String,
                        Index,
                        MetaData,
                        ForeignKey,
                        select,
                        func,
                        bindparam,
                        null)

import config
import util


# Configure SQLAlchemy
engine = create_engine(config.DATABASE, echo=config.DEBUG)
metadata = MetaData()

# Table configuration
users = Table('users', metadata,
              Column('id', Integer, primary_key=True),
              Column('username', String),
              Column('password', String)
)

articles = Table('articles', metadata,
                 Column('id', Integer, primary_key=True),
                 Column('released', Integer),
                 Column('title_path', String),
                 Column('title', String),
                 Column('title_link', String),
                 Column('title_alt', String),
                 Column('date', Integer),
                 Column('body', String)
)
Index('released', articles.c.released)
Index('title_path', articles.c.title_path)
Index('article_date', articles.c.date)

pages = Table('pages', metadata,
              Column('id', Integer, primary_key=True),
              Column('released', Integer),
              Column('pg_order', Integer),
              Column('title_path', String),
              Column('title', String),
              Column('create_date', Integer),
              Column('edit_date', Integer),
              Column('incl_link', Integer),
              Column('body', String)
)
Index('page_released', pages.c.released)
Index('page_link', pages.c.incl_link)
Index('page_order', pages.c.pg_order)
Index('page_title', pages.c.title_path)

tags = Table('tags', metadata,
             Column('id', Integer, primary_key=True),
             Column('tag', String)
)

tag_map = Table('tag_map', metadata,
                Column('tag_id', Integer, ForeignKey('tags.id')),
                Column('article_id', Integer, ForeignKey('articles.id'))
)

sessions = Table('sessions', metadata,
                 Column('key', String, primary_key=True),
                 Column('user', Integer, ForeignKey('users.id')),
                 Column('change', Integer)
)

links = Table('links', metadata,
              Column('id', Integer, primary_key=True),
              Column('article_id', Integer, ForeignKey('articles.id')),
              Column('link', String),
              Column('link_text', String),
              Column('link_alt', String)
)

configuration = Table('configuration', metadata,
                      Column('id', Integer, primary_key=True),
                      Column('key_name', String),
                      Column('value', String),
                      Column('default', String))
Index('config_key', configuration.c.key_name)


def date_to_str(timestamp):
    """Return a date string in a consistent format from a UNIX timestamp."""
    if timestamp is None:
        return ""
    dt = date.fromtimestamp(int(timestamp))
    dt_str = dt.strftime("%B {d.day}, %Y")
    return dt_str.format(d=dt) or ""


def safe_date(article_date):
    """Return a UNIX timestamp for the given date string."""
    timestamp = parser.parse(article_date).timestamp()
    return timestamp


def url_safe_string(string):
    """Returns a URL safe string."""
    whitespace = re.compile('[\s]+', flags=re.ASCII)
    pattern = re.compile('[^a-zA-Z0-9_-]+', flags=re.ASCII)
    safe_str = whitespace.sub('-', string.lower().strip())
    safe_str = pattern.sub('', safe_str)
    return safe_str


def tags_as_list(tag_names):
    """Accept a string of tags delimited by a comma and return a list."""
    if not isinstance(tag_names, str):
        return ()
    tag_names = tag_names.split(",") if len(tag_names) > 0 else ()
    return tuple(tag.strip() for tag in tag_names)


def get_render_func(render=True):
    """Return a function which evaluates whether rendering needs to occur."""
    if render:
        return lambda val: util.mkdown(val)
    else:
        return lambda val: val


def check_login(username, password):
    """Check a username and password combination."""
    stmt = select([users.c.password]).where(users.c.username == username)
    conn = engine.connect()
    result = conn.execute(stmt)
    row = result.fetchone()

    if row is not None:
        if bcrypt.hashpw(password, row[0]) == row[0]:
            result = True

    return result


############################
# SESSION FUNCTIONS
############################


def check_session(username, key):
    """Check a username and key session data combination."""
    stmt = select([
        users.c.username,
        func.sum(
            func.strftime('%s', 'now') - sessions.c.change
        ).label("last_check")
    ]).select_from(
        sessions.join(users, users.c.id == sessions.c.user)
    ).where(
        sessions.c.key == key
    )

    conn = engine.connect()
    result = conn.execute(stmt)
    row = result.fetchone()
    conn.close()

    if row is None or username != row['username']:
        return False, False

    if row['last_check'] > config.SESSION_EXPIRE:
        destroy_session(username, key)
        return True, False

    update_session(username, key)
    return True, True


def create_session(username, key):
    """Create a new session in the database."""
    stmt = sessions.insert().values(
        key=key,
        user=select([users.c.id]).where(users.c.username == username),
        change=func.strftime('%s', 'now')
    )
    conn = engine.connect()
    conn.execute(stmt)
    conn.close()


def destroy_session(username, key):
    """Destroy the given session."""
    seluser = select([users.c.id]).where(
        users.c.username == username
    )
    stmt = sessions.delete().where(
        sessions.c.key == key
    ).where(
        sessions.c.user == seluser
    )
    conn = engine.connect()
    conn.execute(stmt)
    conn.close()


def update_session(username, key):
    """Update a user's last session check time in the database."""
    seluser = select([users.c.id]).where(
        users.c.username == username
    )
    stmt = sessions.update().values(
        change=func.strftime('%s', 'now')
    ).where(sessions.c.key == key).where(sessions.c.user == seluser)

    conn = engine.connect()
    conn.execute(stmt)
    conn.close()


############################
# ARTICLE FUNCTIONS
############################


def article_from_row(row, render=True):
    """Given a SQLite row, create an dictionary for an article."""
    article = {
        'id': '',
        'released': bool,
        'title_path': '',
        'title': '',
        'title_link': '',
        'title_alt': '',
        'date': date_to_str,
        'tag_list': tags_as_list,
        'body': get_render_func(render)
    }

    for key, val in article.copy().items():
        if key in row.keys():
            article[key] = val(row[key]) if callable(val) else row[key]
            article[key] = '' if article[key] is None else article[key]
        else:
            article[key] = ''

    return article


def create_article(title, title_link, title_alt, article_date,
                   body, released, tag_list=None):
    """Save an article to the database."""
    args = {
        'released': released,
        'title_path': url_safe_string(title),
        'title': title,
        'link': title_link,
        'alt': title_alt,
        'date': safe_date(article_date),
        'body': body
    }

    conn = engine.connect()
    stmt = articles.insert()
    result = conn.execute(stmt, args)
    save_tags(result, tag_list)

    return result.inserted_primary_key[0]


def delete_article(article_id):
    """Delete an article by it's ID."""
    stmt = articles.delete().where(articles.c.id == article_id)
    conn = engine.connect()
    conn.execute(stmt)
    conn.close()


def get_article(article_id=None, title_path=None, render=True, released=None):
    """Return an article by it's ID."""
    if article_id is None and title_path is None:
        raise ValueError("You must specify either an ID or path.")

    # Generate the proper where condition
    if article_id is not None:
        where_cond = (articles.c.id == article_id)
    else:
        where_cond = (articles.c.title_path == title_path)

    # Generate the SQL syntax with SQLAlchemy
    stmt = select(
        [articles,
         func.ifnull(func.group_concat(tags.c.tag, ", "), "").label('tag_list')]
    ).select_from(
        articles.outerjoin(
            tag_map,
            articles.c.id == tag_map.c.article_id
        ).outerjoin(
            tags,
            tag_map.c.tag_id == tags.c.id
        )
    ).where(
        where_cond
    ).where(
        articles.c.released == released if released is not None else ""
    ).group_by(
        tag_map.c.article_id
    )

    # Get our results
    conn = engine.connect()
    result = conn.execute(stmt)
    row = result.fetchone()
    article = article_from_row(row, render=render) if row is not None else None
    conn.close()
    return article


def get_articles(start=None, page_size=config.PAGE_SIZE, with_body=True,
                 with_links=False, released=False, render=True,
                 tag=None, tag_list=False):
    """Return a list of articles."""
    by_tag = True if isinstance(tag, str) else False
    # Generate the correct list of columns
    cols = [articles.c.id,
            articles.c.released,
            articles.c.title_path,
            articles.c.title,
            articles.c.date]

    if with_body:
        cols.append(articles.c.body)
    if with_links:
        cols.append(articles.c.title_link)
        cols.append(articles.c.title_alt)
    if tag_list and not by_tag:
        cols.append(
            func.ifnull(
                func.group_concat(tags.c.tag, ", "),
                ""
            ).label('tag_list')
        )

    # Build the statement
    stmt = select(cols, offset=start, limit=page_size).where(
        articles.c.released == released if released is not None else ""
    ).order_by(
        articles.c.date.desc()
    )

    # Join the tag map and tag table if either:
    # - we want to return tags
    # - we are returning all articles with a certain tag
    if by_tag or tag_list:
        stmt = stmt.select_from(
            articles.outerjoin(
                tag_map,
                articles.c.id == tag_map.c.article_id
            ).outerjoin(
                tags,
                tag_map.c.tag_id == tags.c.id
            )
        )

    # Limit by tag only if we are returning all articles with a certain tag
    if by_tag and not tag_list:
        stmt = stmt.where(
            tags.c.tag == tag
        )

    # Execute the statement
    article_list = []
    conn = engine.connect()
    for row in conn.execute(stmt):
        article = article_from_row(row, render=render)
        article_list.append(article)

    conn.close()
    return article_list


def get_num_articles(page_size=config.PAGE_SIZE, released=True, tag=None):
    """Return the number of articles and the number of pages using the
    given page size (rounding up)."""
    stmt = select([func.count(articles.c.id).label("num_articles")]).where(
        articles.c.released == released if released is not None else ""
    )

    # Check against a given tag
    if tag is not None:
        stmt = stmt.select_from(
            articles.outerjoin(
                tag_map,
                articles.c.id == tag_map.c.article_id
            ).outerjoin(
                tags,
                tag_map.c.tag_id == tags.c.id
            )
        ).where(
            tags.c.tag == tag
        )

    # Get the connection
    conn = engine.connect()
    result = conn.execute(stmt)
    row = result.fetchone()
    conn.close()

    pagination = (row['num_articles'],
                  ceil(int(row['num_articles']) / page_size))
    current_app.logger.debug("Pagination is: {}".format(pagination))

    return pagination


def save_article(article_id, title, title_link, title_alt,
                 article_date, body, released, tag_list=None):
    """Updates an existing article."""
    args = {
        'title_path': url_safe_string(title),
        'title': title,
        'title_link': title_link,
        'title_alt': title_alt,
        'date': safe_date(article_date),
        'body': body,
        'released': released
    }

    stmt = articles.update().where(articles.c.id == article_id)
    conn = engine.connect()
    conn.execute(stmt, args)
    save_tags(article_id, tag_list)


############################
# PAGE FUNCTIONS
############################


def page_from_row(row, render=True):
    """Given a SQLite row, create an dictionary for an article."""
    page = {
        'id': '',
        'pg_order': '',
        'released': bool,
        'title_path': '',
        'title': '',
        'create_date': date_to_str,
        'edit_date': date_to_str,
        'incl_link': '',
        'body': get_render_func(render)
    }

    for key, val in page.copy().items():
        if key in row.keys():
            page[key] = val(row[key]) if callable(val) else row[key]
            page[key] = '' if page[key] is None else page[key]
        else:
            page[key] = ''

    return page


def create_page(released, pg_order, title, incl_link, body):
    """Save a new page to the database."""
    stmt = pages.insert().values(
        released=released,
        pg_order=pg_order,
        title_path=url_safe_string(title),
        title=title,
        create_date=func.strftime("%s", "now"),
        incl_link=incl_link,
        body=body
    )
    conn = engine.connect()
    result = conn.execute(stmt)

    return result.inserted_primary_key[0]


def delete_page(page_id):
    """Delete a page by its ID."""
    stmt = pages.delete().where(pages.c.id == page_id)
    conn = engine.connect()
    conn.execute(stmt)
    conn.close()


def get_page(page_id=None, title_path=None, render=True, released=None):
    """Return a page by it's ID or title-path."""
    if page_id is None and title_path is None:
        raise ValueError("You must specify either an ID or path.")

    # Generate the proper where condition
    if page_id is not None:
        where_cond = (pages.c.id == page_id)
    else:
        where_cond = (pages.c.title_path == title_path)

    # Generate the SQL syntax with SQLAlchemy
    stmt = select([pages]).where(
        where_cond
    ).where(
        pages.c.released == released if released is not None else ""
    )

    # Get our results
    conn = engine.connect()
    result = conn.execute(stmt)
    row = result.fetchone()
    page = page_from_row(row, render=render) if row is not None else None
    conn.close()
    return page


def get_pages(released=None, render=True, with_body=True, only_links=True):
    """Return all pages."""
    page_list = []

    # Generate the column list
    cols = [
        pages.c.id,
        pages.c.released,
        pages.c.pg_order,
        pages.c.title_path,
        pages.c.title,
        pages.c.create_date,
        pages.c.edit_date]

    # Include the body
    if with_body:
        cols.append(pages.c.body)

    # Generate the SQL syntax with SQLAlchemy
    stmt = select(cols).order_by(
        pages.c.pg_order.asc()
    )

    # Check for released pages if requested
    if released is not None:
        stmt = stmt.where(
            (pages.c.released == released)
        )

    # Only return pages which are supposed to be top links
    if only_links:
        stmt = stmt.where(
            (pages.c.incl_link == only_links)
        )

    # Get our results
    conn = engine.connect()
    for row in conn.execute(stmt):
        page = page_from_row(row, render=render)
        page_list.append(page)
    conn.close()
    return page_list


def save_page(page_id, released, pg_order, title, incl_link, body):
    """Updates an existing page."""
    stmt = pages.update().values(
        released=released,
        pg_order=pg_order,
        title_path=url_safe_string(title),
        title=title,
        edit_date=func.strftime('%s', 'now'),
        incl_link=incl_link,
        body=body
    ).where(pages.c.id == page_id)
    conn = engine.connect()
    conn.execute(stmt)


############################
# TAG FUNCTIONS
############################

def save_tags(article_id, tag_names=None):
    """Saves the tags associated with an article to the database."""
    # Get tags in the correct format
    if isinstance(tag_names, str):
        tag_names = tag_names.split(",")
        tag_names = tuple(tag.strip() for tag in tag_names if tag != "")
    if not isinstance(tag_names, (list, tuple, type(None))):
        try:
            tag_names = tuple(tag_names)
            tag_names = tuple(tag for tag in tag_names if tag != "")
        except TypeError:
            current_app.logger.error("Could not convert tags to Tuple.")
            return
    current_app.logger.debug("Tags given: {}".format(tag_names))

    conn = engine.connect()

    # Remove all current tags for the given article
    delstmt = tag_map.delete().where(tag_map.c.article_id == article_id)
    conn.execute(delstmt)

    # If tags is None, we just wanted to delete current tag associations
    if tag_names is None or len(tag_names) == 0:
        conn.close()
        return

    # Insert any new tags which didn't exist before
    insstmt = tags.insert().prefix_with("OR IGNORE")
    conn.execute(insstmt, [{'tag': tag} for tag in tag_names])

    # Now attach the tags to the articles using the map table
    selstmt = select([tags.c.id]).where(tags.c.tag == bindparam("tag_name"))
    mapstmt = tag_map.insert({'tag_id': selstmt})
    conn.execute(mapstmt,
                 [{'tag_name': tag,
                   'article_id': article_id} for tag in tag_names])


def get_all_tags(released=True):
    """Return a list of all tags ordered by popularity."""
    stmt = select([tags.c.tag]).select_from(
        tags.outerjoin(
            tag_map, tags.c.id == tag_map.c.tag_id
        ).outerjoin(
            articles, tag_map.c.article_id == articles.c.id
        )
    ).where(
        articles.c.released == released
    ).group_by(
        tags.c.id
    ).order_by(
        func.count(tags.c.id).desc()
    )

    conn = engine.connect()
    tag_list = []
    for row in conn.execute(stmt):
        tag_list.append(row['tag'])

    conn.close()
    return tag_list


############################
# SIDEBAR LINK FUNCTIONS
############################

def add_sidebar_link(article_id=None, external_link=None,
                     link_text=None, link_alt=None):
    """Add a new sidebar link."""
    has_neither = ((article_id is None or article_id == '') and
                   (external_link is None or external_link == ''))
    has_both = ((article_id is not None and article_id != '') and
                (external_link is not None and external_link != ''))
    if has_neither:
        raise ValueError("Please specify either an article or external link.")
    if has_both:
        raise ValueError("Please specify only an article or external link.")

    args = {
        'article_id': article_id if not external_link else '',
        'link': external_link if not article_id else '',
        'link_text': link_text,
        'link_alt': link_alt
    }
    stmt = links.insert()
    conn = engine.connect()
    result = conn.execute(stmt, args)
    conn.close()

    return result.inserted_primary_key[0]


def delete_sidebar_link(link_id):
    """Delete a sidebar link by it's ID."""
    stmt = links.delete().where(links.c.id == link_id)
    conn = engine.connect()
    conn.execute(stmt)
    conn.close()


def get_sidebar_links():
    """Return a list of sidebar links."""
    stmt = select([links, articles.c.title]).select_from(
        links.outerjoin(articles, links.c.article_id == articles.c.id)
    )
    conn = engine.connect()
    result = conn.execute(stmt)
    sidebar_links = []
    for row in result:
        link = {
            'link_id': row['id'],
            'article_id': row['article_id'],
            'article_title': row['title'],
            'external_link': row['link'],
            'link_text': row['link_text'],
            'link_alt': row['link_alt']
        }
        sidebar_links.append(link)

    conn.close()
    return sidebar_links


############################
# MAINTENANCE FUNCTIONS
############################

def prune_tags():
    """Remove any unused tags."""
    stmt = tags.delete().where(
        tags.c.id.in_(
            select([tags.c.id]).select_from(
                tags.outerjoin(tag_map, tags.c.id == tag_map.c.tag_id)
            ).where(
                tag_map.c.article_id == null()
            )
        )
    )
    conn = engine.connect()
    conn.execute(stmt)
    conn.close()


def prune_sessions():
    """Remove any old sessions from the database."""
    stmt = sessions.delete().where(
        func.sum(
            func.strftime('%s', 'now') - sessions.change
        ) == config.SESSION_PRUNE_AGE
    )
    conn = engine.connect()
    conn.execute(stmt)
    conn.close()


############################
# CONFIGURATION FUNCTIONS
############################

def save_config(data):
    """Save configuration options to the database and compile the
    Python config file."""
    zipped = [{'key': k, 'val': v} for k, v in data.items()]
    util.compile_configuration(data)

    stmt = configuration.update().where(
        configuration.c.key_name == bindparam('key')
    ).values(
        value=bindparam('val')
    )

    conn = engine.connect()
    conn.execute(stmt, zipped)
    conn.close()


def load_config():
    """Load the configuration from the database."""
    stmt = select(
        [configuration.c.key_name,
         configuration.c.value,
         configuration.c.default]
    )

    conn = engine.connect()
    result = conn.execute(stmt)
    data = {}
    for row in result:
        val = row['value']
        data[row['key_name']] = val if val is not None else row['default']

    conn.close()
    return data
