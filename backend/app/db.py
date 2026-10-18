"""MongoDB client management using Motor async driver.

This module provides the database client connection lifecycle and exposes helper
getters for the database instance and collection references.

Dependencies:
- motor.motor_asyncio
- backend.app.config
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from backend.app.config import settings

# Global motor client reference dictionary per event loop
_clients = {}


def get_client() -> AsyncIOMotorClient:
    """Returns or initializes the AsyncIOMotorClient instance for the current event loop."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    loop_key = id(loop) if loop else "default"
    if loop_key not in _clients:
        _clients[loop_key] = AsyncIOMotorClient(settings.MONGODB_URI)
    return _clients[loop_key]


def get_database():
    """Returns the MongoDB database instance for network_portal."""
    cli = get_client()
    return cli[settings.MONGODB_DB_NAME]


def close_db_client():
    """Closes all MongoDB motor client connections during application shutdown."""
    for cli in _clients.values():
        cli.close()
    _clients.clear()
