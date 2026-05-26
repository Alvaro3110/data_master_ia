"""
Gerador de dados seed — fact_pricing_snapshot + dimensões.
Gera dados sintéticos realistas de pricing/margem/safra/risco/ROAE.
"""
import random
import json
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

fake = Faker("pt_BR")
random.seed(42)
Faker.seed(42)

N_CLIENTES = 500
N_PRODUTOS = 20
N_SAFRAS = 12

SEGMENTOS = ["PME", "Varejo", "Atacado", "Corporativo", "Agro"]
PORTES = ["Micro", "Pequena", "Média", "Grande"]
UFS = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "GO"]
FAMILIAS_PRODUTO = ["Capital de Giro", "Crédito Rural", "Leasing", "Antecipação", "Consignado"]
GARANTIAS = ["Aval", "Hipoteca", "Alienação Fiduciária", "Sem Garantia"]


def gerar_safras(n: int = 12) -> list[str]:
    hoje = date.today()
    safras = []
    for i in range(n, 0, -1):
        d = hoje.replace(day=1) - timedelta(days=30 * i)
        safras.append(d.strftime("%Y-%m"))
    return safras


def gerar_dim_cliente(n: int = N_CLIENTES) -> list[dict]:
    clientes = []
    for i in range(1, n + 1):
        segmento = random.choice(SEGMENTOS)
        rating = random.choice(["AAA", "AA", "A", "BBB", "BB", "B", "CCC"])
        faixa_risco = "alto" if rating in ("BB", "B", "CCC") else ("médio" if rating == "BBB" else "baixo")
        clientes.append({
            "cliente_id": f"CLI{i:06d}",
            "porte": random.choice(PORTES),
            "segmento": segmento,
            "uf": random.choice(UFS),
            "rating": rating,
            "faixa_risco": faixa_risco,
        })
    return clientes


def gerar_dim_produto(n: int = N_PRODUTOS) -> list[dict]:
    produtos = []
    for i in range(1, n + 1):
        familia = random.choice(FAMILIAS_PRODUTO)
        produtos.append({
            "produto_id": f"PROD{i:03d}",
            "produto": f"{familia} {i:02d}",
            "familia": familia,
            "garantia": random.choice(GARANTIAS),
            "prazo_meses": random.choice([12, 24, 36, 48, 60]),
        })
    return produtos


def gerar_fact_pricing_snapshot(clientes, produtos, safras) -> list[dict]:
    rows = []
    snapshot_id = 1
    for safra in safras:
        sample_clientes = random.sample(clientes, min(80, len(clientes)))
        for cliente in sample_clientes:
            for produto in random.sample(produtos, random.randint(1, 3)):
                score_risco = random.randint(1, 10)
                inadimplente = score_risco >= 7 and random.random() < 0.3
                receita = round(random.uniform(50_000, 500_000), 2)
                custo = round(receita * random.uniform(0.3, 0.7), 2)
                margem_liquida = round((receita - custo) / receita * 100 + random.gauss(0, 2), 2)
                patrimonio = round(receita * random.uniform(1.5, 5.0), 2)
                lucro = round(receita * random.uniform(0.05, 0.25), 2)
                roae = round(lucro / patrimonio * 100, 2)
                rows.append({
                    "snapshot_id": f"SNAP{snapshot_id:08d}",
                    "safra": safra,
                    "cliente_id": cliente["cliente_id"],
                    "segmento": cliente["segmento"],
                    "produto": produto["produto_id"],
                    "receita": receita,
                    "custo": custo,
                    "margem_liquida": margem_liquida,
                    "roae": roae,
                    "score_risco": score_risco,
                    "inadimplente": inadimplente,
                    "status_cliente": "ativo" if not inadimplente else "inadimplente",
                })
                snapshot_id += 1
    return rows


if __name__ == "__main__":
    base = Path(__file__).parent
    (base / "sql").mkdir(exist_ok=True)

    safras = gerar_safras(N_SAFRAS)
    clientes = gerar_dim_cliente(N_CLIENTES)
    produtos = gerar_dim_produto(N_PRODUTOS)
    snapshots = gerar_fact_pricing_snapshot(clientes, produtos, safras)

    print(f"✓ {len(clientes)} clientes, {len(produtos)} produtos, {len(snapshots):,} snapshots")
    print(f"  Safras: {safras[0]} → {safras[-1]}")

    # Salva JSON para DuckDB
    import json
    with open(base / "pricing_snapshot.json", "w") as f:
        json.dump(snapshots[:5000], f)
    print(f"✓ pricing_snapshot.json salvo ({min(len(snapshots), 5000)} linhas)")
