import os
import socket
import sys
import pytest

# Make project importable
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
def test_redirect_localstack(tmp_path, monkeypatch):
    # Ensure DYNAMODB_ENDPOINT points to localstack
    monkeypatch.setenv("DYNAMODB_ENDPOINT", "http://localhost:4566")

    # Load table definitions and ensure tables exist
    yaml_path = os.path.join(os.path.dirname(__file__), "..", "dynamodb-tables.yaml")
    yaml_path = os.path.abspath(yaml_path)
    table_defs = dynamodb_setup.load_table_definitions(yaml_path)
    dynamodb_setup.ensure_tables(table_defs)

    # Put an item in the URLs table
    import boto3

    client = boto3.client("dynamodb", endpoint_url=os.environ["DYNAMODB_ENDPOINT"], region_name=os.getenv("AWS_REGION"))
    short_id = "test123"
    dest = "https://example.test/long"
    client.put_item(TableName="URLs", Item={"short_id": {"S": short_id}, "url": {"S": dest}})

    # Now import shorten and call redirect
    import shorten

    got = shorten.redirect(short_id)
    assert got == dest


@pytest.mark.skipif(
    not is_port_open("localhost", 4566),
    reason="LocalStack not available on localhost:4566",
)
def test_redirect_not_found(monkeypatch):
    monkeypatch.setenv("DYNAMODB_ENDPOINT", "http://localhost:4566")
    import shorten

    with pytest.raises(ValueError):
        shorten.redirect("this-does-not-exist-xyz")
