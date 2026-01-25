constant_number_limit = 1_000_000
warn_on_reference_in_clamp = True

import warnings as _warnings
def warn(message, category, filename, lineno, file=None, line=None):
    print(
        f"\033[38;2;220;150;80mRhombus Warning\n"
        f"╰─×\033[0m {message}\n"
    )

_warnings.showwarning = warn