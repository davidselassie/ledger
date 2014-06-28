housecash
=========
Tool for spliting up house bills.

Usage
-----
Run `python split_bills.py HOUSE_YAML BILLS_YAML` to split up a list of bills.

This will figure out who owes what fraction of each bill and output the split. Each bill is split evenly amongs all of the people in the house, based on the fraction of the time of the bill that they were in residence. If person A is in residence the entire duration of a bill, and person B is there only half of the bills time, person A will owe 3/4ths of it and person B 1/4th.

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

Bill Definition
---------------
The bill YAML is a list of bills. Each bill has a `description`, a `total_cost` in dollars, and `for_dates` which is a single date range.

### Example Bills
```yaml
bills:
  - description: Garbage
    total_cost: 178.08
    for_dates:
      start: 2014-03-31
      end: 2014-06-14
```
