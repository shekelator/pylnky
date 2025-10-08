import os
import socket
import sys
import pytest

# Make the project root importable for tests (allow importing dynamodb_setup)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import dynamodb_setup


def is_port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


@pytest.mark.skipif(
    not is_port_open("localhost", 4566),
    reason="LocalStack not available on localhost:4566",
)
def test_ensure_tables_localstack(tmp_path, monkeypatch):
    # Use the repo's YAML file
    yaml_path = os.path.join(os.path.dirname(__file__), "..", "dynamodb-tables.yaml")
    yaml_path = os.path.abspath(yaml_path)

    # Ensure DYNAMODB_ENDPOINT points to localstack
    monkeypatch.setenv("DYNAMODB_ENDPOINT", "http://localhost:4566")

    table_defs = dynamodb_setup.load_table_definitions(yaml_path)

    # Run ensure_tables which will call the localstack endpoint
    dynamodb_setup.ensure_tables(table_defs)

    # After creation, describe the tables to verify
    import boto3

    client = boto3.client("dynamodb", endpoint_url=os.environ["DYNAMODB_ENDPOINT"], region_name=os.getenv("AWS_REGION"))
    for logical_name, resource in table_defs.items():
        table_name = resource.get("Properties", {}).get("TableName")
        assert table_name
        resp = client.describe_table(TableName=table_name)
        assert resp["Table"]["TableName"] == table_name
