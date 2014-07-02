#!/usr/bin/env python3.4
"""USAGE: split_bills.py HOUSE_YAML BILLS_YAML

Calculate how much each person in a house owes to split a bill evenly
amongst all people who are living in a house.

See README.md for YAML definitions.
"""
from collections import namedtuple
import datetime
from datetime import date
from datetime import timedelta
import yaml
import sys


FUTURE = date(9999, 1, 1)  # This is a date far in the future.
DateRange = namedtuple('DateRange', (
    'start',
    'end_exclusive',
))
EMPTY_INTERSECTION = DateRange(start=FUTURE, end_exclusive=FUTURE)
Bill = namedtuple('Bill', (
    'description',
    'paid_by',
    'for_dates',
    'amount',
))
SharedCost = namedtuple('SharedCost', (
    'description',
    'paid_by',
    'on_date',
    'shared_amongst',
    'amount',
))
Payment = namedtuple('Payment', (
    'payer',
    'to',
    'on_date',
    'amount',
))
Person = namedtuple('Person', (
    'name',
    'residencies',
))
House = namedtuple('House', (
    'name',
    'min_people',
    'people',
))


def split_date_range(dr, d):
    """Return however many date ranges exist after splitting by the given date.

    If the date falls outside the range, then that means no split occurs.

    >>> split_date_range(
    ... DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 2, 1)),
    ... date(2014, 1, 16))
    (DateRange(start=datetime.date(2014, 1, 1), end_exclusive=datetime.date(2014, 1, 16)), DateRange(start=datetime.date(2014, 1, 16), end_exclusive=datetime.date(2014, 2, 1)))
    >>> split_date_range(
    ... DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 2, 1)),
    ... date(2014, 3, 1))
    (DateRange(start=datetime.date(2014, 1, 1), end_exclusive=datetime.date(2014, 2, 1)),)

    :type dr: DateRange
    :type d: date
    :rtype: tuple of DateRanges
    """
    if dr.start < d < dr.end_exclusive:
        return (
            DateRange(start=dr.start, end_exclusive=d),
            DateRange(start=d, end_exclusive=dr.end_exclusive),
        )
    else:
        return dr,


def slice_date_range(dr, ds):
    """Slice up a date range into multiple ones on the given days.

    >>> slice_date_range(
    ... DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 2, 1)),
    ... frozenset((date(2014, 1, 5), date(2014, 1, 30))))
    (DateRange(start=datetime.date(2014, 1, 1), end_exclusive=datetime.date(2014, 1, 5)), DateRange(start=datetime.date(2014, 1, 5), end_exclusive=datetime.date(2014, 1, 30)), DateRange(start=datetime.date(2014, 1, 30), end_exclusive=datetime.date(2014, 2, 1)))

    :type dr: DateRange
    :type ds: iterable of dates
    :rtype: tuple of DateRanges
    """
    drs = (dr, )
    for d in ds:
        new_drs = tuple()
        for dr in drs:
            new_drs += split_date_range(dr, d)
        drs = new_drs
    return drs


def date_range_length(dr):
    """Return the timedelta corresponding to the length of a date range.

    >>> date_range_length(DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 2, 1)))
    datetime.timedelta(31)
    >>> date_range_length(DateRange(start=FUTURE, end_exclusive=FUTURE))
    datetime.timedelta(0)

    :type dr: DateRange
    :rtype: timedelta
    """
    if dr.end_exclusive == FUTURE and dr.start != FUTURE:
        raise ValueError('no length of an unbounded date range')
    return dr.end_exclusive - dr.start


