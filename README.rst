Fio scraper
===========

Requirements:
--------------
 - python >= 2.7
 - pysqlite >= 2.6.3
 - python-fio >= 0.1

Mirror and backup our bank transactions and provide DB for payment analysis.

Provided apps:
--------------

store_sqlite.py
~~~~~~~~~~~~~~~

This app should be periodically run to check for new membership payments from
our Fio bank transparent account website [1].
When started, it compares records from the output of this CGI script with
what is stored in local DB (file "members.db", SQLite3, see also "schema.sql")
and adds any new records. This is because the Fio bank account website shows
only the last N payments.
