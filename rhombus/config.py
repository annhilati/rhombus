from contextvars import ContextVar
from collections import OrderedDict
import beet, warnings

infinitesimal = 1e-8

class ctx:

    datapack: ContextVar[beet.DataPack | None] = ContextVar("datapack", default=None)
    deserialize_reference_with_content: ContextVar[bool] = ContextVar("deserialize_reference_with_content", default=False)

    

def warn(message, category, filename, lineno, file=None, line=None):
    print(
        f"\033[38;2;220;150;80mRhombus Warning\n"
        f"╰─×\033[0m {message}\n"
    )

warnings.showwarning = warn