def date_range_intersection(a, b):
    """Find the intersection date range of two other date ranges.

    >>> date_range_intersection(
    ... DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 1, 31)),
    ... DateRange(start=date(2014, 1, 16), end_exclusive=date(2014, 2, 15)))
    DateRange(start=datetime.date(2014, 1, 16), end_exclusive=datetime.date(2014, 1, 31))
    >>> date_range_intersection(
    ... DateRange(start=date(2014, 1, 2), end_exclusive=date(2014, 1, 2)),
    ... DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 1, 2)))
    DateRange(start=datetime.date(9999, 1, 1), end_exclusive=datetime.date(9999, 1, 1))
    >>> date_range_intersection(
    ... DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 1, 1)),
    ... DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 1, 2)))
    DateRange(start=datetime.date(2014, 1, 1), end_exclusive=datetime.date(2014, 1, 1))

    :type a: DateRange
    :type b: DateRange
    :rtype: DateRange
    """
    a, b = sorted((a, b))
    if b.start != a.start and b.start >= a.end_exclusive:
        return EMPTY_INTERSECTION
    else:
        return DateRange(start=b.start, end_exclusive=min(a.end_exclusive, b.end_exclusive))


def date_range_overlap_fraction(a, b):
    """Given two date ranges, find the fraction of a that is also in b.

    >>> date_range_overlap_fraction(
    ... DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 1, 31)),
    ... DateRange(start=date(2014, 1, 16), end_exclusive=date(2014, 2, 15)))
    0.5
    >>> date_range_overlap_fraction(
    ... DateRange(start=date(2014, 1, 2), end_exclusive=date(2014, 1, 2)),
    ... DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 2, 3)))
    1.0
    >>> date_range_overlap_fraction(
    ... DateRange(start=date(2014, 1, 2), end_exclusive=date(2014, 1, 2)),
    ... DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 1, 1)))
    0.0

    :type a: DateRange
    :type b: DateRange
    :rtype: float
    """
    i = date_range_intersection(a, b)
    if i == a:
        return 1.0
    elif i == EMPTY_INTERSECTION:
        return 0.0
    else:
        return date_range_length(i) / date_range_length(a)


def slice_bill(bill, ds):
    """Slice a bill into parts based on dates, with each part having the
    cost proportional to its duration.

    >>> slice_bill(
    ...     Bill(
    ...         description=None,
    ...         paid_by=None,
    ...         for_dates=DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 1, 31)),
    ...         amount=100.0),
    ...     frozenset((date(2014, 1, 16), )))
    (Bill(description=None, paid_by=None, for_dates=DateRange(start=datetime.date(2014, 1, 1), end_exclusive=datetime.date(2014, 1, 16)), amount=50.0), Bill(description=None, paid_by=None, for_dates=DateRange(start=datetime.date(2014, 1, 16), end_exclusive=datetime.date(2014, 1, 31)), amount=50.0))

    :type bill: Bill
    :type ds: iterable of dates
    :rtype: tuple of Bills
    """
    drs = slice_date_range(bill.for_dates, ds)
    split_bills = tuple(
        Bill(
            description=bill.description,
            paid_by=bill.paid_by,
            for_dates=dr,
            amount=bill.amount * date_range_overlap_fraction(bill.for_dates, dr),
        )
        for dr
        in drs
    )
    total_split_cost = sum(b.amount for b in split_bills)
    if round(bill.amount, 2) != round(total_split_cost, 2):
        raise RuntimeError('bill slice failed: total is {0}, slice total is {1}'.format(
            bill.amount,
            total_split_cost,
        ))
    return split_bills


def residents_during_date_range(dr, people):
    """Calculate names of people in residence during a date range.

    People must not be in residence for only part of the date range;
    that will raise an exception.

    :type dr: DateRange
    :type people: iterable of Persons
    :rtype: set of str
    """
    residents = set()
    for person in people:
        fraction_of_dr_in_residency = sum(date_range_overlap_fraction(dr, r) for r in person.residencies)
        if fraction_of_dr_in_residency == 1.0:
            residents.add(person.name)
        elif fraction_of_dr_in_residency != 0.0:
            raise RuntimeError('{0} is only in residence for part of {1}'.format(
                person,
                dr,
            ))
    return frozenset(residents)


