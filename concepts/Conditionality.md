# Conditionality

Conditionality class.

## Type 1a
```py
v = when(d, above=10.0).then(1).otherwise(0)
```
- typing should be difficult if not all types with None

## Type 1b
```py
v = when(d, ">", 10.0).then(1).otherwise(0)
```
- looks weird, because of the string

## Type 1c

```py
v = when(d > 10.0).then(1).otherwise(0)
```
- `d in (0, 1)` couldn't work because `__contains__` is defined for `tuple`

## Type 2

```py
v = when(d).above(10.0).then(1).otherwise(0)
```
- very flexible