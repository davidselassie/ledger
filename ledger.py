#!/usr/bin/env python3.4
"""USAGE: ledger.py HOUSE_YAML BILLS_YAML

Calculate how much each person in a house owes to split a bill evenly
amongst all people who are living in a house.

See README.md for YAML definitions.
"""
from collections import namedtuple
from datetime import date
from datetime import timedelta
import yaml
import sys


FUTURE = date(9999, 1, 1)  # This is a date far in the future.
DateRange = namedtuple('DateRange', (
    'start',
    'end_exclusive',
))
Bill = namedtuple('Bill', (
    'description',
    'for_dates',
    'total_cost',
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

    >>> split_date_range(DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 2, 1)), date(2014, 1, 16))
    (DateRange(start=datetime.date(2014, 1, 1), end_exclusive=datetime.date(2014, 1, 16)), DateRange(start=datetime.date(2014, 1, 16), end_exclusive=datetime.date(2014, 2, 1)))
    >>> split_date_range(DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 2, 1)), date(2014, 3, 1))
    (DateRange(start=datetime.date(2014, 1, 1), end_exclusive=datetime.date(2014, 2, 1)),)

    :type dr: DateRange
    :type d: date
    :rtype: tuple of DateRanges
    """
    if d > dr.start and d < dr.end_exclusive:
        return (
            DateRange(start=dr.start, end_exclusive=d),
            DateRange(start=d, end_exclusive=dr.end_exclusive),
        )
    else:
        return (dr, )


def slice_date_range(dr, ds):
    """Slice up a date range into multiple ones on the given days.

    >>> slice_date_range(DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 2, 1)), frozenset((date(2014, 1, 5), date(2014, 1, 30))))
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

    :type dr: DateRange
    :rtype: timedelta
    """
    if (
            dr.start == FUTURE
            or dr.end_exclusive == FUTURE
            and not (
                dr.start == FUTURE
                and dr.end_exclusive == FUTURE
            )
    ):
        raise ValueError('no length of an unbounded date range')
    return dr.end_exclusive - dr.start


def date_range_intersection(a, b):
    """Find the intersection date range of two other date ranges.

    >>> date_range_intersection(
    ... DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 1, 31)),
    ... DateRange(start=date(2014, 1, 16), end_exclusive=date(2014, 2, 15)))
    DateRange(start=datetime.date(2014, 1, 16), end_exclusive=datetime.date(2014, 1, 31))

    :type a: DateRange
    :type b: DateRange
    :rtype: DateRange
    """
    i_lb = max(a.start, b.start)
    i_ub = min(a.end_exclusive, b.end_exclusive)
    if i_ub >= i_lb:
        return DateRange(start=i_lb, end_exclusive=i_ub)
    else:
        # Return an empty date range.
        return DateRange(start=i_lb, end_exclusive=i_lb)


def date_range_overlap_fraction(a, b):
    """Given two date ranges, find the fraction of a that is also in b.

    >>> date_range_overlap_fraction(
    ... DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 1, 31)),
    ... DateRange(start=date(2014, 1, 16), end_exclusive=date(2014, 2, 15)))
    0.5

    :type a: DateRange
    :type b: DateRange
    :rtype: float
    """
    i = date_range_intersection(a, b)
    return date_range_length(i) / date_range_length(a)


def slice_bill(bill, ds):
    """Slice a bill into parts based on dates, with each part having the
    cost proportional to its duration.

    >>> slice_bill(Bill(description=None, for_dates=DateRange(start=date(2014, 1, 1), end_exclusive=date(2014, 1, 31)), total_cost=100.0), frozenset((date(2014, 1, 16), )))
    (Bill(description=None, for_dates=DateRange(start=datetime.date(2014, 1, 1), end_exclusive=datetime.date(2014, 1, 16)), total_cost=50.0), Bill(description=None, for_dates=DateRange(start=datetime.date(2014, 1, 16), end_exclusive=datetime.date(2014, 1, 31)), total_cost=50.0))

    :type bill: Bill
    :type ds: iterable of dates
    :rtype: tuple of Bills
    """
    drs = slice_date_range(bill.for_dates, ds)
    split_bills = tuple(
        Bill(
            description=bill.description,
            for_dates=dr,
            total_cost=bill.total_cost * date_range_overlap_fraction(bill.for_dates, dr),
        )
        for dr
        in drs
    )
    total_split_cost = sum(b.total_cost for b in split_bills)
    if round(bill.total_cost, 2) != round(total_split_cost, 2):
        raise RuntimeError('bill slice failed: total is {0}, slice total is {1}'.format(
            bill.total_cost,
            total_split_cost,
        ))
    return split_bills


def residents_during_date_range(dr, people):
    """Calculate who was in residence during a date range.

    People must not be in residence for only part of the date range;
    that will raise an exception.

    :type dr: DateRange
    :type people: iterable of Persons
    :rtype: set of Persons
    """
    residents = set()
    for person in people:
        fraction_of_dr_in_residency = sum(date_range_overlap_fraction(dr, r) for r in person.residencies)
        if fraction_of_dr_in_residency == 1.0:
            residents.add(person)
        elif fraction_of_dr_in_residency != 0.0:
            raise RuntimeError('{0} is only in residence for part of {1}'.format(
                person,
                dr,
            ))
    return frozenset(residents)


def split_bill_evenly(bill_total_cost, residents):
    """Given the cost of a bill, split it evenly amongst all people who are
    currently in residence. Return a dict of what each person owes.

    :type bill_total_cost: float in dollars
    :type residents: iterable of Persons
    :rtype: dict from Person to float in dollars
    """
    num_residents = len(residents)
    return {
        person: bill_total_cost / num_residents
        for person
        in residents
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
    :rtype: dict from Person to float in dollars

    """
    residents_during_slice = residents_during_date_range(
        bill_slice.for_dates,
        house.people,
    )
    if len(residents_during_slice) < house.min_people:
        raise ValueError('house is under-rented during {0}'.format(
            bill_slice.for_dates,
        ))

    person_to_slice_cost = split_bill_evenly(
        bill_slice.total_cost,
        residents_during_slice,
    )
    total_personal_slice_costs = sum(person_to_slice_cost.values())
    if round(bill_slice.total_cost, 2) != round(total_personal_slice_costs, 2):
        raise RuntimeError('splitting bill slice failed: slice total is {0}; split slice total is {1}'.format(
            bill_slice.total_cost,
            total_personal_slice_costs,
        ))
    return person_to_slice_cost