def split_evenly(amount, among):
    """Given a cost, split it evenly amongst some people. Return a dict of what each person owes.

    >>> split_evenly(100.0, ('Bob', 'Alice'))
    {'Bob': 50.0, 'Alice': 50.0}

    :type amount: float in dollars
    :type among: iterable of str
    :rtype: dict from str to float in dollars
    """
    num_people = len(among)
    return {
        person: amount / num_people
        for person
        in among
    }


def sum_dicts(a, b):
    """Union the values in two dictionaries, summing if there are
    collisions.

    >>> sum_dicts({1: 1, 3: 3}, {1: 2, 4: 4})
    {1: 3, 3: 3, 4: 4}
    """
    o = dict(a)
    for k, v in b.items():
        try:
            o[k] += v
        except KeyError:
            o[k] = v
    return o


def bill_slice_personal_costs(bill_slice, house):
    """Calculate what dollar amounts of a slice of a bill are owed by each
    person in the house.

    An exception will be raised if anyone moves in or out during this
    slice's time period, or if the house is under-rented during the
    slice.

    :type bill_slice: Bill
    :type house: House
    :rtype: dict from str to float in dollars
    """
    residents_during_slice = residents_during_date_range(
        bill_slice.for_dates,
        house.people,
    )
    if len(residents_during_slice) < house.min_people:
        raise ValueError('house is under-rented during {0}'.format(
            bill_slice.for_dates,
        ))

    person_to_slice_cost = split_evenly(
        bill_slice.amount,
        residents_during_slice,
    )
    total_personal_slice_costs = sum(person_to_slice_cost.values())
    if round(bill_slice.amount, 2) != round(total_personal_slice_costs, 2):
        raise RuntimeError('splitting bill slice failed: slice total is {0}; split slice total is {1}'.format(
            bill_slice.amount,
            total_personal_slice_costs,
        ))
    return person_to_slice_cost


def bill_personal_costs(bill, house):
    """Calculate what dollar amounts of a bill are owed by all people in the
    house.

    :type bill: Bill
    :type house: House
    :rtype: dict from str to float in dollars
    """
    person_to_cost = {bill.paid_by: -bill.amount}
    for bill_slice in slice_bill(bill, house_move_dates(house)):
        person_to_slice_cost = bill_slice_personal_costs(bill_slice, house)
        person_to_cost = sum_dicts(person_to_cost, person_to_slice_cost)

    total_personal_costs = sum(person_to_cost.values())
    if round(total_personal_costs, 2) != 0.0:
        raise RuntimeError('splitting bill failed: total is {0}; split is {1!r}'.format(
            bill.amount,
            person_to_cost,
        ))
    return person_to_cost


def shared_personal_costs(shared_cost):
    person_to_cost = {shared_cost.paid_by: -shared_cost.amount}
    person_to_shared_cost = split_evenly(shared_cost.amount, shared_cost.shared_amongst)
    return sum_dicts(person_to_cost, person_to_shared_cost)


def make_payment(payment):
    return {
        payment.payer: -payment.amount,
        payment.to: payment.amount,
    }


def house_move_dates(house):
    """Return a set of all dates someone moves into or out of a house.

    :type house: House
    :rtype: set of dates
    """
    dates = set()
    for person in house.people:
        for residency in person.residencies:
            dates.add(residency.start)
            dates.add(residency.end_exclusive)
    return frozenset(dates)


def type_date(d):
    if isinstance(d, date):
        return d
    else:
        return datetime.strptime(d, '%Y-%m-%d').date()


def type_date_range(d):
    start_date = type_date(d['start'])
    if 'end' not in d and 'end_exclusive' not in d:
        end_date = FUTURE
    elif 'end' in d and 'end_exclusive' in d:
        raise ValueError('date range has both end and end_exclusive')
    elif 'end' in d:
        end_date = type_date(d['end']) + timedelta(days=1)
    else:
        end_date = type_date(d['end_exclusive'])
    return DateRange(start=start_date, end_exclusive=end_date)


