"""Baixa e valida o ZIP, depois carrega os quatro CSVs na camada Raw."""
from __future__ import annotations

import csv
import io
import sys
import zipfile
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

import gdown
import psycopg2
from gdown.exceptions import FileURLRetrievalError
from psycopg2 import sql
from requests.exceptions import RequestException

from banco import conectar
from config import ARQUIVOS, DATASET_ZIP, DRIVE_FILE_ID


def localizar_csv(arquivo: str, zf: zipfile.ZipFile) -> str:
    """Localiza um único CSV, inclusive quando há uma pasta dentro do ZIP."""
    candidatos = [
        nome for nome in zf.namelist()
        if nome.replace("\\", "/").endswith("/" + arquivo)
        or nome == arquivo
    ]
    if len(candidatos) != 1:
        raise ValueError(
            f"Esperado um arquivo {arquivo} no ZIP; "
            f"encontrados: {candidatos}"
        )
    return candidatos[0]


def validar_zip(caminho: Path) -> None:
    """Confere a integridade, os quatro membros e seus cabeçalhos."""
    with zipfile.ZipFile(caminho) as zf:
        corrompido = zf.testzip()
        if corrompido is not None:
            raise ValueError(f"Arquivo corrompido dentro do ZIP: {corrompido}")
        for arquivo, cfg in ARQUIVOS.items():
            membro = localizar_csv(arquivo, zf)
            with zf.open(membro) as raw:
                with io.TextIOWrapper(
                    raw, encoding="latin-1", newline=""
                ) as stream:
                    cabecalho = next(csv.reader(stream, delimiter=";"), None)
            if cabecalho is None or (
                [coluna.strip() for coluna in cabecalho]
                != cfg["cabecalho_csv"]
            ):
                raise ValueError(f"Cabeçalho inesperado em {arquivo}.")


def obter_zip() -> Path:
    """Publica o download no caminho definitivo somente após validá-lo."""
    if DATASET_ZIP.exists():
        validar_zip(DATASET_ZIP)
        return DATASET_ZIP
    if not DRIVE_FILE_ID:
        raise ValueError(
            f"ZIP não encontrado: {DATASET_ZIP}. "
            "Configure DRIVE_FILE_ID no .env para baixar do Drive."
        )

    DATASET_ZIP.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(
        prefix="download_viagens_", dir=DATASET_ZIP.parent
    ) as pasta:
        temporario = Path(pasta) / DATASET_ZIP.name
        resultado = gdown.download(
            id=DRIVE_FILE_ID, output=str(temporario), quiet=False,
            use_cookies=False,
        )
        if not resultado or not temporario.is_file():
            raise RuntimeError(
                "O download não produziu o ZIP. Confira DRIVE_FILE_ID, "
                "o compartilhamento do arquivo e a conexão com a internet."
            )
        validar_zip(temporario)
        temporario.replace(DATASET_ZIP)
    return DATASET_ZIP


def carregar_raw(caminho: Path) -> dict[str, int]:
    """Executa os quatro TRUNCATE/COPY em uma única transação."""
    contagens = {}
    with zipfile.ZipFile(caminho) as zf:
        with closing(conectar()) as conn:
            with conn:
                with conn.cursor() as cur:
                    for cfg in ARQUIVOS.values():
                        cur.execute(
                            sql.SQL("TRUNCATE TABLE {}").format(
                                sql.Identifier(cfg["tabela_raw"])
                            )
                        )
                    for arquivo, cfg in ARQUIVOS.items():
                        membro = localizar_csv(arquivo, zf)
                        with zf.open(membro) as raw:
                            with io.TextIOWrapper(
                                raw, encoding="latin-1", newline=""
                            ) as stream:
                                copy_sql = sql.SQL(
                                    "COPY {} ({}) FROM STDIN WITH "
                                    "(FORMAT CSV, HEADER TRUE, "
                                    "DELIMITER ';', NULL '\\N')"
                                ).format(
                                    sql.Identifier(cfg["tabela_raw"]),
                                    sql.SQL(", ").join(
                                        map(sql.Identifier, cfg["colunas_raw"])
                                    ),
                                )
                                cur.copy_expert(
                                    copy_sql.as_string(conn), stream, size=8192
                                )
                        cur.execute(
                            sql.SQL("SELECT COUNT(*) FROM {}").format(
                                sql.Identifier(cfg["tabela_raw"])
                            )
                        )
                        contagens[arquivo] = cur.fetchone()[0]
    return contagens


def main() -> int:
    try:
        caminho = obter_zip()
        contagens = carregar_raw(caminho)
    except (
        OSError, EOFError, zipfile.BadZipFile, csv.Error, psycopg2.Error,
        ValueError, RuntimeError, RequestException, FileURLRetrievalError,
    ) as exc:
        print(f"Falha na extração: {exc}", file=sys.stderr)
        return 1
    for arquivo, quantidade in contagens.items():
        print(f"{arquivo}: {quantidade:,} linhas carregadas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
