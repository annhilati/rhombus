import re

with open('rhombus/support/lithostitched/types.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('), versions=("1.6.0", ...)):', ', versions=("1.6.0", ...)):')
text = text.replace('), versions=("1.3.1", ...)):', ', versions=("1.3.1", ...)):')

with open('rhombus/support/lithostitched/types.py', 'w', encoding='utf-8') as f:
    f.write(text)
