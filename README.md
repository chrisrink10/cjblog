cjblog
===

This is my home-built blog and home page. It is written using Python, Flask,
SQLAlchemy, and a few other smaller packages.

## Getting Started
Sorry I haven't built an install script because I don't often have to
reinstall this software. You can get it up and running by following these
steps:
1. Create a SQLite3 database using the SQL script make_database.sql.
2. Generate a secret key using Python's ```os.urandom(32)``` and fill that
in in the appropriate section of config.ini. Fill in the name of the database
file you created in the previous step.
3. Run the function ```util.compile_configuration(data)``` from the Python
console.
4. If you want, create a virtual environment for your blog. Install the
requirements listed in requirements.txt.
5. Magic!
