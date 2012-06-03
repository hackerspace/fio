#!/usr/bin/env python
# push data from sqlite database to django site

from datetime import date

from django.contrib.auth.models import User

from payments.models import Payment

import sqlite3

db_file='../members.db'

con = sqlite3.connect(db_file)
cur = con.cursor()
q = cur.execute('select * from members')
ms = q.fetchall()
q = cur.execute('select * from payments')
ps = q.fetchall()

pid_map = {}

for m in ms:
    u = User(username='_' + m[1],
        first_name=m[2].split()[0],
        last_name=m[2].split()[1],
        password='',
        date_joined=date(*map(int, m[3].split('-')))
        )
    u.save()

    p = u.get_profile()
    p.payments_id = int(m[0])
    p.accepted = True
    p.save()

    pid_map[int(m[0])] = u

def fix(inp):
    if inp==u'': return 0
    return int(inp)

def fixfloat(inp):
    if type(inp) == float:
        return inp
    return float(inp)

for p in ps:
    user = None
    if fix(p[5]) in pid_map:
        user = pid_map[fix(p[5])]

    p = Payment(
        date=date(*map(int, p[1].split('-'))),
        amount=fixfloat(p[2]),
        payment_type=p[3],
        constant_symbol=fix(p[4]),
        variable_symbol=fix(p[5]),
        specific_symbol=fix(p[6]),
        identification=p[7],
        message=p[8],
        user=user)
    p.save()
