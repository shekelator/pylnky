from fastapi import FastAPI
import logging

from .dynamodb_setup import ensure_tables_from_yaml

logger = logging.getLogger(__name__)

app = FastAPI()


@app.on_event("startup")
def on_startup():
    """Ensure required DynamoDB tables exist when the app starts."""
    try:
        ensure_tables_from_yaml()
    except Exception:
        logger.exception("Failed to ensure DynamoDB tables on startup")


@app.get("/")
async def root():
    return {"message": "Hi worldy"}
