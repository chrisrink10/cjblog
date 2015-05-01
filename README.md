cjblog
===

This is my home-built blog and home page. It is written using Python, Flask,
SQLAlchemy, and a few other smaller packages.

## Getting Started
You can easily install this blog following these steps. The steps assume
you are using some sort of UNIX-like operating system and that you have
set up uWSGI and nginx to your liking.

1.  Create your directory:
    `sudo mkdir /var/www/mysite`
2.  Create a new virtual environment within that directory: 
    `sudo pyvenv /var/www/mysite/venv`
3.  Activate your virtual environment: 
    `source /var/www/mysite/venv/bin/activate`
3.  Install the `cjblog` software: 
    `pip install git+git://github.com/chrisrink10/cjblog.git@master`
4.  Create your new database, user, and generate configuration:
    `setup-blog -d /var/www/mysite -n blog.db --create-database -u admin --gen-config --install`
5.  Follow any steps from the script as they arise.
6.  Create a new uWSGI configuration file (
    `sudo nano /etc/uwsgi/apps-available/mysite.ini`) with the following text:

        ```
        [uwsgi]
        # Variables
        base = /var/www/mysite
        callable = app
        module = main
        
        # Generic configuration
        home = %(base)/venv
        pythonpath = %(base)
        socket = /var/www/run/%n.sock
        module = %(module)
        logto = /var/log/uwsgi/%n.log
        ```
   
7.  Enable your uWSGI app: 
    `sudo ln -s /etc/uwsgi/apps-available/mysite.ini /etc/uwsgi/apps-enabled/mysite.ini`
8.  Reset the uWSGI workers: 
    `sudo touch /etc/uwsgi/apps-available/mysite.ini`
9.  Go to your site! You can login by going to the route `{root}/login`.

## License
MIT License