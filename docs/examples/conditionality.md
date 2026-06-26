---
title: Conditionality
icon: 
---

### Chosing density based of the height
```py
from rhombus import *
from rhombus.macros.conditional import when

y = coords.y()

islands_FINAL = cache_once(
    when(y).atleast_but_less(-64.0, 0.0).then(
        max(
            layer_depth_bottom(1),
            layer_depth_bottom(2)
        )
    ).elsewhen(y).atleast_but_less(0.0, 48.0).then(
        max(
            layer_depth_top(1),
            layer_depth_bottom(2),
            layer_depth_bottom(3)
        )
    ).elsewhen(y).atleast_but_less(48.0, 96.0).then(
        max(
            layer_depth_top(1),
            layer_depth_top(2),
            layer_depth_bottom(3),
            layer_depth_bottom(4)
        )
    ).elsewhen(y).atleast_but_less(96.0, 144.0).then(
        max(
            layer_depth_top(2),
            layer_depth_top(3),
            layer_depth_bottom(4),
            layer_depth_bottom(5)
        )
    ).elsewhen(y).atleast_but_less(144.0, 192.0).then(
        max(
            layer_depth_top(3),
            layer_depth_top(4),
            layer_depth_bottom(5)
        )
    ).elsewhen(y).atleast_but_less(192.0, 256.0).then(
        max(
            layer_depth_top(4),
            layer_depth_top(5)
        )
    ).otherwise(
        -0.1
    )
)
```