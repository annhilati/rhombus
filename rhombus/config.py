from contextvars import ContextVar
import beet, warnings

infinitesimal = 1e-16

class ctx:

    datapack: ContextVar[beet.DataPack | None] = ContextVar("datapack", default=None)
    deserialize_reference_with_content: ContextVar[bool] = ContextVar("deserialize_reference_with_content", default=False)
    caching_function_types: ContextVar[frozenset] = ContextVar("caching_function_types", default=frozenset())

# TODO: Implement an addon system that manages all kinds of registries 

def warn(message, category, filename, lineno, file=None, line=None):
    print(
        f"\033[38;2;220;150;80mRhombus Warning\n"
        f"╰─×\033[0m {message}\n"
    )

warnings.showwarning = warn
