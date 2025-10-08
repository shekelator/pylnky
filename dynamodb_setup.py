import os
import yaml
import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def load_table_definitions(path: str):
    """Load DynamoDB table definitions from a CloudFormation-like YAML file.

    Returns the Resources dict from the YAML.
    """
    with open(path, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    return doc.get("Resources", {})


def ensure_tables(table_defs, dynamodb=None):
    """Ensure DynamoDB tables described in table_defs exist.

    table_defs: mapping of logical name -> resource definition
    dynamodb: optional boto3 DynamoDB client or resource (if None, a client is created)
    """
    if dynamodb is None:
        # Allow overriding the endpoint for local testing (LocalStack).
        endpoint = os.getenv("DYNAMODB_ENDPOINT", "http://localhost:4566")
        dynamodb = boto3.client(
            "dynamodb",
            region_name=os.getenv("AWS_REGION"),
            endpoint_url=endpoint,
        )

    for logical_name, resource in table_defs.items():
        props = resource.get("Properties", {})
        table_name = props.get("TableName")
        if not table_name:
            logger.warning("Skipping resource %s: no TableName", logical_name)
            continue

        # Check if table exists
        try:
            dynamodb.describe_table(TableName=table_name)
            logger.info("Table '%s' already exists", table_name)
            continue
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code != "ResourceNotFoundException":
                logger.exception("Error describing table %s", table_name)
                raise

        # Build CreateTable params
        params = {"TableName": table_name}

        billing = props.get("BillingMode")
        if billing:
            params["BillingMode"] = billing

        if billing != "PAY_PER_REQUEST":
            # Optionally support ProvisionedThroughput if provided
            pt = props.get("ProvisionedThroughput")
            if pt:
                params["ProvisionedThroughput"] = pt

        attr_defs = props.get("AttributeDefinitions")
        if attr_defs:
            # Convert to boto3 format (same shape)
            params["AttributeDefinitions"] = attr_defs

        key_schema = props.get("KeySchema")
        if key_schema:
            params["KeySchema"] = key_schema

        # GlobalSecondaryIndexes, LocalSecondaryIndexes, etc. (pass-through)
        for idx_key in ("GlobalSecondaryIndexes", "LocalSecondaryIndexes"):
            if props.get(idx_key):
                params[idx_key] = props[idx_key]

        logger.info("Creating table %s with params: %s", table_name, {k: v for k, v in params.items() if k != 'AttributeDefinitions'})

        try:
            dynamodb.create_table(**params)
            waiter = dynamodb.get_waiter("table_exists")
            waiter.wait(TableName=table_name)
            logger.info("Created table '%s'", table_name)
        except ClientError:
            logger.exception("Failed to create table %s", table_name)
            raise


def ensure_tables_from_yaml(path: str = "dynamodb-tables.yaml"):
    table_defs = load_table_definitions(path)
    ensure_tables(table_defs)
