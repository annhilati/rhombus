# Conditionality

```py

v = (
    (when(df, greater=1.0) or when(df, less=-1.0))
        .then(10.0)
    .elsewhen(between=(-0.1, 0.1))
        .then(0.0)
    .otherwise(df)
)

```

Condition -> Causality -> Density
Condition -> Causality -> Condition+ -> Causality+ -> Density

Causality
    *(
        Condition
        DensityDescriptor
    )