from pathlib import Path
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
import subprocess


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str]):
        """
        Runs the npm install and build commands for the frontend before the python build process begins.
        This ensures that the latest compiled frontend assets are available.
        """

        frontend = Path(__file__).parent / "rhombus-preview"

        subprocess.run("npm install", cwd=frontend, shell=True, check=True)

        subprocess.run("npm run build", cwd=frontend, shell=True, check=True)
