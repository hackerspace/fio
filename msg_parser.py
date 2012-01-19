#!/usr/bin/env python

import re

monthspec_pattern = re.compile(
        r'(?P<year>\d{4})/'
        r'('
            r'(?P<month>\d\d?$)'
            r'|'
            r'(?P<range>\d\d?-\d\d?$)'
        r')'
        )

class MessageSyntaxError(Exception):
    pass

def check_month(x):
    if int(x) not in range(1,13):
        raise MessageSyntaxError('Month not in range <1,12>')
    return int(x)


def parse_message(msg):
    """
    Checks message syntax for month specification (according to
    http://undergroundlab.cz/hackerspace/wiki/legal) and maps specifications
    like "2011/1 2011/2-3" to:
        [{'year': 2011, 'month': 1}, {'year': 2011, 'month': 2, 'month2': 3}]
    """

    # "message" must contain month specification (range of payment):
    #     possible month specifications:
    #       - <year>/<month>
    #       - <year>/<month_range_in_one_year>
    #     examples:
    #       - 2011/01
    #       - 2011/1
    #       - 2011/1-3
    # specifications can be chained: "2011/11-12 2012/1-5"
    periods=[]

    # special case for periodical fixed payment - message identification
    # is deduced from "arrival" field
    if (msg == 'clensky prispevek' or msg == ''):
        return periods

    for spec in msg.split(' '):
        period={}

        m = monthspec_pattern.match(spec)
        if m is None:
            raise MessageSyntaxError('Cannot parse date specification')
        else:
            period['year'] = int(m.group('year'))

            # check month ranges (1-12)
            if m.group('month') is not None:
                period['month'] = check_month(m.group('month'))
            else:
                period['month'] = check_month(m.group('range').split('-')[0])
                period['month2'] = check_month(m.group('range').split('-')[1])
        periods.append(period)
    return periods


# Basic testing
if __name__ == '__main__':
    positives = (
            '2000/1', '2999/01', '2999/12',         # simple
            '2011/1-2', '2011/01-2', '2011/1-02',   # ranges
            '2011/1 2011/2', '2011/10-12 2012/1',   # multiple specs
            'clensky prispevek'                     # special case
            )
    negatives = (
            'asdf', '2011/feb', '2012/1-jan', '2011/1-3 2011/april',
            '2011', '2011/13'  # and so on ...
            )

    for spec in positives:
        try:
            m = parse_message(spec)
            print('OK(accepted) - %s'%spec)
            print('  ', m)
        except MessageSyntaxError as e:
            print('FAIL(should be accepted) - %s [%s]'%(spec, e))

    print()
    for spec in negatives:
        try:
            m = parse_message(spec)
            print('FAIL(shouldnt be accepted) - %s'%spec)
        except MessageSyntaxError as e:
            print('OK(rejected) - %s [%s]'%(spec, e))
            continue
