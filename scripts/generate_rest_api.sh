#!/bin/bash -xe
echo "Using https://github.com/OpenAPITools/openapi-generator-cli"
if [ ! -d "openapi-generator-cli" ]; then
  npm install -g @openapitools/openapi-generator-cli
fi

TEMP_REST_API_CLIENT_DIR=temp_gte_api_client
echo "generate rest api client"
rm -rf $TEMP_REST_API_CLIENT_DIR || true
mkdir -p $TEMP_REST_API_CLIENT_DIR
(cd $TEMP_REST_API_CLIENT_DIR && openapi-generator-cli generate -i ../docs/openapi.yaml -g python)
rm -rf src/gte_py/api/openapi | true
mkdir -p src/gte_py/api/openapi
cp -r $TEMP_REST_API_CLIENT_DIR/openapi_client/* src/gte_py/api/openapi/

echo "replace openapi_client with gte_py.api.openapi"
find src/gte_py/api/openapi -type f -name "*.py" -exec sed -i 's/openapi_client/gte_py.api.openapi/g' {} \;
echo "cleanup"
rm -rf $TEMP_REST_API_CLIENT_DIR || true

uv run ruff check src/gte_py/api/openapi || true
uv run ruff format src/gte_py/api/openapi
echo "done"