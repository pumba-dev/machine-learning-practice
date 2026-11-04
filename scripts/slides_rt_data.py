"""Números da segunda apresentação (comparação entre árvore, Random Tree e conjuntos de árvores).

Grava slides/data/slides_rt_data.json, lido por build_slides_rt.py e slides_rt_notes.py. Duas fontes:

- report/results/multiseed.csv (10 seeds), pelas mesmas funções do notebook 07 (`src/comparison`);
- a seed 42, refazendo o que os notebooks 03 a 07 mostram: busca no cenário escolhido, curvas,
  árvore, Random Tree e Random Forest com a mesma árvore base, e confiança de cada modelo no teste.

Uso, a partir da raiz do projeto (leva alguns minutos, por causa das buscas da RF e do boosting):

    python scripts/slides_rt_data.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import comparison, modeling, random_forest, random_tree  # noqa: E402
from src import gradient_boosting  # noqa: E402
from src.config import CLASSES, FINAL_CSV  # noqa: E402

MULTISEED = ROOT / "report" / "results" / "multiseed.csv"
OUT = ROOT / "slides" / "data" / "slides_rt_data.json"


def multiseed_block():
    """Tabela de modelos, ganho sobre a árvore seed a seed, F1 por classe e Random Tree × árvore."""
    results = comparison.load_multiseed(MULTISEED)
    table = comparison.multiseed_table(results)
    gain = comparison.gain_over_tree(results)
    f1 = comparison.per_class_f1(results)
    models = {}
    for label, row in table.iterrows():
        if label.startswith("Bagging"):  # o bagging fica só no notebook 07
            continue
        models[label] = {
            "acuracia": float(row["acurácia (%)"]),
            "desvio": float(row["desvio (pontos)"]),
            "f1_macro": float(row["F1 macro (%)"]),
        }
        if label in gain.index:
            models[label]["ganho_pontos"] = float(gain.loc[label, "ganho médio (pontos)"])
            models[label]["seeds_com_ganho"] = int(gain.loc[label, "seeds com ganho"])
        if label in f1.index:
            models[label]["f1_classes"] = {c: float(f1.loc[label, c]) for c in CLASSES}
    rt = comparison.rt_vs_dt(MULTISEED).reset_index()
    scenarios = [{
        "features": r["features"], "split": r["split"],
        "arvore": float(r["Árvore de decisão"]), "random_tree": float(r["Random Tree"]),
        "diferenca_pontos": float(r["diferença (pontos)"]), "seeds_rt_melhor": int(r["seeds com RT melhor"]),
    } for _, r in rt.iterrows()]
    return {"modelos": models, "rt_cenarios": scenarios, "seeds": int(results["seed"].nunique())}


def confidence(model, dados):
    """Como a confiança do modelo se relaciona com os erros no teste. Faixas fechadas à direita, como em
    `modeling.confidence_table`: "abaixo de 70%" inclui 70%, "máxima" é acima de 99,9%."""
    X_tr, X_te, y_tr, y_te = modeling._subset(dados)
    proba = model.predict_proba(X_te)
    conf = proba.max(axis=1)
    wrong = model.classes_[proba.argmax(axis=1)] != y_te.to_numpy()
    n_wrong = int(wrong.sum())
    top = conf > 0.999
    real, predicted = y_te.to_numpy()[wrong], model.classes_[proba.argmax(axis=1)][wrong]
    pair = np.isin(real, ["HDAC1", "EGFR"]) & np.isin(predicted, ["HDAC1", "EGFR"])
    return {
        "teste": int(len(y_te)),
        "erros": n_wrong,
        "acuracia": float(1 - wrong.mean()) * 100,
        "previsoes_confianca_maxima": float(top.mean() * 100),
        "erros_confianca_maxima": float(wrong[top].sum() / n_wrong * 100),
        "erros_abaixo_70": float(wrong[conf <= 0.7].sum() / n_wrong * 100),
        "previsoes_abaixo_70": float((conf <= 0.7).mean() * 100),
        "acuracia_acima_90": float(1 - wrong[conf > 0.9].mean()) * 100,
        "par_hdac1_egfr": float(pair.mean() * 100),
    }


def score(model, dados):
    return float(modeling.test_scores(model, dados)["acurácia teste"] * 100)


def seed42_block(dados):
    seed = dados.seed
    n_features = len(dados.X.columns)
    out = {"seed": seed}

    print("árvore de decisão", flush=True)
    _, tree = modeling.tune_chosen(dados, DecisionTreeClassifier(random_state=seed), modeling.PARAM_GRID)

    print("Random Tree", flush=True)
    _, rt = modeling.tune_chosen(dados, random_tree.estimator(seed), random_tree.PARAM_GRID)
    rt_params = modeling.chosen_params(rt, random_tree.PARAM_GRID)
    X_tr, _, y_tr, _ = modeling._subset(dados)
    weka = random_tree.weka_default(seed, n_features).fit(X_tr, y_tr)
    curve = random_tree.max_features_curve(dados, rt_params)
    variance = random_tree.seed_summary(random_tree.seed_variance(dados, rt_params))
    k_rt = rt_params["max_features"]
    out["random_tree"] = {
        "k_weka": random_tree.weka_k(n_features),
        "k_ajustada": int(k_rt * n_features) if isinstance(k_rt, float) else k_rt,
        "params": {k: (None if v is None else v) for k, v in rt_params.items()},
        "acuracia_weka": score(weka, dados),
        "acuracia_ajustada": score(rt, dados),
        "folhas_ajustada": int(rt.get_n_leaves()),
        "curva_k": {int(k): float(v * 100) for k, v in curve["validação"].items()},
        "melhor_k": int(curve["validação"].idxmax()),
        "sementes": {name: {c: float(row[c] * 100) for c in ["mean", "std", "min", "max"]}
                     for name, row in variance.iterrows()},
    }

    print("Random Forest", flush=True)
    _, forest = modeling.tune_chosen(dados, random_forest.estimator(seed), random_forest.PARAM_GRID)
    forest_params = modeling.chosen_params(forest, random_forest.PARAM_GRID)
    forest_default = modeling.reference_candidates(seed)["Random Forest (300 árvores)"].fit(X_tr, y_tr)
    trees = random_forest.n_trees_curve(dados, forest_params)

    print("gradient boosting", flush=True)
    _, boosting = modeling.tune_chosen(dados, gradient_boosting.estimator(seed), gradient_boosting.PARAM_GRID)
    boosting_params = modeling.chosen_params(boosting, gradient_boosting.PARAM_GRID)
    boosting_default = modeling.reference_candidates(seed)["HistGradientBoosting"].fit(X_tr, y_tr)
    iterations = gradient_boosting.iterations_curve(dados, boosting_params)

    print("árvore, Random Tree e Random Forest", flush=True)
    bridge = comparison.bridge(dados)
    bridge_curve = comparison.bridge_curve(dados)

    out["ajuste"] = {
        "random_forest": {"padrao": score(forest_default, dados), "ajustada": score(forest, dados),
                          "params": {k: str(v) for k, v in forest_params.items()},
                          "curva_arvores": {int(k): float(v * 100) for k, v in trees["validação"].items()}},
        "gradient_boosting": {"padrao": score(boosting_default, dados), "ajustado": score(boosting, dados),
                              "params": {k: str(v) for k, v in boosting_params.items()},
                              "curva_iteracoes": {int(k): float(v * 100) for k, v in iterations["validação"].items()},
                              "curva_iteracoes_treino": {int(k): float(v * 100) for k, v in iterations["treino"].items()}},
    }
    # Da árvore à floresta, com a mesma árvore base: o experimento do notebook 07 sem a célula do bagging.
    cells = {"arvore": ("sem sorteio", "1 árvore"), "random_tree": ("com sorteio", "1 árvore"),
             "random_forest": ("com sorteio", f"{comparison.N_TREES} árvores")}
    out["tres_arvores"] = {}
    for key, (sorteio, arvores) in cells.items():
        r = bridge[(bridge["sorteio de atributos"] == sorteio) & (bridge["árvores"] == arvores)].iloc[0]
        sd = r["desvio entre sementes"]
        out["tres_arvores"][key] = {"acuracia": float(r["acurácia teste"] * 100),
                                    "desvio": None if pd.isna(sd) else float(sd * 100)}
    out["curva_floresta"] = {int(k): float(v * 100) for k, v in bridge_curve["Random Forest (com sorteio)"].items()}

    print("confiança", flush=True)
    out["confianca"] = {
        "Árvore de decisão": confidence(tree, dados),
        "Random Tree": confidence(rt, dados),
        "Random Forest": confidence(forest, dados),
        "Gradient boosting": confidence(boosting, dados),
    }
    out["arvore"] = {"acuracia": score(tree, dados), "folhas": int(tree.get_n_leaves())}
    out["grids"] = {"Árvore de decisão": int(np.prod([len(v) for v in modeling.PARAM_GRID.values()])),
                    "Random Tree": int(np.prod([len(v) for v in random_tree.PARAM_GRID.values()])),
                    "Random Forest": int(np.prod([len(v) for v in random_forest.PARAM_GRID.values()])),
                    "Gradient boosting": int(np.prod([len(v) for v in gradient_boosting.PARAM_GRID.values()]))}
    return out


def main():
    final = pd.read_csv(FINAL_CSV)
    dados = modeling.prepare(final)
    payload = {
        "moleculas": int(len(dados.y)),
        "multiseed": multiseed_block(),
        "seed42": seed42_block(dados),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("gravado:", OUT)


if __name__ == "__main__":
    main()
