"""Generate the reproducible project analysis notebook."""
from pathlib import Path
import nbformat as nbf

root = Path(__file__).resolve().parent
nb = nbf.v4.new_notebook()
cells = [
 nbf.v4.new_markdown_cell("""# Análise de despesas com viagens — janeiro a junho de 2025

Execute nesta ordem: `0_criar_banco.py`, `1_extrair.py`, `2_transformar.py` e este notebook. A seleção da base corresponde ao primeiro semestre de 2025; datas finais posteriores, inclusive em 2026, são mantidas. Custo da viagem = diárias + passagens + outros gastos − devoluções; componente ausente é tratado como zero apenas nessa soma."""),
 nbf.v4.new_code_cell('''import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import text
from banco import motor
sns.set_theme(style="whitegrid", palette="viridis")
engine = motor()
def consultar(sql): return pd.read_sql(text(sql), engine)
print("Conectado ao banco do projeto.")'''),
 nbf.v4.new_markdown_cell("## Pergunta 1 — Cinco órgãos superiores com maior custo total"),
 nbf.v4.new_code_cell('''q1 = consultar("""SELECT nome_orgao_superior AS orgao, SUM(valor_total) AS custo_total
FROM silver_viagem GROUP BY nome_orgao_superior ORDER BY custo_total DESC LIMIT 5""")
display(q1.style.format({"custo_total": "R$ {:,.2f}"}))
ax=q1.sort_values("custo_total").plot.barh(x="orgao",y="custo_total",legend=False,figsize=(10,5),color="#4c956c")
ax.set(title="Cinco órgãos com maior custo total",xlabel="Custo total (R$)",ylabel="Órgão superior")
plt.tight_layout(); plt.show()'''),
 nbf.v4.new_markdown_cell("## Pergunta 2 — Três destinos com maior custo médio por viagem\nAgrupa pelo texto completo do campo Destinos, evitando duplicar custo por causa de vários trechos."),
 nbf.v4.new_code_cell('''q2 = consultar("""SELECT destinos AS destino, COUNT(*) AS viagens, AVG(valor_total) AS custo_medio
FROM silver_viagem WHERE destinos IS NOT NULL GROUP BY destinos ORDER BY custo_medio DESC LIMIT 3""")
display(q2.style.format({"custo_medio": "R$ {:,.2f}"}))
ax=q2.sort_values("custo_medio").plot.barh(x="destino",y="custo_medio",legend=False,figsize=(10,4),color="#386641")
ax.set(title="Três destinos com maior custo médio",xlabel="Custo médio (R$)",ylabel="Destino")
plt.tight_layout(); plt.show()'''),
 nbf.v4.new_markdown_cell("## Pergunta 3 — Viagem mais longa e seu custo"),
 nbf.v4.new_code_cell('''q3 = consultar("""SELECT id_viagem,nome_viajante,nome_orgao_superior,destinos,data_inicio,data_fim,duracao_dias,valor_total
FROM silver_viagem WHERE duracao_dias IS NOT NULL ORDER BY duracao_dias DESC,valor_total DESC LIMIT 1""")
display(q3.style.format({"valor_total": "R$ {:,.2f}"}))
if not q3.empty:
    x=q3.iloc[0]
    plt.figure(figsize=(7,4)); plt.bar(["Duração (dias)","Custo (R$ mil)"],[x.duracao_dias,x.valor_total/1000],color=["#6a994e","#a7c957"])
    plt.title(f"Viagem mais longa — processo {x.id_viagem}"); plt.tight_layout(); plt.show()'''),
 nbf.v4.new_markdown_cell("## Camada Gold\nAgrega as tabelas filhas antes das junções para impedir multiplicação de valores. Recria apenas os objetos Gold."),
 nbf.v4.new_code_cell('''gold_sql = """
DROP VIEW IF EXISTS gold_resumo_viagem_vw;
DROP TABLE IF EXISTS gold_resumo_viagem;
CREATE TABLE gold_resumo_viagem AS
WITH pagamentos AS (SELECT id_viagem,SUM(valor) valor_pago,COUNT(*) quantidade_pagamentos FROM silver_pagamento GROUP BY id_viagem),
passagens AS (SELECT id_viagem,SUM(COALESCE(valor_passagem,0)+COALESCE(taxa_servico,0)) custo_passagens FROM silver_passagem GROUP BY id_viagem),
trechos AS (SELECT id_viagem,COUNT(*) quantidade_trechos FROM silver_trecho GROUP BY id_viagem)
SELECT v.id_viagem,v.nome_orgao_superior,v.valor_total,v.duracao_dias,
 COALESCE(p.valor_pago,0) valor_pago,COALESCE(p.quantidade_pagamentos,0) quantidade_pagamentos,
 COALESCE(a.custo_passagens,0) custo_passagens,COALESCE(t.quantidade_trechos,0) quantidade_trechos
FROM silver_viagem v LEFT JOIN pagamentos p USING(id_viagem)
LEFT JOIN passagens a USING(id_viagem) LEFT JOIN trechos t USING(id_viagem);
CREATE VIEW gold_resumo_viagem_vw AS SELECT * FROM gold_resumo_viagem;"""
with engine.begin() as conn:
    for statement in gold_sql.split(";"):
        if statement.strip(): conn.execute(text(statement))
print("Tabela e view Gold criadas.")'''),
 nbf.v4.new_markdown_cell("## Pergunta 4 — Tipo de pagamento com maior valor médio"),
 nbf.v4.new_code_cell('''q4=consultar("""SELECT tipo_pagamento,COUNT(*) pagamentos,AVG(valor) valor_medio FROM silver_pagamento
GROUP BY tipo_pagamento ORDER BY valor_medio DESC""")
display(q4.style.format({"valor_medio":"R$ {:,.2f}"}))
ax=q4.sort_values("valor_medio").plot.barh(x="tipo_pagamento",y="valor_medio",legend=False,figsize=(9,5),color="#bc6c25")
ax.set(title="Valor médio por tipo de pagamento",xlabel="Valor médio (R$)",ylabel="Tipo"); plt.tight_layout(); plt.show()'''),
 nbf.v4.new_markdown_cell("## Perguntas 5 e 6 — Meio de transporte mais usado e UF de destino mais frequente"),
 nbf.v4.new_code_cell('''q5=consultar("""SELECT meio_transporte,COUNT(*) trechos FROM silver_trecho WHERE meio_transporte IS NOT NULL
GROUP BY meio_transporte ORDER BY trechos DESC""")
q6=consultar("""SELECT destino_uf uf_destino,COUNT(*) ocorrencias FROM silver_trecho WHERE destino_uf IS NOT NULL
GROUP BY destino_uf ORDER BY ocorrencias DESC LIMIT 10""")
display(q5); display(q6)
fig,ax=plt.subplots(1,2,figsize=(15,5))
q5.head(8).sort_values("trechos").plot.barh(x="meio_transporte",y="trechos",ax=ax[0],legend=False,color="#606c38")
q6.sort_values("ocorrencias").plot.barh(x="uf_destino",y="ocorrencias",ax=ax[1],legend=False,color="#283618")
ax[0].set(title="Trechos por meio",xlabel="Quantidade",ylabel="Meio"); ax[1].set(title="Dez UFs de destino",xlabel="Ocorrências",ylabel="UF")
plt.tight_layout(); plt.show()'''),
 nbf.v4.new_markdown_cell("## Pergunta 7 — Órgão pagador com maior valor total"),
 nbf.v4.new_code_cell('''q7=consultar("""SELECT p.nome_orgao_pagador orgao_pagador,SUM(p.valor) total_pago,COUNT(*) pagamentos
FROM silver_pagamento p JOIN gold_resumo_viagem_vw g USING(id_viagem)
WHERE p.nome_orgao_pagador IS NOT NULL GROUP BY p.nome_orgao_pagador ORDER BY total_pago DESC LIMIT 10""")
display(q7.style.format({"total_pago":"R$ {:,.2f}"}))
ax=q7.sort_values("total_pago").plot.barh(x="orgao_pagador",y="total_pago",legend=False,figsize=(11,6),color="#dda15e")
ax.set(title="Órgãos pagadores por valor total",xlabel="Total pago (R$)",ylabel="Órgão pagador"); plt.tight_layout(); plt.show()'''),
 nbf.v4.new_markdown_cell("""## Observações sobre os dados
- Campos como cargo, CPF, UF e data de emissão podem estar vazios na fonte; não são preenchidos artificialmente.
- A categoria de transporte `Inválido` existe na fonte e é mantida nas contagens.
- A base inclui viagens iniciadas no primeiro semestre, com datas finais que podem avançar para 2026.
- Q2 agrupa o texto integral de Destinos; grafias diferentes podem aparecer como destinos separados."""),
]
nb.cells = cells
nb.metadata = {"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.11.0"}}
nbf.write(nb, root / "3_analise.ipynb")
print("Notebook criado:", root / "3_analise.ipynb")
