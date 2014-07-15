import unittest
from datetime import date

from ledger import dues_for_bill
from ledger import dues_for_payment
from ledger import dues_for_shared_cost
from ledger import House
from ledger import Person
from ledger import Bill
from ledger import DateRange
from ledger import Payment
from ledger import SharedCost
from ledger import SHARED_AMONGST_EVERYONE


JAN_START = date(2014, 1, 1)
JAN_HALF = date(2014, 1, 16)
JAN_END = date(2014, 1, 31)
JAN_DR = DateRange(start=JAN_START, end_exclusive=JAN_END)
FIRST_HALF_JAN_DR = DateRange(start=JAN_START, end_exclusive=JAN_HALF)
SECOND_HALF_JAN_DR = DateRange(start=JAN_HALF, end_exclusive=JAN_END)


class BillTestCase(unittest.TestCase):
    maxDiff = None

    def test_single_person(self):
        bill = Bill(description=None, for_dates=JAN_DR, amount=100.0, paid_by='Bob', paid_on_date=None)
        person = Person(name='Bob', residencies=(JAN_DR, ))
        house = House(name=None, min_people=1, people=(person, ))

        found_pc = dues_for_bill(bill, house)
        expected_pc = {'Bob': 0.0}
        self.assertEqual(found_pc, expected_pc)

    def test_two_people(self):
        bill = Bill(description=None, for_dates=JAN_DR, amount=100.0, paid_by='Bob', paid_on_date=None)
        person1 = Person(name='Bob', residencies=(JAN_DR, ))
        person2 = Person(name='Alice', residencies=(JAN_DR, ))
        house = House(name=None, min_people=1, people=(person1, person2))

        found_pc = dues_for_bill(bill, house)
        expected_pc = {'Bob': -50.0, 'Alice': 50.0}
        self.assertEqual(found_pc, expected_pc)

    def test_half_and_half_person(self):
        bill = Bill(description=None, for_dates=JAN_DR, amount=100.0, paid_by='Bob', paid_on_date=None)
        person1 = Person(name='Bob', residencies=(FIRST_HALF_JAN_DR, ))
        person2 = Person(name='Alice', residencies=(SECOND_HALF_JAN_DR, ))
        house = House(name=None, min_people=1, people=(person1, person2))

        found_pc = dues_for_bill(bill, house)
        expected_pc = {'Bob': -50.0, 'Alice': 50.0}
        self.assertEqual(found_pc, expected_pc)

    def test_one_and_half_person(self):
        bill = Bill(description=None, for_dates=JAN_DR, amount=100.0, paid_by='Bob', paid_on_date=None)
        person1 = Person(name='Bob', residencies=(JAN_DR, ))
        person2 = Person(name='Alice', residencies=(FIRST_HALF_JAN_DR, ))
        house = House(name=None, min_people=1, people=(person1, person2))

        found_pc = dues_for_bill(bill, house)
        expected_pc = {'Bob': -25.0, 'Alice': 25.0}
        self.assertEqual(found_pc, expected_pc)


class SharedCostTestCase(unittest.TestCase):
    maxDiff = None

    def test_explicit_split(self):
        shared = SharedCost(
            description=None,
            paid_by='Bob',
            on_date=JAN_START,
            shared_amongst=frozenset(('Bob', 'Alice')),
            amount=100.0,
        )

        found_pc = dues_for_shared_cost(shared, None)
        expected_pc = {'Bob': -50.0, 'Alice': 50.0}
        self.assertEqual(found_pc, expected_pc)

    def test_residence_split(self):
        shared = SharedCost(
            description=None,
            paid_by='Bob',
            on_date=JAN_START,
            shared_amongst=SHARED_AMONGST_EVERYONE,
            amount=100.0,
        )
        person1 = Person(name='Bob', residencies=(JAN_DR, ))
        person2 = Person(name='Alice', residencies=(FIRST_HALF_JAN_DR, ))
        person3 = Person(name='Dan', residencies=(SECOND_HALF_JAN_DR, ))
        house = House(name=None, min_people=1, people=(person1, person2, person3))

        found_pc = dues_for_shared_cost(shared, house)
        expected_pc = {'Bob': -50.0, 'Alice': 50.0}
        self.assertEqual(found_pc, expected_pc)


class PaymentsTestCase(unittest.TestCase):
    maxDiff = None

    def test_payment(self):
        payment = Payment(payer='Bob', to='Alice', amount=100.0, on_date=JAN_START)

        found_pc = dues_for_payment(payment)
        expected_pc = {'Bob': -100.0, 'Alice': 100.0}
        self.assertEqual(found_pc, expected_pc)


if __name__ == '__main__':
    unittest.main()
