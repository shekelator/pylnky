# pylnky
Python version of lnky

### Resources
- [Using uv with FastAPI](https://docs.astral.sh/uv/guides/integration/fastapi/#migrating-an-existing-fastapi-project)
- 
## DynamoDB table auto-creation

On startup the FastAPI app will attempt to ensure DynamoDB tables defined in `dynamodb-tables.yaml` exist. It uses `boto3` and `PyYAML`.

Environment variables respected:
- AWS_REGION (recommended)
- AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY for credentials

If you run a local DynamoDB-compatible endpoint (for example LocalStack), set the environment variable `AWS_ENDPOINT_URL` and modify `dynamodb_setup.py` to pass it to the boto3 client (or set endpoint via standard boto3 environment config).

If a table already exists it will be left intact.

## Running LocalStack with docker-compose

A reproducible LocalStack setup is included via `docker-compose.yml`. To start LocalStack (DynamoDB only):

```bash
docker compose up -d
```

Wait for the healthcheck to pass. You can follow logs with:

```bash
docker compose logs -f localstack
```

## Running tests against LocalStack

1. Start LocalStack (see above).
2. Export environment variables so the code and tests use LocalStack:

```bash
export DYNAMODB_ENDPOINT="http://localhost:4566"
export AWS_REGION="us-east-1"
export AWS_ACCESS_KEY_ID="test"
export AWS_SECRET_ACCESS_KEY="test"
```

3. Install dev dependencies and run tests:

```bash
uv run pytest
```

The test suite will skip the LocalStack test if the LocalStack endpoint is not reachable on `localhost:4566`. If you want the tests to fail instead of skipping, remove the skip condition in `tests/test_dynamodb_setup.py`.

## Running application "locally"

```
uv run fastapi dev
```

## Deployment instructions

TODO
