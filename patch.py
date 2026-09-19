import re

with open('rhombus/support/moredfs/types.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('), versions=("2.2.0", ...)):', ', versions=("2.2.0", ...)):')

with open('rhombus/support/moredfs/types.py', 'w', encoding='utf-8') as f:
    f.write(text)
