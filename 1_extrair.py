"""Load the four source CSVs into Raw with PostgreSQL COPY."""
from __future__ import annotations

import csv
import sys
import zipfile

import psycopg2
from psycopg2 import sql

from banco import conectar
from config import ARQUIVOS, DATASET_ZIP, DRIVE_FILE_ID


def localizar_csv(arquivo: str, zf: zipfile.ZipFile) -> str:
    candidatos = [n for n in zf.namelist() if n.replace("\\", "/").endswith("/" + arquivo) or n == arquivo]
    if len(candidatos) != 1:
        raise ValueError(f"Esperado um arquivo {arquivo} no ZIP; encontrados: {candidatos}")
    return candidatos[0]


def main() -> None:
    if not DATASET_ZIP.exists():
        if not DRIVE_FILE_ID:
            raise SystemExit(f"ZIP não encontrado: {DATASET_ZIP}. Configure DRIVE_FILE_ID para baixar do Drive.")
        import gdown
        DATASET_ZIP.parent.mkdir(parents=True, exist_ok=True)
        gdown.download(id=DRIVE_FILE_ID, output=str(DATASET_ZIP), quiet=False)
    try:
        with zipfile.ZipFile(DATASET_ZIP) as zf, conectar() as conn:
            with conn.cursor() as cur:
                for cfg in ARQUIVOS.values():
                    cur.execute(sql.SQL("TRUNCATE TABLE {}").format(sql.Identifier(cfg["tabela_raw"])))
                for arquivo, cfg in ARQUIVOS.items():
                    member = localizar_csv(arquivo, zf)
                    with zf.open(member) as raw, __import__("io").TextIOWrapper(raw, encoding="latin-1", newline="") as stream:
                        header = next(csv.reader(stream, delimiter=";"))
                        if [x.strip() for x in header] != cfg["cabecalho_csv"]:
                            raise ValueError(f"Cabeçalho inesperado em {arquivo}: {header}")
                        stream.seek(0)
                        copy_sql = sql.SQL("COPY {} ({}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE, DELIMITER ';', NULL '\\N')").format(
                            sql.Identifier(cfg["tabela_raw"]),
                            sql.SQL(", ").join(map(sql.Identifier, cfg["colunas_raw"])),
                        )
                        cur.copy_expert(copy_sql.as_string(conn), stream)
                    cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(cfg["tabela_raw"])))
                    print(f"{arquivo}: {cur.fetchone()[0]:,} linhas carregadas")
    except (OSError, zipfile.BadZipFile, psycopg2.Error, ValueError) as exc:
        print(f"Falha na extração: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
