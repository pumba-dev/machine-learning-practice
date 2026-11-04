"""Repete os notebooks 03 a 06 com várias seeds e grava média e desvio dos resultados de teste.

Cada seed muda o split aleatório, o split agrupado e as dobras da validação cruzada interna; os
dados são os mesmos. Uso, a partir da raiz do projeto:

    python scripts/multiseed.py                       # 10 seeds (0 a 9), todos os modelos
    python scripts/multiseed.py --seeds 0 1           # seeds escolhidas
    python scripts/multiseed.py --models rf gb        # só alguns grupos de modelos

Grupos de modelos (`--models`):
    arvore        árvore de decisão ajustada nos 6 cenários (notebook 03)
    random-tree   Random Tree ajustada nos 6 cenários e no padrão do Weka (notebook 04)
    rf            Random Forest ajustada (notebook 05)
    gb            gradient boosting ajustado (notebook 06)
    bagging       bagging de 300 árvores de decisão (experimento-ponte do notebook 07)
    referencia    classe majoritária, Random Forest e gradient boosting sem ajuste

Os modelos fora dos grupos 'arvore' e 'random-tree' só rodam no cenário escolhido (descritores + SMILES,
divisão agrupada). Uma execução parcial não apaga o resto: as linhas novas substituem só as de mesma
seed, conjunto de features, divisão e modelo.

Saídas em report/results/:
    multiseed.csv          uma linha por seed, conjunto de features, split e modelo
    multiseed_summary.csv  média, desvio, mínimo e máximo por conjunto de features, split e modelo
"""
import argparse
import sys
import time
from pathlib import Path

import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import gradient_boosting, modeling, random_forest, random_tree  # noqa: E402
from src.config import CLASSES, FEATURE_SETS, FINAL_CSV  # noqa: E402

OUT_DIR = ROOT / "report" / "results"
DEFAULT_SEEDS = list(range(10))
GROUPS = ["arvore", "random-tree", "rf", "gb", "bagging", "referencia"]
KEYS = ["seed", "features", "split", "modelo"]
METRICS = ["acurácia", "F1 macro", *[f"F1 {c}" for c in CLASSES], "folhas", "profundidade", "tempo de treino (s)"]


def result_row(dados, model, name, features, split, seconds, twins):
    """Uma linha do CSV: métricas de teste, F1 por classe e, para árvores únicas, folhas e profundidade."""
    report, _ = modeling.evaluation(model, dados, features, split)
    row = {
        "seed": dados.seed, "features": features, "split": split, "modelo": name,
        "acurácia": report.loc["accuracy", "F1"], "F1 macro": report.loc["macro avg", "F1"],
        **{f"F1 {c}": report.loc[c, "F1"] for c in CLASSES},
        "tempo de treino (s)": round(seconds, 2), "% teste com gêmeo": twins,
    }
    if hasattr(model, "get_n_leaves"):
        row.update({"folhas": model.get_n_leaves(), "profundidade": model.get_depth()})
    return row


def timed_fit(model, dados, features=None, split=None):
    """Ajusta no treino do cenário e devolve (modelo, segundos)."""
    X_tr, _, y_tr, _ = modeling._subset(dados, features, split)
    start = time.time()
    model.fit(X_tr, y_tr)
    return model, time.time() - start


def refit_seconds(model, dados, features=None, split=None):
    """Tempo de um ajuste com os hiperparâmetros escolhidos (o modelo da busca já vem ajustado)."""
    return timed_fit(clone(model), dados, features, split)[1]


def run_seed(final, seed, groups):
    """Todas as linhas de resultado de uma seed para os grupos de modelos pedidos."""
    dados = modeling.prepare(final, seed=seed)
    twins = modeling.group_leakage(dados).loc["% do teste com gêmeo"].iloc[0]
    features, split = modeling.CHOSEN
    rows = []

    def add(model, name, f=features, s=split, seconds=None):
        seconds = refit_seconds(model, dados, f, s) if seconds is None else seconds
        rows.append(result_row(dados, model, name, f, s, seconds, twins))

    if "arvore" in groups:
        _, modelos = modeling.tune_all(dados)
        for (f, s), model in modelos.items():
            add(model, "Árvore de decisão", f, s)
    if "random-tree" in groups:
        _, modelos = modeling.tune_all(dados, random_tree.PARAM_GRID, random_tree.estimator(seed))
        for (f, s), model in modelos.items():
            add(model, "Random Tree", f, s)
        model, seconds = timed_fit(random_tree.weka_default(seed, len(FEATURE_SETS[features])), dados)
        add(model, "Random Tree (padrão Weka)", seconds=seconds)
    if "rf" in groups:
        _, model = modeling.tune_chosen(dados, random_forest.estimator(seed), random_forest.PARAM_GRID)
        add(model, "Random Forest (ajustada)")
    if "gb" in groups:
        _, model = modeling.tune_chosen(dados, gradient_boosting.estimator(seed), gradient_boosting.PARAM_GRID)
        add(model, "Gradient boosting (ajustado)")
    if "bagging" in groups:
        bagging = RandomForestClassifier(300, max_features=None, random_state=seed, n_jobs=-1)
        model, seconds = timed_fit(bagging, dados)
        add(model, "Bagging (300 árvores)", seconds=seconds)
    if "referencia" in groups:
        for name, candidate in modeling.reference_candidates(seed).items():
            model, seconds = timed_fit(candidate, dados)
            add(model, name, seconds=seconds)
    return rows


def merge(old, new):
    """Substitui em `old` as linhas com a mesma chave das de `new` e mantém o resto."""
    if old is None or old.empty:
        return new
    replaced = old.set_index(KEYS).index.isin(new.set_index(KEYS).index)
    return pd.concat([old[~replaced], new], ignore_index=True)


def sort_rows(results):
    """Ordem estável: seed, depois a ordem em que os modelos aparecem nos notebooks."""
    order = ["Árvore de decisão", "Random Tree", "Random Tree (padrão Weka)", "Random Forest (ajustada)",
             "Gradient boosting (ajustado)", "Bagging (300 árvores)", *modeling.reference_candidates(0)]
    rank = results["modelo"].map({m: i for i, m in enumerate(order)})
    return results.assign(_r=rank).sort_values(["seed", "_r"], kind="stable").drop(columns="_r").reset_index(drop=True)


def summarize(results):
    """Média, desvio (amostral), mínimo e máximo de cada métrica por cenário."""
    keys = ["features", "split", "modelo"]
    metrics = [m for m in METRICS if m in results]
    stats = results.groupby(keys, sort=False)[["% teste com gêmeo", *metrics]].agg(["mean", "std", "min", "max"])
    stats.columns = [f"{metric} {stat}" for metric, stat in stats.columns]
    stats.insert(0, "seeds", results.groupby(keys, sort=False)["seed"].nunique())
    return stats.round(4).reset_index()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS)
    parser.add_argument("--models", nargs="+", choices=GROUPS, default=GROUPS)
    args = parser.parse_args()

    final = pd.read_csv(FINAL_CSV)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "multiseed.csv"
    results = pd.read_csv(path) if path.exists() else None
    for seed in args.seeds:
        start = time.time()
        new = pd.DataFrame(run_seed(final, seed, args.models))
        # Grava a cada seed: uma execução longa interrompida não perde o que já terminou.
        results = sort_rows(merge(results, new))
        results.to_csv(path, index=False)
        summarize(results).to_csv(OUT_DIR / "multiseed_summary.csv", index=False)
        print(f"seed {seed} pronta em {time.time() - start:.0f}s", flush=True)


if __name__ == "__main__":
    main()
