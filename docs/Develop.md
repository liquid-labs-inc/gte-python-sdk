# Developer Guide

## Codegen

I use https://github.com/OpenAPITools/openapi-generator and copied(with some changes) the files into our
gte_py.api.openapi module.
However, this implementation is a bit cumbersome, so the old gte_py.api.rest is still in use

### OpenAPI Code Generation

The project uses OpenAPI Generator CLI to generate Python client code from the OpenAPI specification. The process is automated through the `scripts/generate_rest_api.sh` script.

#### Prerequisites

- Node.js and npm installed (for OpenAPI Generator CLI)
- The `docs/openapi.yaml` specification file must be up to date

#### Generation Process

1. Install the OpenAPI Generator CLI globally if not already installed:
   ```bash
   npm install -g @openapitools/openapi-generator-cli
   ```

2. Run the generation script:
   ```bash
   ./scripts/generate_rest_api.sh
   ```

The script performs the following actions:
- Creates a temporary directory for generated files
- Generates a Python client from the OpenAPI specification
- Copies the generated files to `src/gte_py/api/openapi/`
- Updates import paths from `openapi_client` to `gte_py.api.openapi`
- Runs linting and formatting on the generated code
- Cleans up temporary files

#### Customizing the Generated Code

If you need to modify the generated OpenAPI client:
1. Update the `docs/openapi.yaml` specification
2. Re-run the generation script
3. If custom changes are needed beyond what OpenAPI Generator provides, make them directly in the `src/gte_py/api/openapi/` directory

Note that regenerating the API client will overwrite any custom changes, so document any manual modifications carefully.

#### API Implementation Alternatives

The project maintains two API implementations:
- `api/openapi/`: The auto-generated OpenAPI client
- `api/rest/`: A custom implementation that may be more suitable for certain use cases

When developing new features, consider which API implementation best fits your requirements.