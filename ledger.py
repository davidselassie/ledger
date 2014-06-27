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
    'end',
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


def date_range_length(dr):
    """Return the timedelta corresponding to the lenght of a date range.

    :type dr: DateRange
    :rtype: timedelta
    """
    if (
            dr.start == FUTURE
            or dr.end == FUTURE
            and not (
                dr.start == FUTURE
                and dr.end == FUTURE
            )
    ):
        raise ValueError('no length of an unbounded date range')
    return dr.end - dr.start


def date_range_intersection(a, b):
    """Find the intersection date range of two other date ranges.

    :type a: DateRange
    :type b: DateRange
    :rtype: DateRange
    """
    i_lb = max(a.start, b.start)
    i_ub = min(a.end, b.end)
    if i_ub >= i_lb:
        return DateRange(start=i_lb, end=i_ub)
    else:
        # Return an empty date range.
        return DateRange(start=i_lb, end=i_lb)


def date_range_overlap_fraction(a, b):
    """Given two date ranges, find the fraction of a that is contained by b.

    :type a: DateRange
    :type b: DateRange
    :rtype: float
    """
    i = date_range_intersection(a, b)
    return date_range_length(i) / date_range_length(a)


def calc_relative_responsibility(bill_date_range, person):
    """Figure out the _relative_ share of a bill a person is responsible
    for.

    If a person is only in residence for half of the bill's duration,
    they are responsible for 0.5 a person's share. Someone who is in
    residence for the entirety of a bill is responsible for 1.0 of a
    share.

    :type bill_date_range: DateRange
    :type person: Person
    :rtype: float
    """
    return sum(
        date_range_overlap_fraction(bill_date_range, residency)
        for residency
        in person.residencies
    )


def calc_all_relative_responsibilities(bill, people):
    """Calculate the relative responsabilities of a list of people for a
    bill.

    :type bill: Bill
    :type people: iterable of Persons
    :rtype: dict from Person to float
    """
    return {
        person: calc_relative_responsibility(bill.for_dates, person)
        for person
        in people
    }


def calc_personal_costs_from_responsibilities(bill_total_cost, person_to_relative_responsibility):
    """Given relative responsibilities for all people, determine what part
    of the total cost of a bill each owes.

    :type bill: Bill
    :type person_to_relative_responsibility: dict from Person to float
    :rtype: dict from Person to float in dollars
    """
    total_responsibility = sum(person_to_relative_responsibility.values())
    return {
        person: relative_responsibility / total_responsibility * bill_total_cost
        for person, relative_responsibility
        in person_to_relative_responsibility.items()
    }


def calc_all_personal_costs(bill, house):
    """Calculate what dollar amounts of a bill are owed by all people in the
    house.

    :type bill: Bill
    :type house: House
    :rtype: dict from Person to float in dollars
    """
    person_to_relative_responsibility = calc_all_relative_responsibilities(
        bill,
        house.people,
    )

    if sum(person_to_relative_responsibility.values()) < house.min_people:
        raise ValueError('house is under-rented during {0}'.format(
            bill.for_dates,
        ))

    person_to_cost = calc_personal_costs_from_responsibilities(
        bill.total_cost,
        person_to_relative_responsibility,
    )

    total_personal_costs = sum(person_to_cost.values())
    if round(bill.total_cost, 2) != round(total_personal_costs, 2):
        raise RuntimeError('bill split failed: total is {0}; split total is {1}'.format(
            bill.total_cost,
            total_personal_costs,
        ))

    return person_to_cost


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
        end_date = type_date(d['end'])
    elif 'end_exclusive' in d:
        end_date = type_date(d['end_exclusive']) - timedelta(days=1)
    return DateRange(start=start_date, end=end_date)


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
        person_to_cost = calc_all_personal_costs(bill, house)
        print('----')
        print_bill(bill)
        print_person_to_cost(person_to_cost)


def print_bill(bill):
    print('For {0!r} from {1} to {2} totalling ${3:.2f}:'.format(
        bill.description,
        bill.for_dates.start,
        bill.for_dates.end,
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
