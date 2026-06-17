import subprocess
from hatchling.builders.hooks.plugin.interface import BuildHookInterface

class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        subprocess.run(
            ["npm", "install"],
            cwd="rhombus-preview",
            check=True
        )

        subprocess.run(
            ["npm", "run", "build"],
            cwd="rhombus-preview",
            check=True
        )