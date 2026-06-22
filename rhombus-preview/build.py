from pathlib import Path
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
import subprocess

class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str]):
        """
        Runs the npm install and build commands for the frontend before the python build process begins.
        This ensures that the latest compiled frontend assets are available.
        """
        
        frontend = Path(__file__).parent
        
        subprocess.run(
            ["cmd", "/c", "npm", "install"],
            cwd=frontend,
            check=True
        )

        subprocess.run(
            ["cmd", "/c", "npm", "run", "build"],
            cwd=frontend,
            check=True
        )