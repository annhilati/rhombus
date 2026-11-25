---
icon: lucide/parentheses
title: Style Guide
---

# Style Guide

## Style

- Headings with **two or more hashtags** (except for Google style sections).
    Should be a **process or progressive verb form** (e.g. `Creation`, `Naming`).

## Docstrings

### Variables & Attributes


### Functions

1. **Short Description**: One or few sentences about what the function does in 3rd person without pronoun.
    The first word should be the finite verb and one that is not too general, but fits the context.
    Should not mention specific fields.
2. **Details**: If needed, text with an extended explanation of the behaviour.
    May contain hyperlinks, lists, tables and code examples. 
3. **Admonitions**: Additional notices. E.g.:
    - Version restrictions with **INFO**
    - Unexpected behaviour with **NOTE**
    - Usage advice with **TIP**
    - Aspects to be cautious of with **WARNING**
3. **Parameters**: List of Parameters in the Google Style.
    ```
    Parameters:
        xz_scale (float between `0.001` and `1000.0`): Controls how often the block-like structures repeat in the XZ-plane.
        y_scale (float between `0.001` and `1000.0`): Controls how often the block-like structures repeat in the Y-axis.
        xz_factor (float between `0.001` and `1000.0`): Controls how much the small structures vary on the XZ-plane.
        y_factor (float between `0.001` and `1000.0`): Controls how much the small structures vary along the Y-axis.
        smear_scale_multiplier (float between `1.0` and `8.0`): Kinda affects how smooth the small structures are, but near to no impact on the structure.
    ```
    - **Parameter Description**:
4. **Further resources**: Under a horizontal line (`---`). Stated as hyperlinks, separated by ` • `.

## To evaluate

- allow / in single argument functions?