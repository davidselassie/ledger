import unittest
from datetime import date

from ledger import calc_all_personal_costs
from ledger import House
from ledger import Person
from ledger import Bill
from ledger import DateRange


JAN_START = date(2014, 1, 1)
JAN_HALF = date(2014, 1, 16)
JAN_END = date(2014, 1, 31)
JAN_DR = DateRange(start=JAN_START, end_exclusive=JAN_END)
FIRST_HALF_JAN_DR = DateRange(start=JAN_START, end_exclusive=JAN_HALF)
SECOND_HALF_JAN_DR = DateRange(start=JAN_HALF, end_exclusive=JAN_END)


class LedgerTestCase(unittest.TestCase):
    maxDiff = None

    def test_single_person(self):
        bill = Bill(description=None, for_dates=JAN_DR, total_cost=100.0)
        person = Person(name='Bob', residencies=(JAN_DR, ))
        house = House(name=None, min_people=1, people=(person, ))

        found_pc = calc_all_personal_costs(bill, house)
        expected_pc = {person: 100.0}
        self.assertEqual(found_pc, expected_pc)

    def test_two_people(self):
        bill = Bill(description=None, for_dates=JAN_DR, total_cost=100.0)
        person1 = Person(name='Bob', residencies=(JAN_DR, ))
        person2 = Person(name='Alice', residencies=(JAN_DR, ))
        house = House(name=None, min_people=1, people=(person1, person2))

        found_pc = calc_all_personal_costs(bill, house)
        expected_pc = {person1: 50.0, person2: 50.0}
        self.assertEqual(found_pc, expected_pc)

    def test_half_and_half_person(self):
        bill = Bill(description=None, for_dates=JAN_DR, total_cost=100.0)
        person1 = Person(name='Bob', residencies=(FIRST_HALF_JAN_DR, ))
        person2 = Person(name='Alice', residencies=(SECOND_HALF_JAN_DR, ))
        house = House(name=None, min_people=1, people=(person1, person2))

        found_pc = calc_all_personal_costs(bill, house)
        expected_pc = {person1: 50.0, person2: 50.0}
        self.assertEqual(found_pc, expected_pc)

    def test_one_and_half_person(self):
        bill = Bill(description=None, for_dates=JAN_DR, total_cost=100.0)
        person1 = Person(name='Bob', residencies=(JAN_DR, ))
        person2 = Person(name='Alice', residencies=(FIRST_HALF_JAN_DR, ))
        house = House(name=None, min_people=1, people=(person1, person2))

        found_pc = calc_all_personal_costs(bill, house)
        expected_pc = {person1: 75.0, person2: 25.0}
        self.assertEqual(found_pc, expected_pc)


if __name__ == '__main__':
    unittest.main()
