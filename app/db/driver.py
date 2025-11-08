# app\db\driver.py
from neo4j import AsyncGraphDatabase, AsyncDriver
from app.core.config import settings

class Neo4jDriver:
    _driver: AsyncDriver | None = None

    @classmethod
    async def get_driver(cls) -> AsyncDriver:
        if cls._driver is None:
            cls._driver = AsyncGraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_pool_size=50,
                connection_timeout=30,
                max_transaction_retry_time=30,
            )
        return cls._driver

    @classmethod
    async def close_driver(cls):
        if cls._driver is not None:
            await cls._driver.close()
            cls._driver = None

async def get_db_driver() -> AsyncDriver:
    return await Neo4jDriver.get_driver()
