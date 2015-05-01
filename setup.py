"""cjblog :: setup.py

Author: Christopher Rink (chrisrink10 at gmail dot com)"""
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='cjblog',
    version='0.1',
    packages=['cjblog'],
    url='http://github.com/chrisrink10/cjblog',
    license='MIT License',
    author='Christopher Rink',
    author_email='chrisrink10@gmail.com',
    description='A small personal blog written with Flask and SQLAlchemy',
    install_requires=[
        'Flask>=0.10.1',
        'bcrypt>=1.1.1',
        'python-dateutil>=2.2',
        'Markdown>=2.4',
        'Pygments>=1.6',
        'SQLAlchemy>=0.9.4'
    ],
    include_package_data=True,
    scripts=['bin/setup-blog'],
    package_data={
        'static': 'cjblog/static/*',
        'templates': 'cjblog/templates/*'
    },
)