def type_person(d):
    return Person(
        name=d['name'],
        residencies=tuple(type_date_range(r) for r in d['residencies']),
    )


def type_bill(d):
    if 'for_dates' in d and 'on_date' in d:
        raise ValueError('bill has both for_dates and on_date specified')
    if 'on_date' in d:
        dr_date = type_date(d['on_date'])
        dr = DateRange(start=dr_date, end_exclusive=dr_date)
    else:
        dr = type_date_range(d['for_dates'])
    return Bill(
        description=d['description'],
        paid_by=d['paid_by'],
        for_dates=dr,
        amount=float(d['amount']),
    )


def type_shared_cost(d):
    return SharedCost(
        description=d['description'],
        paid_by=d['paid_by'],
        shared_amongst=frozenset(d['shared_amongst']),
        amount=float(d['amount']),
        on_date=type_date(d['on_date']),
    )


def type_payment(d):
    return Payment(
        payer=d['payer'],
        to=d['to'],
        on_date=type_date(d['on_date']),
        amount=float(d['amount']),
    )


def type_house(d):
    return House(
        name=d['name'],
        min_people=int(d['min_people']),
        people=tuple(type_person(p) for p in d['people']),
    )


def load_yaml(fn):
    with open(fn, 'r') as fp:
        return yaml.safe_load(fp)


def main(house_fn):
    house = type_house(load_yaml(house_fn)['house'])
    bills = tuple(type_bill(b) for b in load_yaml(bills_fn)['bills'])
    shared_costs = tuple(type_shared_cost(c) for c in load_yaml(shared_costs_fn)['shared_costs'])
    payments = tuple(type_payment(p) for p in load_yaml(payments_fn)['payments'])

    person_to_grand_total = {}
    for bill in bills:
        person_to_cost = bill_personal_costs(bill, house)
        person_to_grand_total = sum_dicts(person_to_grand_total, person_to_cost)
        print('----')
        print_bill(bill)
        print_person_to_cost(person_to_cost)
    for shared_cost in shared_costs:
        person_to_cost = shared_personal_costs(shared_cost)
        person_to_grand_total = sum_dicts(person_to_grand_total, person_to_cost)
        print('----')
        print_shared_cost(shared_cost)
        print_person_to_cost(person_to_cost)
    for payment in payments:
        person_to_cost = make_payment(payment)
        person_to_grand_total = sum_dicts(person_to_grand_total, person_to_cost)
        print('----')
        print_payment(payment)

    print('====')
    print('Grand Total:')
    print_person_to_cost(person_to_grand_total)
    if round(sum(person_to_grand_total.values()), 2) != 0.0:
        raise RuntimeError('grand total does not check out')


def print_bill(bill):
    print('For {0!r} from {1} to {2} totalling ${3:.2f} (paid by {4}):'.format(
        bill.description,
        bill.for_dates.start,
        bill.for_dates.end_exclusive - timedelta(days=1),
        bill.amount,
        bill.paid_by,
    ))


def print_shared_cost(shared_cost):
    print('For {0!r} totalling ${1:.2f} shared amongst {2} (paid by {3})'.format(
        shared_cost.description,
        shared_cost.amount,
        ', '.join(shared_cost.shared_amongst),
        shared_cost.paid_by,
    ))


def print_payment(payment):
    print('Payment from {0} to {1} of ${2:.2f}'.format(
        payment.payer,
        payment.to,
        payment.amount,
    ))


def print_person_to_cost(person_to_cost):
    print('Costs:')
    for person, cost in sorted(person_to_cost.items()):
        if cost != 0.0:
            print('  {0}: ${1:.2f}'.format(person.name if isinstance(person, Person) else person, cost))


if __name__ == '__main__':
    house_fn = sys.argv[1]
    main(house_fn)
