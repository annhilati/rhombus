from contextvars import ContextVar
import beet, warnings

constant_number_limit = 1_000_000
warn_on_reference_in_clamp = True


datapack_context: ContextVar[beet.DataPack | None] = ContextVar("datapack_context", default=None)


def warn(message, category, filename, lineno, file=None, line=None):
    print(
        f"\033[38;2;220;150;80mRhombus Warning\n"
        f"╰─×\033[0m {message}\n"
    )

warnings.showwarning = warn