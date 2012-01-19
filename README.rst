Fio scraper
===========
Mirror and backup our bank transactions and provide DB for payment analyzing.

Note: Use Python2 or rewrite the parts with lxml and urllib.

This app should be periodically run to check for new membership payments from
our Fio bank transparent account website [1].
When started, it compares records from the output of this CGI script with
what is stored in local DB (file "members.db", SQLite3, see also "schema.sql")
and adds any new records. This is because the Fio bank account website shows
only the last N payments.

When comparing records from the website with DB records, fields
arrival, identification and message are used.

Later, DB records could be directly used for membership accounting and access
granting (somehow).


For regenerating DB, I use:
    1) sqlite3 -init schema.sql members.db
    2) ./insert_users.py
    3) ./scrape.py

User addition and management will be in the webapp.

[1] https://www.fio.cz/scgi-bin/hermes/dz-transparent.cgi?ID_ucet=2900086515
