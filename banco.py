"""PostgreSQL helpers used by the pipeline scripts and notebook."""
from __future__ import annotations

import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL

from config import POSTGRES_CONFIG


def conectar(database: str | None = None):
    """Open a psycopg2 connection to the project database."""
    settings = POSTGRES_CONFIG.copy()
    if database:
        settings["dbname"] = database
    if not settings["password"]:
        raise RuntimeError("Defina POSTGRES_PASSWORD no arquivo .env antes de conectar.")
    return psycopg2.connect(**settings)


def motor(database: str | None = None) -> Engine:
    """Create a SQLAlchemy engine with safely escaped credentials."""
    settings = POSTGRES_CONFIG.copy()
    if database:
        settings["dbname"] = database
    if not settings["password"]:
        raise RuntimeError("Defina POSTGRES_PASSWORD no arquivo .env antes de conectar.")
    url = URL.create(
        "postgresql+psycopg2",
        username=settings["user"], password=settings["password"],
        host=settings["host"], port=settings["port"], database=settings["dbname"],
    )
    return create_engine(url, pool_pre_ping=True)
