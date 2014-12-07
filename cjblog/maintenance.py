"""cjblog :: maintenance module

Performs database maintenance functions.

Author: Christopher Rink (chrisrink10 at gmail dot com)"""
import database


if __name__ == "__main__":
    database.prune_tags()
    database.prune_sessions()
