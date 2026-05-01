from contextvars import ContextVar
import beet, warnings

infinitesimal = 1/10000000

class ctx:

    datapack: ContextVar[beet.DataPack | None] = ContextVar("datapack", default=None)
    

def warn(message, category, filename, lineno, file=None, line=None):
    print(
        f"\033[38;2;220;150;80mRhombus Warning\n"
        f"╰─×\033[0m {message}\n"
    )

warnings.showwarning = warn
