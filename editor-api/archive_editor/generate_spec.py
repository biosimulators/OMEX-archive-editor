import json
import os

import yaml
from fastapi.openapi.utils import get_openapi

from archive_editor.main import app


def main():
    openapi_spec = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )

    # Convert the JSON OpenAPI spec to YAML
    openapi_spec_yaml = yaml.dump(json.loads(json.dumps(openapi_spec)), sort_keys=False)

    current_directory = os.path.dirname(os.path.realpath(__file__))

    # Write the YAML OpenAPI spec to a file in subdirectory spec
    specs_dir = f"{current_directory}/specs"
    if not os.path.exists(specs_dir):
        os.mkdir(specs_dir)

    yaml_fp = f"{specs_dir}/openapi_{app.openapi_version.replace('.', '_')}_generated_spec.yaml"
    if os.path.exists(yaml_fp):
        os.remove(yaml_fp)
        print('Old spec removed!')

    with open(yaml_fp, "w") as f:
        f.write(openapi_spec_yaml)
        print('New spec written!')


if __name__ == "__main__":
    main()
