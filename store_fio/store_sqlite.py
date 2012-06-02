#!/usr/bin/env python
# -*- coding: utf-8 -*-
# script to save new payments to sqlite database

import sys
import urllib
import lxml.html

import sqlite3 as lite
import datetime
import unicodedata

import fio

#account overview URL
url = 'https://www.fio.cz/scgi-bin/hermes/dz-transparent.cgi?pohyby_DAT_od=01.01.2011&ID_ucet=2900086515'

db_file='members.db'

def rm_dia(text):
    """Removes diacritic signs from the string $text"""

    if sys.hexversion >= 0x3000000:
        # On Python >= 3.0.0
        return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode()
    else:
        # On Python < 3.0.0
        return unicodedata.normalize('NFKD', unicode(text)).encode('ASCII', 'ignore')


class MembersDB:
    def __init__(self):
        self.con = lite.connect('members.db', detect_types=lite.PARSE_DECLTYPES)
        self.con.row_factory = lite.Row
        self.cur = self.con.cursor()

    def get_member(self, member_id):
        """Fetch member record"""

        self.cur.execute("SELECT * FROM Members WHERE id=?;", [member_id])
        return self.cur.fetchone()

    def detect_member(self, payment):
        """
        Detect member_id from payment $p using:
            1) VS field of payment
            2) Identification field of payment
                (compares the name with the names in Members DB table)

        Returns member record in DB or None
        """
        member=None
        member_id=None

        # check if there is something in VS field and is usable?
        try:
            member_id = int(payment.vs)
        except ValueError as e:
            pass

        if member_id:
            member = self.get_member(member_id)

        # use some heuristics, such as detecting memberID from 'identification'
        if payment.identification.strip():
            self.cur.execute('SELECT id, name FROM members')
            members = self.cur.fetchall()
            # create list of member names, lowercased, without diacritic
            splnames = map(
                    lambda x: (x['id'], rm_dia(x['name']).lower().split(' ')),
                    members)

 
            # 'Fér   Radek' -> ['fer', 'radek']
            name = filter(None, rm_dia(payment.identification).lower().split(' '))

            # compare names of members and the name for current payment,
            # filter out matching member records.
            # try both possibilities: radek fer and fer radek
            tmp=filter(
                    lambda x: (name[0] in x[1]) and (name[1] in x[1]),
                    splnames)

            if tmp:
                if len(tmp) == 1:
                    # unique match with somebody's name from members table
                    return self.get_member(tmp[0][0])

        return member



    def add_payment(self, payment):
        member = self.detect_member(payment)

        if member:
            print('new payment from %s' % member['nick'])
            payment.member_id = member['id']
        else:
            print('new payment (%s)'% payment.arrival)

        # - create new record in Payments
        command  = "INSERT INTO Payments("
        command += ", ".join(payment.keys())
        command += ") VALUES("
        command += ", ".join('?'*len(payment))
        command += ");"

        self.cur.execute(command, payment.values())

    def update(self):
        """ Perform update from source (Fio webpages). """

        #open DB for storing payments
        #fetch will return dictionary rather then a tuple

        new_count=0

        for payment in fio.scrape(url):
            self.cur.execute("SELECT * FROM Payments "
                    "WHERE arrival=? "
                    "AND identification=? "
                    "AND message=?;", (
                        payment.arrival,
                        payment.identification, payment.message))

            if self.cur.fetchone():
                # there is already this payment in DB, skip it
                pass
            else:
                # this is new payment, not yet in DB, insert it
                self.add_payment(payment)
                new_count += 1

        self.cur.execute("INSERT INTO UpdateHistory VALUES(datetime())")
        self.con.commit()

        print("Update complete (%d new payments)"%new_count)

if __name__ == "__main__":
    db = MembersDB()
    db.update()
