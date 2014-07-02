housecash
=========
Tool for splitting up house expenses.

Usage
-----
Run `python ledger.py HOUSE_YAML` to split up a list of expenses.

This will figure out who owes what fraction of each expense and output the split. There are a few types of expenses you can log.

Expense Types
-------------
### Bills
Each bill is split evenly amongst all of the people in the house, based on the fraction of the time of the bill that they were in residence. A bill can also be for a single moment in time, in which case it's shared amongst all people who live in the house that day equally.

If person A is in residence the entire duration of a bill, and person B is there only half of the bills time, person A will owe 3/4ths of it and person B 1/4th.

### Shared Costs
Shared costs are split evenly amongst a set list of people.

### Payments
Payments log the transfer of money from one person to another. You use them to pay off dues.

House Definition
----------------
A house has a `name`, a `min_people` that it should contain, and a list of `people` who have lived there.

You'll get an error if you try to split up a bill between fewer people than the house is supposed to contain.

### Person
A person has a `name` and a list of `residencies` which are each a date range. Each residency is a contiguous block of time that they've lived there. If they go away for a summer, they have two residencies: before they left and after they've returned.

### Date Range
A date range describes a time span. It always has a `start`. It might have an `end`, but could be unbounded into the future. It's also possible, for convenience, to specify the end date as the first day that's _not_ in the range via `end_exclusive`.

It's possible to specify the entire month of January 2014 by either of the following
```yaml
start: 2014-01-01
end: 2014-01-31

start: 2014-01-01
end_exclusive: 2014-02-01
```

### Example House
```yaml
house:
  name: Housetub
  min_people: 3
  people:
    - name: David
      residencies:
        - start: 2013-09-01
          end_exclusive: 2014-09-01
    - name: Stubbs
      residencies:
        - start: 2013-08-01
          end: 2014-05-23
        - start: 2014-08-06
```

Expense Definitions
-------------------
Expenses are listed in a `ledger` in the house YAML.

### Bills
Each bill has a `description`, the name of the person `paid_by`, an `amount` in dollars, and `for_dates` which is a single date range or `on_date` which is a single day.

```yaml
bill:
  - description: Garbage
    paid_by: Stubbs
    amount: 178.08
    for_dates:
      start: 2014-03-31
      end: 2014-06-14
```

### Shared Costs
Each shared cost has a `description`, the name of the person `paid_by`, an `amount` in dollars, and `on_date` which is a single day, and a list of names of people the cost was `shared_amongst`.

```yaml
shared_cost:
  - description: Dinner
    paid_by: David
    total_cost: 51.00
    shared_amongst: [David, Stubbs]
    on_day: 2014-04-15
```

### Payment
Each payment has the name of the `payer`, the name of the person paid `to`, the `amount`, and the `on_date` it was paid.

```yaml
payment:
  - payer: David
    to: Stubbs
    total_cost: 10.00
    on_day: 2014-04-15
```
