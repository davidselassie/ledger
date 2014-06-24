#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division

import datetime
import urllib

bills = {
    'PG&E': 355.30,
    'Comcast': 120.80,
}
people = 7
month_date = datetime.date(2014, 4, 1)

# Fixed script here.


def build_mailto(to, cc, subject, body):
    params = {}
    if cc:
        params['cc'] = cc
    if subject:
        params['subject'] = subject
    if body:
        params['body'] = body
    params_str = urllib.urlencode(params)
    pay_mailto = 'mailto:{0}?{1}'.format(to, params_str)

    print('To: {0}'.format(to))
    if cc:
        print('Cc: {0}'.format(cc))
    if subject:
        print('Subject: {0}'.format(subject))
    print()
    if body:
        print(body)
        print()

    return pay_mailto


def build_pay_mailto(amount, month_date):
    HOUSE_ACCT_EMAIL = 'housetub@gmail.com'
    SQUARE_EMAIL = 'cash@square.com'

    subject = 'I payed my Housetub bills for {month_year}! ${amount:.2f}'.format(
        month_year=month_date.strftime('%B %Y'),
        amount=amount,
    )
    return build_mailto(HOUSE_ACCT_EMAIL, SQUARE_EMAIL, subject, None)


def build_summary_mailto(bills, people, month_date):
    total_amount = sum(bills.values())
    amount_per_person = total_amount / people

    itemized = '\n'.join(
        '* {service}: ${cost:.2f}'.format(
            service=service,
            cost=cost,
        )
        for service, cost
        in bills.items()
    )
    pay_mailto = build_pay_mailto(amount_per_person, month_date)
    subject = 'Housetub Bills for {month_year}: ${amount_per_person:.2f} / person'.format(
        month_year=month_date.strftime('%B %Y'),
        amount_per_person=amount_per_person,
    )
    body = """{subject}
{hr}
{itemized}
Total: ${total_amount:.2f}
Per Person for {people} People: ${amount_per_person:.2f}

Pay Link {pay_mailto}
""".format(
        subject=subject,
        hr='=' * len(subject),
        itemized=itemized,
        total_amount=total_amount,
        people=people,
        amount_per_person=amount_per_person,
        pay_mailto=pay_mailto,
    )

    HOUSE_GROUP_EMAIL = 'housetub@googlegroups.com'
    return build_mailto(HOUSE_GROUP_EMAIL, None, subject, body)


if __name__ == '__main__':
    print(build_summary_mailto(bills, people, month_date))
