from itertools import chain
import json
import sys
import os
from os import path
from pydantic import json_schema

sys.path.append("./lib/python")

from shared.utils.openapi import OpenApiMetadata, openapi_meta_key_name
import importlib.util


def get_meta_from_handler_path(filePath: str) -> OpenApiMetadata | None:
    functionFilePath = filePath.split(".", 2)[0]
    functionPath = path.relpath(filePath).replace(os.sep, ".")
    modname = ".".join(functionPath.split(".")[:-1])

    handlerFunctionName = functionPath.split(".")[-1]

    spec = importlib.util.spec_from_file_location(modname, functionFilePath + ".py")

    if spec is None:
        return None

    lambdaHandlerModule = importlib.util.module_from_spec(spec)
    sys.modules[modname] = lambdaHandlerModule

    if spec.loader:
        spec.loader.exec_module(lambdaHandlerModule)

    fn = getattr(lambdaHandlerModule, handlerFunctionName, None)

    if fn is None:
        return None

    return getattr(fn, openapi_meta_key_name, None)


if __name__ == "__main__":
    result = {path: get_meta_from_handler_path(path) for path in sys.argv[1:]}

    tags = set(
        chain.from_iterable(item.tags for item in result.values() if item is not None)
    )

    models = set(
        chain.from_iterable(
            item.responses for item in result.values() if item is not None
        )
    )

    print(
        json.dumps(
            {
                "endpoints": {
                    path: res.to_dict() if res is not None else None
                    for path, res in result.items()
                },
                "models": json_schema.models_json_schema(
                    [(model, "validation") for model in models]
                )[1],
                "tags": [tag.model_dump() for tag in tags],
            }
        )
    )
