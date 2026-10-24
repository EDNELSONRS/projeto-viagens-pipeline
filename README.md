# Análise de despesas com viagens a serviço

Projeto avaliativo de Análise de Dados com Python. O objetivo é transformar dados de viagens a serviço do Governo Federal em informações sobre custos, destinos, duração, pagamentos e meios de transporte.

O pipeline utiliza Python e PostgreSQL e segue a arquitetura Medallion: Raw, Silver e Gold.

## Tecnologias

Python 3.10 ou superior, PostgreSQL 13 ou superior, pandas, psycopg2, SQLAlchemy, python-dotenv, gdown, Matplotlib, Seaborn e Jupyter Notebook no VS Code.

## Fonte dos dados

A base fornecida para a atividade contém viagens iniciadas entre janeiro e junho de 2025. O ZIP deve conter `2025_Viagem.csv`, `2025_Pagamento.csv`, `2025_Passagem.csv` e `2025_Trecho.csv`.

Os CSVs usam separador `;`, codificação Latin-1, vírgula decimal e datas no formato `DD/MM/AAAA`.

[Arquivo de dados no Google Drive](https://drive.google.com/file/d/1pQjKacyHdIsyteknQbwKGM5_4hL5V4RV/view?usp=drive_link)

O ID utilizado para download é `1pQjKacyHdIsyteknQbwKGM5_4hL5V4RV`. O arquivo precisa estar disponível para o gdown; o pipeline não implementa login na conta Google. Se o acesso estiver restrito, solicite ao responsável pela base um compartilhamento que permita o download.

## Organização

| Arquivo | Finalidade |
|---|---|
| `0_criar_banco.py` | Cria o banco dedicado e executa o SQL. |
| `0_criar_banco.sql` | Define quatro tabelas Raw e quatro Silver. |
| `1_extrair.py` | Obtém o ZIP quando necessário e carrega a Raw. |
| `2_transformar.py` | Converte os dados e popula a Silver. |
| `3_analise.ipynb` | Cria os objetos Gold e apresenta análises e gráficos. |
| `config.py` e `banco.py` | Centralizam a configuração e as conexões. |
| `.env.example` | Modelo de configuração sem senha real. |
| `.gitignore` | Define os arquivos locais que não devem ser versionados. |
| `requirements.txt` | Lista as dependências. |
| `gerar_notebook.py` | Utilitário opcional que recria o notebook. |

A pasta `data/`, o arquivo `.env` e o ambiente `.venv` são locais. Executar `gerar_notebook.py` novamente pode substituir as saídas salvas do notebook; ele não é necessário para usar o pipeline.

## Etapas do pipeline

### Raw

As tabelas Raw preservam todas as colunas dos CSVs como `VARCHAR`, sem restrições. `1_extrair.py` procura `data/viagens_2025_6meses.zip`. Se esse arquivo não existe, utiliza o `DRIVE_FILE_ID` do `.env` para baixá-lo.

Antes de conectar ao banco, o script confere a integridade do ZIP, a presença de um único CSV de cada tipo e seus cabeçalhos. Essa validação também ocorre quando o ZIP já existe na pasta `data/`.

Quando precisa baixar a base, o script utiliza o ID do Drive sem login ou cookies. O download fica em uma pasta temporária e só é publicado como `data/viagens_2025_6meses.zip` após a validação. Em caso de falha, o temporário da execução é removido.

Os CSVs são transmitidos ao PostgreSQL por COPY, com buffer de leitura configurado em 8192, sem carregar os arquivos inteiros em memória. Os quatro TRUNCATE e COPY ocorrem em uma única transação. Se uma carga falhar, a transação é revertida; as mensagens de sucesso só são exibidas após a confirmação da carga completa. A conexão é fechada ao final.

Falhas previstas de rede, acesso ao Drive, arquivo, estrutura dos CSVs ou banco são tratadas com uma mensagem `Falha na extração` e código de saída 1. Após corrigir a causa, execute novamente `python 1_extrair.py`.
### Silver

`2_transformar.py` converte os textos para datas, inteiros e valores decimais. As tabelas possuem chaves primárias, chaves estrangeiras e restrições de integridade. São calculados:

```text
valor_total = valor_diarias + valor_passagens + valor_outros_gastos - valor_devolucao
duracao_dias = data_fim - data_inicio
```

Somente na composição do total, componentes ausentes contam como zero. Os campos individuais permanecem nulos quando não informados. A duração corresponde à diferença entre as datas, sem adicionar um dia à contagem.

### Gold

O notebook cria a tabela `gold_resumo_viagem`, com chave primária em `id_viagem`, e a view `gold_resumo_viagem_vw`, ambas com uma linha por viagem. Pagamentos, passagens e trechos são agregados antes das junções para evitar multiplicação de valores.

A view de resumo alimenta quatro views agregadas: `gold_pagamento_tipo_vw`, `gold_transporte_vw`, `gold_destino_uf_vw` e `gold_orgao_pagador_vw`. As perguntas 4 a 7 consultam exclusivamente essas views Gold, que utilizam JOIN e GROUP BY para obter os indicadores.

A reconstrução dos objetos Gold ocorre em uma transação. Raw e Silver são utilizadas como fontes de leitura. A última célula compara contagens e totais entre as camadas e verifica que a Gold possui uma linha por viagem.

## Instalação e configuração

Instale Python e PostgreSQL. Confirme que o serviço PostgreSQL está ativo e que o usuário configurado pode criar um banco. Abra a pasta do projeto no VS Code e execute no PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

No Windows, uma pasta curta, como `D:\ProjetoViagens`, ajuda a evitar o limite de tamanho de caminhos do JupyterLab. Se a instalação falhar por esse motivo, utilize as extensões Python e Jupyter do VS Code e instale:

```powershell
python -m pip install pandas sqlalchemy psycopg2-binary python-dotenv gdown matplotlib seaborn nbformat ipykernel
```

Se ainda não existir um `.env`, copie o modelo:

```powershell
Copy-Item .env.example .env
```

Preencha o `.env` com sua senha local e o ID da base:

```dotenv
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=COLE_SUA_SENHA_AQUI
POSTGRES_DATABASE=transparencia_viagens
DRIVE_FILE_ID=1pQjKacyHdIsyteknQbwKGM5_4hL5V4RV
```

Cada pessoa utiliza as credenciais do próprio PostgreSQL. O `.env.example` pode manter `DRIVE_FILE_ID=` vazio, pois o ID está documentado neste README. Não publique o `.env` nem sua senha real.

## Execução

Com o ambiente virtual ativo, execute cada comando e aguarde a conclusão antes de prosseguir:

```powershell
python 0_criar_banco.py
python 1_extrair.py
python 2_transformar.py
```

**Atenção:** a etapa 0 remove e recria as tabelas do projeto e os objetos Gold. Utilize um banco dedicado e repita essa etapa apenas quando desejar reinicializar o projeto.

Se ocorrer erro de codificação na conexão com PostgreSQL no Windows, configure a sessão antes de tentar novamente:

```powershell
$env:PGCLIENTENCODING = "UTF8"
```

Se a falha persistir, confira também as credenciais, o serviço e a porta do PostgreSQL.

Para executar a análise no VS Code:

1. Abra `3_analise.ipynb`.
2. Clique em Selecionar Kernel e em Ambientes do Python.
3. Escolha `.venv\Scripts\python.exe`.
4. Use Reiniciar Kernel e Executar Tudo.
5. Confira os resultados e salve o notebook com suas saídas usando `Ctrl+S`.

## Perguntas de negócio

1. Quais são os cinco órgãos superiores com maior custo total?
2. Quais são os três destinos com maior custo médio por viagem?
3. Qual foi a viagem de maior duração e qual foi seu custo total?
4. Qual tipo de pagamento apresenta o maior valor médio?
5. Qual meio de transporte aparece mais nos trechos?
6. Qual UF de destino aparece em mais trechos?
7. Qual órgão pagador apresenta o maior total pago?

Custo da viagem e total desembolsado em pagamentos são medidas de fontes diferentes e não devem ser somados entre si.

## Conferência da execução

Na versão fornecida da base, as cargas Raw e Silver produziram:

| Entidade | Raw | Silver |
|---|---:|---:|
| Viagem | 341.860 | 341.860 |
| Pagamento | 606.916 | 606.916 |
| Passagem | 167.260 | 167.260 |
| Trecho | 763.349 | 763.349 |

São 1.879.385 registros em cada camada. Após executar o notebook, `gold_resumo_viagem` e `gold_resumo_viagem_vw` devem ter uma linha por viagem: 341.860 registros nesta base. As quatro views agregadas têm uma linha por categoria de pagamento, transporte, UF ou órgão pagador.

Para testar o download, mantenha uma cópia de segurança do ZIP e deixe o caminho `data/viagens_2025_6meses.zip` sem arquivo. Configure `DRIVE_FILE_ID` no `.env` e execute `python 1_extrair.py`. O resultado esperado é o download seguido da carga. Esse teste substitui a Raw; execute novamente a transformação e o notebook para atualizar Silver e Gold.

Para testar a reexecução, repita extração e transformação e confira se as contagens permanecem iguais. As contagens, isoladamente, não comprovam a correção de todas as análises.

## Resultados e interpretação

Na versão fornecida da base, Raw e Silver possuem 1.879.385 registros cada. A tabela de resumo Gold possui 341.860 viagens. O notebook confere as contagens, a unicidade das viagens e os totais de custo, pagamentos e trechos. As sete respostas foram verificadas e as seis figuras foram salvas no notebook executado.

| Pergunta | Resultado principal |
|---|---|
| Maior custo por órgão superior | Ministério da Justiça e Segurança Pública: R$ 486.933.121,65. |
| Maior custo médio por roteiro | Abu Dabi/Emirados Árabes, Riad/Arábia Saudita, Rio de Janeiro/RJ: R$ 245.852,80, referente a uma viagem. |
| Viagem de maior duração | Processo 0000000000020699856: 383 dias, com R$ 0,00 registrados como custo total. |
| Maior média por tipo de pagamento | DIÁRIAS: R$ 2.078,28 por registro. |
| Transporte mais frequente | Veículo Oficial: 386.424 trechos. |
| UF de destino mais frequente | São Paulo: 82.722 ocorrências em trechos. |
| Maior total por órgão pagador | Fundo Nacional de Segurança Pública: R$ 278.481.047,89. |

Na pergunta 2, destino significa o roteiro textual completo; o custo não é repartido entre cidades. Os códigos Roteiro 1, 2 e 3 no gráfico correspondem aos textos completos da tabela apresentada logo acima. Uma média baseada em uma viagem não permite generalizar o custo daquele destino.

Na pergunta 3, o custo zero é um valor registrado na fonte e não comprova ausência de despesas. Duração e custo são apresentados separadamente, com suas respectivas unidades.

Custos de viagens, pagamentos e frequências representam medidas distintas. Os rankings, isoladamente, não permitem concluir eficiência ou causalidade. As interpretações exibidas no notebook são calculadas a partir das consultas executadas.
## Observações e limites

- Algumas viagens iniciadas no primeiro semestre de 2025 possuem datas finais em 2026; esses registros são mantidos.
- Cargo, CPF, UF e data de emissão podem estar vazios na fonte; a transformação não inventa valores para preenchê-los.
- A categoria de transporte `Inválido` existe na fonte e permanece nas contagens.
- A segunda pergunta agrupa o texto completo de `Destinos`. O custo de uma viagem com vários destinos não é distribuído entre cidades.
- Os rankings e valores financeiros devem ser consultados nas saídas salvas do notebook e interpretados a partir dos resultados executados.

## GitHub e entrega

Versione os scripts, o notebook com suas saídas, este README, `requirements.txt`, `.env.example` e `.gitignore`. Confira se o `.gitignore` contém:

```gitignore
.env
.venv/
.venv-1/
.vscode/
venv/
__pycache__/
*.py[cod]
.ipynb_checkpoints/
data/
*.zip
*.csv
```

Use branches por funcionalidade e mensagens curtas e específicas, como `cria tabelas raw e silver`, `implementa extracao` e `documenta execucao do projeto`.

O link entregue no AVA deve ser o do repositório GitHub. O link do Drive neste README permite localizar a fonte para refazer a extração. A senha local do banco não faz parte da entrega.

## Melhorias futuras

- Implementar retentativas para falhas transitórias no download.
- Registrar logs com duração, contagens e registros rejeitados.
- Automatizar verificações de conversão, duplicidade, relacionamentos e totais.
- Padronizar nomes de destinos antes de análises por cidade.
- Aprofundar a interpretação dos rankings considerando volume de viagens, características dos roteiros e evolução mensal.
