import json
import subprocess
from typing import Any

with open("package.json", "r") as p:
    packagejson = json.load(p)

deps: dict[str, Any] = packagejson.get("devDependencies", {})

for depName in deps.keys():
    if depName.startswith("serverless-"):
        subprocess.run(
            ["npx", "serverless", "plugin", "install", "-n", depName],
            stdin=subprocess.STD_OUTPUT_HANDLE,
            stderr=subprocess.STD_ERROR_HANDLE,
        )
