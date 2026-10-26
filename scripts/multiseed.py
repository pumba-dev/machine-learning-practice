"""Repete o notebook 03 com várias seeds e grava média e desvio dos resultados de teste.

Cada seed muda o split aleatório, o split agrupado e as dobras da validação cruzada interna; os
dados são os mesmos. Uso, a partir da raiz do projeto:

    python scripts/multiseed.py              # 10 seeds (0 a 9)
    python scripts/multiseed.py --seeds 0 1  # seeds escolhidas

Saídas em report/results/:
    multiseed.csv          uma linha por seed, conjunto de features, split e modelo
    multiseed_summary.csv  média, desvio, mínimo e máximo por conjunto de features, split e modelo
"""
import argparse
import sys
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import modeling  # noqa: E402
from src.config import CLASSES, FINAL_CSV  # noqa: E402

OUT_DIR = ROOT / "report" / "results"
DEFAULT_SEEDS = list(range(10))
METRICS = ["acurácia", "F1 macro", *[f"F1 {c}" for c in CLASSES], "folhas", "profundidade"]


def run_seed(final, seed):
    """Todas as linhas de resultado de uma seed: 6 cenários da árvore + modelos de referência."""
    dados = modeling.prepare(final, seed=seed)
    comparacao, modelos = modeling.tune_all(dados)
    twins = modeling.group_leakage(dados).loc["% do teste com gêmeo"].iloc[0]
    rows = []
    for _, line in comparacao.iterrows():
        features, split = line["features"], line["split"]
        report, _ = modeling.evaluation(modelos[(features, split)], dados, features, split)
        rows.append({
            "seed": seed, "features": features, "split": split, "modelo": "Árvore de decisão",
            "acurácia": line["acurácia teste"], "F1 macro": line["F1 macro teste"],
            **{f"F1 {c}": report.loc[c, "F1"] for c in CLASSES},
            "folhas": line["folhas"], "profundidade": line["profundidade"],
            "% teste com gêmeo": twins,
        })
    features, split = modeling.CHOSEN
    for name, line in modeling.reference_models(dados).iterrows():
        rows.append({
            "seed": seed, "features": features, "split": split, "modelo": name,
            "acurácia": line["acurácia teste"], "F1 macro": line["F1 macro teste"],
            "% teste com gêmeo": twins,
        })
    return rows


def summarize(results):
    """Média, desvio (amostral), mínimo e máximo de cada métrica por cenário."""
    keys = ["features", "split", "modelo"]
    stats = results.groupby(keys, sort=False)[["% teste com gêmeo", *METRICS]].agg(["mean", "std", "min", "max"])
    stats.columns = [f"{metric} {stat}" for metric, stat in stats.columns]
    stats.insert(0, "seeds", results.groupby(keys, sort=False)["seed"].nunique())
    return stats.round(4).reset_index()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seeds", nargs="+", type=int, default=DEFAULT_SEEDS)
    args = parser.parse_args()

    final = pd.read_csv(FINAL_CSV)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for seed in args.seeds:
        start = time.time()
        rows += run_seed(final, seed)
        # Grava a cada seed: uma execução longa interrompida não perde o que já terminou.
        results = pd.DataFrame(rows)
        results.to_csv(OUT_DIR / "multiseed.csv", index=False)
        summarize(results).to_csv(OUT_DIR / "multiseed_summary.csv", index=False)
        print(f"seed {seed} pronta em {time.time() - start:.0f}s", flush=True)


if __name__ == "__main__":
    main()
