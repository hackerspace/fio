#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#Simple web scraper for Fio bank public accounts

import sys
import urllib
import lxml.html

import sqlite3 as lite
import datetime
import unicodedata

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

    def detect_member(self, p):
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
            member_id = int(p['VS'])
        except ValueError as e:
            pass

        if member_id:
            member = self.get_member(member_id)

        # use some heuristics, such as detecting memberID from 'identification'
        if p['identification'].strip():
            self.cur.execute('SELECT id, name FROM members')
            members = self.cur.fetchall()
            # create list of member names, lowercased, without diacritic
            splnames = map(
                    lambda x: (x['id'], rm_dia(x['name']).lower().split(' ')),
                    members)

 
            # 'Fér   Radek' -> ['fer', 'radek']
            name = filter(None, rm_dia(p['identification']).lower().split(' '))

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



    def add_payment(self, p):
        member=self.detect_member(p)

        if member:
            print('new payment from %s'%member['nick'])
            p['member_id']=member['id']
        else:
            print('new payment (%s)'%p['arrival'])

        # - create new record in Payments
        command  = "INSERT INTO Payments("
        command += ", ".join(p.keys())
        command += ") VALUES("
        command += ", ".join('?'*len(p))
        command += ");"

        arrival = map(lambda x: int(x), p['arrival'].split('.'))
        p['arrival'] = datetime.date(arrival[2], arrival[1], arrival[0])
        self.cur.execute(command, p.values())

    def update(self):
        """ Perform update from source (Fio webpages). """

        #open DB for storing payments
        #fetch will return dictionary rather then a tuple

        content = urllib.urlopen(url).read()
        root = lxml.html.fromstring(content)
        new_count=0

        for table in root.cssselect("table.table_prm")[2:]:
            for tr in reversed(table.cssselect("tr")[1:-1]):
                p = {
                'arrival' : tr[0].text_content(),
                'amount' : ((tr[1].text_content()).replace(",", ".")),
                'payment_type' : tr[2].text_content(),
                'KS' : tr[3].text_content(),
                'VS' : tr[4].text_content(),
                'SS' : tr[5].text_content(),
                'identification' : tr[6].text_content(),
                'message' : tr[7].text_content()
                }

                date=map(lambda x: int(x), p['arrival'].split('.'))
                self.cur.execute("SELECT * FROM Payments "
                        "WHERE arrival=? "
                        "AND identification=? "
                        "AND message=?;", (
                            datetime.date(date[2], date[1], date[0]),
                            p['identification'], p['message']))

                if self.cur.fetchone():
                    # there is already this payment in DB, skip it
                    pass
                else:
                    # this is new payment, not yet in DB, insert it
                    self.add_payment(p)
                    new_count += 1

        self.cur.execute("INSERT INTO UpdateHistory VALUES(datetime())")
        self.con.commit()

        print("Update complete (%d new payments)"%new_count)

if __name__ == "__main__":
    db = MembersDB()
    db.update()
