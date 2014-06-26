#!/usr/bin/env python3.4
"""
"""


import arrow
from collections import namedtuple
import datetime
import yaml
import sys


PRESENT_DAY = 'NOW'
DateRange = namedtuple('DateRange', (
    'start',
    'end',
))
Bill = namedtuple('Bill', (
    'type_id',
    'for_dates',
    'total_cost',
    'payer_id',
))
Person = namedtuple('Person', (
    'id_name',
    'residency_dates',
))
Payment = namedtuple('Payment', (
    'payer_id',
    'payee_id',
    'amount',
))


def date_range_length(dr):
    """Return the timedelta corresponding to the lenght of a date range.

    :type dr: DateRange
    :rtype: timedelta
    """
    return dr.end - dr.start


def date_range_overlap_fraction(a, b):
    """Given two date ranges, find the fraction of a that is contained by b.

    :type a: DateRange
    :type b: DateRange
    :rtype: float
    """
    i_lb = max(a.start, b.start)
    i_ub = min(a.end, b.end)
    i_range = i_lb - i_ub
    if i_range < timedelta():
        return 0.0
    else:
        return i_range / date_range_length(a)


def intersect(bill, person):
    return date_range_overlap_fraction(bill.for_dates, person.residency_dates) * person.weight * bill.total_cost


def type_date(d):
    if d == PRESENT_DAY:
        return arrow.utcnow()
    elif isinstance(d, datetime.date):
        return arrow.get(datetime.datetime.combine(d, datetime.time()), 'UTC')
    else:
        return arrow.get(d)


def type_date_range(d):
    return DateRange(start=type_date(d['start']), end=type_date(d['end']))


def type_person(d):
    return Person(
        id_name=d['id_name'],
        residency_dates=type_date_range(d['residency_dates']),
    )


def type_bill(d):
    return Bill(
        type_id=d['type_id'],
        for_dates=type_date_range(d['for_dates']),
        total_cost=float(d['total_cost']),
        payer_id=d['payer_id'],
    )


def type_payment(d):
    return Payment(
        payer_id=d['payer_id'],
        payee_id=d['payee_id'],
        amount=float(d['amount']),
    )


def load_yaml(f):
    with open(f, 'r') as fp:
        d = yaml.safe_load(fp)

    bills = tuple(type_bill(bd) for bd in d['bills'])
    people = tuple(type_person(pd) for pd in d['people'])
    payments = tuple(type_payment(pd) for pd in d['payments'])

    return bills, people, payments


if __name__ == '__main__':
    print(load_yaml(sys.argv[1]))
