"""# Rhombus Preview

The Rhombus Preview is a lightweight web application for previewing density functions
and other worldgen-related resources.

To start the preview webserver and file-watching backend use `~.serve()`.
"""

__all__ = ["serve", "resources_from_datapack"]

from rhombus.preview._service import serve, resources_from_datapack
