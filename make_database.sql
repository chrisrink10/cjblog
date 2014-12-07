/*
 * cjblog :: make_database script
 *
 * This script would create a valid schema for a SQLite database.
 *
 * Author: Christopher Rink (chrisrink10 at gmail dot com)
 */
CREATE TABLE IF NOT EXISTS users (
    id        INTEGER PRIMARY KEY,
    username  TEXT,
    password  TEXT
);

CREATE TABLE IF NOT EXISTS articles (
    id          INTEGER PRIMARY KEY,
    released    INTEGER,
    title_path  TEXT,
    title       TEXT,
    title_link  TEXT,
    title_alt   TEXT,
    date        INTEGER,
    body        TEXT
);

CREATE INDEX released ON articles (released);
CREATE INDEX title_path ON articles (title_path);
CREATE INDEX article_date ON articles (date);

CREATE TABLE IF NOT EXISTS pages (
    id          INTEGER PRIMARY KEY,
    released    INTEGER,
    pg_order    INTEGER,
    title_path  TEXT,
    title       TEXT,
    create_date INTEGER,
    edit_date   INTEGER,
    incl_link   INTEGER,
    body        TEXT
);

CREATE INDEX page_released ON pages (released);
CREATE INDEX page_link ON pages (incl_link);
CREATE INDEX page_order ON pages (pg_order);
CREATE INDEX page_title ON pages (title_path);

CREATE TABLE IF NOT EXISTS tags (
    id  INTEGER PRIMARY KEY,
    tag TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS tag_map (
    tag_id INTEGER,
    article_id INTEGER,
    FOREIGN KEY(tag_id) REFERENCES tags(id),
    FOREIGN KEY(article_id) REFERENCES articles(id)
);

CREATE TABLE IF NOT EXISTS sessions (
    key     TEXT PRIMARY KEY,
    user    INTEGER,
    change  INTEGER,
    FOREIGN KEY(user) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS links (
    id          INTEGER PRIMARY KEY,
    article_id  INTEGER,
    link        TEXT,
    link_text   TEXT,
    link_alt    TEXT,
    FOREIGN KEY(article_id) REFERENCES articles(id)
);

CREATE TABLE IF NOT EXISTS configuration (
    id        INTEGER PRIMARY KEY,
    key_name  TEXT,
    value     TEXT,
    `default`   TEXT
);

CREATE INDEX config_key ON configuration (key_name);

INSERT INTO configuration (key_name, value, `default`) VALUES
    ('main_title', '', 'my new blog'),
    ('subtitle', '', 'has a subtitle'),
    ('browser_title', '', 'My New Blog'),
    ('footer_text', '', '&copy; My New Blog'),
    ('image_location', '', '#'),
    ('image_alt', '', 'My New Blog image'),
    ('about_blurb', '', 'Check out my cool new blog!'),
    ('page_size', '', '5'),
    ('session_expire', '', '1800'),
    ('session_prune_age', '', '3600');