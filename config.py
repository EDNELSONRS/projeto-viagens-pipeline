"""Project paths, CSV layout, and PostgreSQL settings."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
DATASET_ZIP = DATA_DIR / "viagens_2025_6meses.zip"
load_dotenv(ROOT_DIR / ".env")

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5432")),
    "user": os.getenv("POSTGRES_USER", "postgres"),
    "password": os.getenv("POSTGRES_PASSWORD", ""),
    "dbname": os.getenv("POSTGRES_DATABASE", "transparencia_viagens"),
}
DRIVE_FILE_ID = os.getenv("DRIVE_FILE_ID", "")
TAMANHO_BLOCO = 50_000

ARQUIVOS = {
    "2025_Viagem.csv": {
        "tabela_raw": "raw_viagem",
        "colunas_raw": [
            "id_viagem", "num_proposta", "situacao", "viagem_urgente",
            "justificativa_urgencia_viagem", "cod_orgao_superior",
            "nome_orgao_superior", "cod_orgao_solicitante",
            "nome_orgao_solicitante", "cpf_viajante", "nome_viajante",
            "cargo", "funcao", "descricao_funcao", "data_inicio", "data_fim",
            "destinos", "motivo", "valor_diarias", "valor_passagens",
            "valor_devolucao", "valor_outros_gastos",
        ],
        "cabecalho_csv": [
            "Identificador do processo de viagem", "Número da Proposta (PCDP)",
            "Situação", "Viagem Urgente", "Justificativa Urgência Viagem",
            "Código do órgão superior", "Nome do órgão superior",
            "Código órgão solicitante", "Nome órgão solicitante", "CPF viajante",
            "Nome", "Cargo", "Função", "Descrição Função",
            "Período - Data de início", "Período - Data de fim", "Destinos",
            "Motivo", "Valor diárias", "Valor passagens", "Valor devolução",
            "Valor outros gastos",
        ],
    },
    "2025_Pagamento.csv": {
        "tabela_raw": "raw_pagamento",
        "colunas_raw": [
            "id_viagem", "num_proposta", "cod_orgao_superior",
            "nome_orgao_superior", "codigo_orgao_pagador", "nome_orgao_pagador",
            "codigo_ug_pagadora", "nome_ug_pagadora", "tipo_pagamento", "valor",
        ],
        "cabecalho_csv": [
            "Identificador do processo de viagem", "Número da Proposta (PCDP)",
            "Código do órgão superior", "Nome do órgão superior",
            "Codigo do órgão pagador", "Nome do órgao pagador",
            "Código da unidade gestora pagadora", "Nome da unidade gestora pagadora",
            "Tipo de pagamento", "Valor",
        ],
    },
    "2025_Passagem.csv": {
        "tabela_raw": "raw_passagem",
        "colunas_raw": [
            "id_viagem", "num_proposta", "meio_transporte", "pais_origem_ida",
            "uf_origem_ida", "cidade_origem_ida", "pais_destino_ida",
            "uf_destino_ida", "cidade_destino_ida", "pais_origem_volta",
            "uf_origem_volta", "cidade_origem_volta", "pais_destino_volta",
            "uf_destino_volta", "cidade_destino_volta", "valor_passagem",
            "taxa_servico", "data_emissao", "hora_emissao",
        ],
        "cabecalho_csv": [
            "Identificador do processo de viagem", "Número da Proposta (PCDP)",
            "Meio de transporte", "País - Origem ida", "UF - Origem ida",
            "Cidade - Origem ida", "País - Destino ida", "UF - Destino ida",
            "Cidade - Destino ida", "País - Origem volta", "UF - Origem volta",
            "Cidade - Origem volta", "Pais - Destino volta", "UF - Destino volta",
            "Cidade - Destino volta", "Valor da passagem", "Taxa de serviço",
            "Data da emissão/compra", "Hora da emissão/compra",
        ],
    },
    "2025_Trecho.csv": {
        "tabela_raw": "raw_trecho",
        "colunas_raw": [
            "id_viagem", "num_proposta", "sequencia_trecho", "origem_data",
            "origem_pais", "origem_uf", "origem_cidade", "destino_data",
            "destino_pais", "destino_uf", "destino_cidade", "meio_transporte",
            "numero_diarias", "missao",
        ],
        "cabecalho_csv": [
            "Identificador do processo de viagem", "Número da Proposta (PCDP)",
            "Sequência Trecho", "Origem - Data", "Origem - País", "Origem - UF",
            "Origem - Cidade", "Destino - Data", "Destino - País", "Destino - UF",
            "Destino - Cidade", "Meio de transporte", "Número Diárias", "Missao?",
        ],
    },
}
