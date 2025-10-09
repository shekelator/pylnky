import os
import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeDeserializer
from pydantic import BaseModel, HttpUrl

logger = logging.getLogger(__name__)


class URLItem(BaseModel):
    """Pydantic model representing an item stored in the `URLs` table.

    Assumption: the table stores the original destination in the attribute named
    `url` (string). If your table uses a different attribute name, update the
    code or pass a custom deserialized mapping into the model.
    """

    short_id: str
    url: HttpUrl


# Notes:
# - Environment variables respected: DYNAMODB_ENDPOINT, AWS_REGION
# - The default table name is 'URLs' but can be overridden via URLS_TABLE env var


def _get_dynamodb_client() -> boto3.client:
    """Create a boto3 DynamoDB client honoring environment overrides.

    Uses the same `DYNAMODB_ENDPOINT` and `AWS_REGION` convention used
    elsewhere in the project.
    """
    endpoint = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:4566")
    return boto3.client(
        "dynamodb",
        region_name=os.getenv("AWS_REGION"),
        endpoint_url=endpoint,
    )


def _deserialize_dynamodb_item(item: dict) -> dict:
    """Convert a DynamoDB item (with DynamoDB types) to plain Python types.

    Uses boto3's TypeDeserializer which supports common DynamoDB types.
    """
    deserializer = TypeDeserializer()
    return {k: deserializer.deserialize(v) for k, v in item.items()}


def redirect(short_code: str, *, dynamodb_client: Optional[boto3.client] = None, table_name: Optional[str] = None) -> str:
    """Return the original URL for the given short code by reading the `URLs` table.

    Args:
        short_code: the short identifier stored as `short_id` in DynamoDB.
        dynamodb_client: optional boto3 client (for testing/injection).
        table_name: optional table name (defaults to 'URLs').

    Returns:
        The full destination URL as a string.

    Raises:
        ValueError: if the short code does not exist in the table.
        botocore.exceptions.ClientError: for unexpected AWS errors.
    """
    if not short_code:
        raise ValueError("short_code must be a non-empty string")

    client = dynamodb_client or _get_dynamodb_client()
    table = table_name or os.getenv("URLS_TABLE", "URLs")

    try:
        resp = client.get_item(TableName=table, Key={"short_id": {"S": short_code}})
    except ClientError:
        logger.exception("Error fetching short code %s from table %s", short_code, table)
        raise

    item = resp.get("Item")
    if not item:
        raise ValueError(f"Short code not found: {short_code}")

    data = _deserialize_dynamodb_item(item)

    # Validate/parse with pydantic model
    url_item = URLItem(**data)
    return str(url_item.url)


__all__ = ["redirect", "URLItem"]
