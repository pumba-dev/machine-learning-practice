"""Gera as tabelas LaTeX de resultados do relatório a partir de report/results/multiseed.csv.

Uso, a partir da raiz do projeto (depois de scripts/multiseed.py):

    python scripts/results_tables.py

Saídas em report/results/: tab_features.tex e tab_referencia.tex, incluídas por sections/06_resultados.tex.
Os números saem do CSV, então o texto do relatório e as tabelas não divergem de uma execução para outra.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "report" / "results"
TREE = "Árvore de decisão"
FEATURES = ["descritores", "só SMILES", "descritores + SMILES"]
LABELS = {"descritores": "Descritores (5)", "só SMILES": "SMILES (12)", "descritores + SMILES": "Ambos (17)"}


def pm(series, digits=3):
    """'média $\\pm$ desvio' com vírgula decimal; o desvio é o amostral (ddof=1)."""
    return f"{series.mean():.{digits}f} $\\pm$ {series.std():.{digits}f}".replace(".", ",")


def features_table(results):
    """Árvore em cada conjunto de features: os dois splits, F1 macro agrupado e a superestimativa."""
    tree = results[results["modelo"] == TREE]
    rows = []
    for features in FEATURES:
        part = tree[tree["features"] == features]
        random = part[part["split"] == "aleatória"].set_index("seed")
        grouped = part[part["split"] == "agrupada"].set_index("seed")
        gap = (random["acurácia"] - grouped["acurácia"]) * 100  # por seed: mesma divisão de dados nos dois splits
        rows.append(f"{LABELS[features]} & {pm(random['acurácia'])} & {pm(grouped['acurácia'])} & "
                    f"{pm(grouped['F1 macro'])} & {pm(gap, 1)} \\\\")
    return rows


def reference_table(results):
    """Piso, árvore escolhida e modelos de referência, todos no split agrupado com 17 atributos."""
    chosen = results[(results["features"] == "descritores + SMILES") & (results["split"] == "agrupada")]
    rows = []
    for model in ["Dummy (classe majoritária)", TREE, "Random Forest (300 árvores)", "HistGradientBoosting"]:
        part = chosen[chosen["modelo"] == model]
        rows.append(f"{model.replace('Dummy (classe majoritária)', 'Classe majoritária')} & "
                    f"{pm(part['acurácia'])} & {pm(part['F1 macro'])} \\\\")
    per_class = " / ".join(
        f"{c} {chosen[chosen['modelo'] == TREE][f'F1 {c}'].mean():.3f}".replace(".", ",")
        for c in ["EGFR", "BACE1", "DRD2", "HDAC1"]
    )
    return rows, per_class


def main():
    results = pd.read_csv(RESULTS / "multiseed.csv")
    n_seeds = results["seed"].nunique()

    header = "\\begin{tabular}{lcccc}\n\\toprule\n" \
             "Atributos & \\shortstack{Acurácia\\\\aleatória} & \\shortstack{Acurácia\\\\agrupada} & " \
             "\\shortstack{F1 macro\\\\agrupado} & \\shortstack{Superestimativa\\\\(pontos)} \\\\\n\\midrule\n"
    body = "\n".join(features_table(results))
    (RESULTS / "tab_features.tex").write_text(f"{header}{body}\n\\bottomrule\n\\end{{tabular}}\n", encoding="utf-8")

    rows, per_class = reference_table(results)
    header = "\\begin{tabular}{lcc}\n\\toprule\nModelo & Acurácia & F1 macro \\\\\n\\midrule\n"
    (RESULTS / "tab_referencia.tex").write_text(
        f"{header}{chr(10).join(rows)}\n\\bottomrule\n\\end{{tabular}}\n", encoding="utf-8")
    print(f"{n_seeds} seeds; F1 por classe da árvore escolhida: {per_class}")


if __name__ == "__main__":
    main()
