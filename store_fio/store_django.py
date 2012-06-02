#!/usr/bin/env python
# -*- coding: utf-8 -*-
# script to save new payments to django site

import sys
import urllib
import lxml.html

import sqlite3 as lite
import datetime
import unicodedata

import fio

from django.contrib.auth.models import User

from payments.models import Payment

#account overview URL
url = 'https://www.fio.cz/scgi-bin/hermes/dz-transparent.cgi?pohyby_DAT_od=01.01.2011&ID_ucet=2900086515'

def rm_dia(text):
    """Removes diacritic signs from the string $text"""

    if sys.hexversion >= 0x3000000:
        # On Python >= 3.0.0
        return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode()
    else:
        # On Python < 3.0.0
        return unicodedata.normalize('NFKD', unicode(text)).encode('ASCII', 'ignore')

class MembersDB:

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

        # check if there is something in VS field
        if payment.vs:
            try:
                member = User.objects.get(baseprofile__payments_id=payment.vs)
                return member
            except User.DoesNotExist:
                pass


        # use some heuristics, such as detecting memberID from 'identification'
        if payment.identification:
            members = User.objects.all()
            # create list of member names, lowercased, without diacritic
            splnames = map(
                    lambda x: (x,
                        rm_dia(x.first_name).lower() + ' ' +
                        rm_dia(x.last_name).lower()),
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
                    return tmp[0][0]

        return member

    def add_payment(self, payment):
        member = self.detect_member(payment)

        new_payment = Payment(
            date=payment.arrival,
            amount=payment.amount,
            payment_type=payment.payment_type,
            constant_symbol=payment.ks,
            variable_symbol=payment.vs,
            specific_symbol=payment.ss,
            identification=payment.identification,
            message=payment.message)

        if member:
            print('new payment (%s) from %s [%.2f]' % (payment.arrival,
                member, payment.amount))
            new_payment.user = member
        else:
            print('new payment (%s) - %s - %s [%.2f]'% (payment.arrival,
                payment.payment_type, payment.identification, payment.amount))

        new_payment.save()

    def update(self):
        """ Perform update from source (Fio webpages). """
        new_count=0

        for payment in fio.scrape(url):
            try:
                Payment.objects.get(date=payment.arrival,
                    identification=payment.identification,
                    message=payment.message,
                    amount=payment.amount)
            except Payment.MultipleObjectsReturned:
                continue
            except Payment.DoesNotExist:
                new_count += 1
                self.add_payment(payment)

        print("Update complete (%d new payments)" % new_count)

if __name__ == "__main__":
    db = MembersDB()
    db.update()
