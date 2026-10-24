"""Cria o banco dedicado e inicializa as tabelas Raw e Silver."""
from __future__ import annotations

import psycopg2
from psycopg2 import sql

from config import POSTGRES_CONFIG, ROOT_DIR


def main() -> None:
    settings = POSTGRES_CONFIG.copy()
    database = settings.pop("dbname")

    if not settings["password"]:
        raise SystemExit("Defina POSTGRES_PASSWORD no arquivo .env.")

    # CREATE DATABASE precisa ser executado fora de uma transação.
    admin = psycopg2.connect(dbname="template1", **settings)
    admin.autocommit = True
    try:
        with admin.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (database,),
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    sql.SQL("CREATE DATABASE {} TEMPLATE template0").format(
                        sql.Identifier(database)
                    )
                )
    finally:
        admin.close()

    with psycopg2.connect(dbname=database, **settings) as conn:
        with conn.cursor() as cursor:
            arquivo_sql = ROOT_DIR / "0_criar_banco.sql"
            cursor.execute(arquivo_sql.read_text(encoding="utf-8-sig"))

    print(f"Banco {database!r} pronto com as tabelas Raw e Silver.")


if __name__ == "__main__":
    main()