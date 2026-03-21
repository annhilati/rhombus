# Conditionality

Conditionality class.

```py

v = (
    (when(df, greater=1.0) or when(df, less=-1.0))
        .then(10.0)
    .elsewhen(between=(-0.1, 0.1))
        .then(0.0)
    .otherwise(df)
)

```