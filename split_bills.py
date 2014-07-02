#!/usr/bin/env python3.4
"""USAGE: split_bills.py HOUSE_YAML

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
    'paid_on_date',
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


def date_range_of_day(d):
    """Generate a zero-length date range for a given day.

    :type d: datetime.date
    :rtype: DateRange
    """
    return DateRange(start=d, end_exclusive=d)


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
            paid_on_date=bill.paid_on_date,
            amount=bill.amount * date_range_overlap_fraction(bill.for_dates, dr),
        )
        for dr
        in drs
    )

    total_split_cost = sum(b.amount for b in split_bills)
    if round(bill.amount, 2) != round(total_split_cost, 2):
        raise RuntimeError('slicing bill failed: total is {0}, slices are {1!r}'.format(
            bill.amount,
            tuple(b.amount for b in split_bills),
        ))
    return split_bills


def resident_names_during_date_range(dr, people):
    """Calculate names of people in residence during a date range.

    People must not be in residence for only part of the date range;
    that will raise an exception.

    :type dr: DateRange
    :type people: iterable of Persons
    :rtype: set of str
    """
    resident_names = set()
    for person in people:
        fraction_of_dr_in_residency = sum(date_range_overlap_fraction(dr, r) for r in person.residencies)
        if fraction_of_dr_in_residency == 1.0:
            resident_names.add(person.name)
        elif fraction_of_dr_in_residency != 0.0:
            raise RuntimeError('{0} is only in residence for part of {1}'.format(
                person,
                dr,
            ))
    return frozenset(resident_names)


def split_evenly(amount, among_names):
    """Given an amount, split it evenly amongst some people. Return a dict of what each person owes.

    >>> sorted(split_evenly(100.0, ('Bob', 'Alice')).items())
    [('Alice', 50.0), ('Bob', 50.0)]

    :type amount: float in dollars
    :type among_names: iterable of str
    :rtype: dict from str to float in dollars
    """
    num_people = len(among_names)
    name_to_dues = {
        person: amount / num_people
        for person
        in among_names
    }

    total_dues = sum(name_to_dues.values())
    if round(total_dues, 2) != round(amount, 2):
        raise RuntimeError('splitting amount failed: amount is {0}; dues are {1!r}'.format(
            amount,
            name_to_dues,
        ))
    return name_to_dues


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
    resident_names_during_slice = resident_names_during_date_range(
        bill_slice.for_dates,
        house.people,
    )
    if len(resident_names_during_slice) < house.min_people:
        raise ValueError('house is under-rented during {0}'.format(
            bill_slice.for_dates,
        ))

    name_to_dues = split_evenly(
        bill_slice.amount,
        resident_names_during_slice,
    )

    total_dues = sum(name_to_dues.values())
    if round(bill_slice.amount, 2) != round(total_dues, 2):
        raise RuntimeError('splitting bill slice failed: total is {0}; dues are {1!r}'.format(
            bill_slice.amount,
            name_to_dues,
        ))
    return name_to_dues


def dues_for_bill(bill, house):
    """Calculate what dollar amounts of a bill are owed by all people in the
    house.

    :type bill: Bill
    :type house: House
    :rtype: dict from str to float in dollars
    """
    name_to_dues = {bill.paid_by: -bill.amount}
    for bill_slice in slice_bill(bill, house_move_dates(house)):
        name_to_dues_for_slice = bill_slice_personal_costs(bill_slice, house)
        name_to_dues = sum_dicts(name_to_dues, name_to_dues_for_slice)

    total_dues = sum(name_to_dues.values())
    if round(total_dues, 2) != 0.0:
        raise RuntimeError('splitting bill failed: total is {0}; dues are {1!r}'.format(
            bill.amount,
            name_to_dues,
        ))
    return name_to_dues


def dues_for_shared_cost(shared_cost, house):
    """Calculate what dollar amounts of a shared cost are owed by those who shared it.

    :type shared_cost: SharedCost
    :type house: House
    :rtype: dict from str to float in dollars
    """
    name_to_dues = {shared_cost.paid_by: -shared_cost.amount}
    if shared_cost.shared_amongst:
        shared_amongst_names = shared_cost.shared_amongst
    else:
        shared_amongst_names = resident_names_during_date_range(date_range_of_day(shared_cost.on_date), house.people)
    name_to_dues_for_shared_cost = split_evenly(shared_cost.amount, shared_amongst_names)
    name_to_dues = sum_dicts(name_to_dues, name_to_dues_for_shared_cost)

    total_dues = sum(name_to_dues.values())
    if round(total_dues, 2) != 0.0:
        raise RuntimeError('splitting shared cost failed: total is {0}; dues are {1!r}'.format(
            shared_cost.amount,
            name_to_dues,
        ))
    return name_to_dues


def dues_for_payment(payment):
    """Convert a payment into dues.

    :type payment: Payment
    :rtype: dict from str to float in dollars
    """
    name_to_dues = {
        payment.payer: -payment.amount,
        payment.to: payment.amount,
    }

    total_dues = sum(name_to_dues.values())
    if round(total_dues, 2) != 0.0:
        raise RuntimeError('splitting payment failed: total is {0}; dues are {1!r}'.format(
            payment.amount,
            name_to_dues,
        ))
    return name_to_dues


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
        raise ValueError("date range has both 'end' and 'end_exclusive'")
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
    return Bill(
        description=d['description'],
        paid_by=d['paid_by'],
        for_dates=type_date_range(d['for_dates']),
        paid_on_date=type_date(d['on_date']),
        amount=float(d['amount']),
    )


def type_shared_cost(d):
    if 'shared_amongst' in d:
        shared_amongst = frozenset(d['shared_amongst'])
    else:
        shared_amongst = None
    return SharedCost(
        description=d['description'],
        paid_by=d['paid_by'],
        shared_amongst=shared_amongst,
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


def date_order_item(i):
    if isinstance(i, Bill):
        return i.paid_on_date
    elif isinstance(i, SharedCost):
        return i.on_date
    elif isinstance(i, Payment):
        return i.on_date
    else:
        raise TypeError('unknown ledger item type {0!r}'.format(type(i)))


def type_ledger(d):
    for i in d:
        if len(i) > 1:
            raise ValueError('ledger item has multiple types {0!r}'.format(i.keys()))
        (ik, iv), *_ = i.items()
        if ik == 'bill':
            yield type_bill(iv)
        elif ik == 'shared_cost':
            yield type_shared_cost(iv)
        elif ik == 'payment':
            yield type_payment(iv)
        else:
            raise TypeError('unknown ledger item type {0!r}'.format(ik))


def type_house(d):
    return House(
        name=d['name'],
        min_people=int(d['min_people']),
        people=tuple(type_person(p) for p in d['people']),
    )


def load_yaml(fn):
    with open(fn, 'r') as fp:
        return yaml.safe_load(fp)


def main(in_fn):
    in_f_d = load_yaml(in_fn)
    house = type_house(in_f_d['house'])
    ledger = sorted(tuple(type_ledger(in_f_d['ledger'])), key=date_order_item)

    name_to_total_dues = {}
    for i in ledger:
        print('---> ', end='')
        if isinstance(i, Bill):
            print_bill(i)
            name_to_dues_for_i = dues_for_bill(i, house)
        elif isinstance(i, SharedCost):
            print_shared_cost(i)
            name_to_dues_for_i = dues_for_shared_cost(i, house)
        elif isinstance(i, Payment):
            print_payment(i)
            name_to_dues_for_i = dues_for_payment(i)
        else:
            raise TypeError('unknown ledger item type {0!r}'.format(type(i)))
        name_to_total_dues = sum_dicts(name_to_total_dues, name_to_dues_for_i)
        print_name_to_dues(name_to_dues_for_i)
        print('========> Running Total')
        print_name_to_dues(name_to_total_dues)
        if round(sum(name_to_total_dues.values()), 2) != 0.0:
            raise RuntimeError('grand total does not check out')


def print_bill(bill):
    print('Bill for {0!r} from {1} until {2} totalling ${3:.2f} paid by {4} on {5}'.format(
        bill.description,
        bill.for_dates.start,
        bill.for_dates.end_exclusive,
        bill.amount,
        bill.paid_by,
        bill.paid_on_date,
    ))


def print_shared_cost(shared_cost):
    if shared_cost.shared_amongst:
        shared_amongst_str = ', '.join(shared_cost.shared_amongst)
    else:
        shared_amongst_str = 'everyone'
    print('Cost of {0!r} totalling ${1:.2f} shared amongst {2} paid by {3} on {4}'.format(
        shared_cost.description,
        shared_cost.amount,
        shared_amongst_str,
        shared_cost.paid_by,
        shared_cost.on_date,
    ))


def print_payment(payment):
    print('Payment from {0} to {1} of ${2:.2f} on {3}'.format(
        payment.payer,
        payment.to,
        payment.amount,
        payment.on_date,
    ))


def print_name_to_dues(name_to_dues):
    print('Dues:')
    for name, dues in sorted(name_to_dues.items()):
        if dues != 0.0:
            print('  {0}: ${1:.2f}'.format(name, dues))


if __name__ == '__main__':
    house_fn = sys.argv[1]
    main(house_fn)
