#!/usr/bin/env python
# -*- coding: utf-8 -*-
# script to save new payments to django site

from __future__ import unicode_literals

import sys
import time
import urllib
import lxml.html

import sqlite3 as lite
import datetime
import unicodedata

import fiobank

from django.contrib.auth.models import User

from payments.models import Payment

# Modified retry decorator with exponential backoff from PythonDecoratorLibrary
def retry(tries, delay=3, backoff=2, verbose=False):
    '''
    Retries a function or method until it returns value.

    Delay sets the initial delay in seconds, and backoff sets the factor by which
    the delay should lengthen after each failure. backoff must be greater than 1,
    or else it isn't really a backoff. tries must be at least 0, and delay
    greater than 0.
    '''

    def deco_retry(func):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay  # make mutable

            while mtries > 0:
                # Catching too general exception Exception
                # pylint: disable-msg=W0703
                try:
                    return func(*args, **kwargs)
                except Exception as ex:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                # pylint: enable-msg=W0703

                    if verbose:
                        print('Exception occured, retrying in {0} seconds'
                              ' {1}/{2}'.format(mdelay, (tries - mtries + 1),
                                                tries))

                        msg = traceback.format_exception(exc_type, exc_value,
                                                         exc_traceback)

                        if type(msg) == list:
                            msg = ''.join(msg)

                        print(msg)
                    mtries -= 1

                time.sleep(mdelay)
                mdelay *= backoff  # make future wait longer

            raise ex  # out of tries

        return f_retry
    return deco_retry


# account token
tok = ''

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
        if payment['variable_symbol']:
            try:
                member = User.objects.get(baseprofile__payments_id=payment['variable_symbol'])
                return member
            except User.DoesNotExist:
                pass


        # use some heuristics, such as detecting memberID from 'identification'
        if payment['identification']:
            members = User.objects.all()
            # create list of member names, lowercased, without diacritic
            splnames = map(
                    lambda x: (x,
                        rm_dia(x.first_name).lower() + ' ' +
                        rm_dia(x.last_name).lower()),
                    members)

            # 'Fér   Radek' -> ['fer', 'radek']
            name = filter(None, rm_dia(payment['identification']).lower().split(' '))

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
            date=payment['date'],
            amount=payment['amount'],
            payment_type=payment['type'],
            constant_symbol=payment['constant_symbol'],
            variable_symbol=payment['variable_symbol'],
            specific_symbol=payment['specific_symbol'],
            identification=payment['identification'],
            message=payment['recipient_message'])

        if member:
            print('new payment (%s) from %s [%.2f]' % (payment['date'],
                member, payment['amount']))
            new_payment.user = member
        else:
            print('new payment (%s) - %s - %s [%.2f]'% (payment['date'],
                payment['type'], payment['identification'], payment['amount']))

        new_payment.save()

    @retry(5, delay=10, backoff=10)
    def update(self):
        """ Perform update from source (Fio webpages). """
        new_count=0

        fd = datetime.date.today() - datetime.timedelta(days=150)

        fio = fiobank.FioBank(token='W2Sd4Us7ie5w2Jd0bvU0JQC8VfADE2u1jUHhZDikR1bjU6jVqT5csYXq48mijqNA')

        for payment in fio.last(from_date=fd.strftime('%Y-%m-%d')):
            try:
		pid = ''
                if 'comment' in payment:
		    pid = payment['comment']
                if 'account_name' in payment:
                    pid = payment['account_name']

		payment['identification'] = pid

                if not 'recipient_message' in payment:
                    payment['recipient_message'] = ''

		symbols = ['variable_symbol', 'specific_symbol', 'constant_symbol']
		for sym in symbols:
			if sym not in payment:
				payment[sym] = 0

                print("looking up {0} {1} {2} {3}".format(payment['date'],
                                                      payment['identification'],
                                                      payment['recipient_message'],
                                                      payment['amount']))

                Payment.objects.get(date=payment['date'],
                    identification=payment['identification'],
                    message=payment['recipient_message'],
                    amount=payment['amount'])
            except Payment.MultipleObjectsReturned:
                continue
            except Payment.DoesNotExist:
                new_count += 1
                self.add_payment(payment)

        print("Update complete (%d new payments)" % new_count)

if __name__ == "__main__":
    db = MembersDB()
    db.update()