def bill_personal_costs(bill, house):
    """Calculate what dollar amounts of a bill are owed by all people in the
    house.

    :type bill: Bill
    :type house: House
    :rtype: dict from Person to float in dollars
    """
    person_to_cost = {}
    for bill_slice in slice_bill(bill, house_move_dates(house)):
        person_to_slice_cost = bill_slice_personal_costs(bill_slice, house)
        person_to_cost = sum_dicts(person_to_cost, person_to_slice_cost)

    total_personal_costs = sum(person_to_cost.values())
    if round(bill.total_cost, 2) != round(total_personal_costs, 2):
        raise RuntimeError('splitting bill failed: total is {0}; split total is {1}'.format(
            bill.total_cost,
            total_personal_costs,
        ))
    return person_to_cost


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
    if 'end' in d:
        end_date = type_date(d['end']) + timedelta(days=1)
    elif 'end_exclusive' in d:
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
        for_dates=type_date_range(d['for_dates']),
        total_cost=float(d['total_cost']),
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


def main(house_fn, bills_fn):
    house = type_house(load_yaml(house_fn)['house'])
    bills = tuple(type_bill(b) for b in load_yaml(bills_fn)['bills'])

    for bill in bills:
        person_to_cost = bill_personal_costs(bill, house)
        print('----')
        print_bill(bill)
        print_person_to_cost(person_to_cost)


def print_bill(bill):
    print('For {0!r} from {1} to {2} totalling ${3:.2f}:'.format(
        bill.description,
        bill.for_dates.start,
        bill.for_dates.end_exclusive - timedelta(days=1),
        bill.total_cost,
    ))


def print_person_to_cost(person_to_cost):
    print('Costs:')
    for person, cost in sorted(person_to_cost.items()):
        if cost > 0.0:
            print('  {0}: ${1:.2f}'.format(person.name, cost))


if __name__ == '__main__':
    house_fn, bills_fn = sys.argv[1:]
    main(house_fn, bills_fn)
