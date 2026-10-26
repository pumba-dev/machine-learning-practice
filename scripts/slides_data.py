"""Calcula os números que os slides mostram e grava slides/data/slides_data.json.

Tudo que não vem de report/results/multiseed.csv é recalculado aqui com a seed 42, pelas mesmas
funções dos notebooks, então os slides não dependem de números digitados à mão.

Uso, a partir da raiz do projeto:

    python scripts/slides_data.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import results_tables  # noqa: E402
from src import eda, modeling  # noqa: E402
from src.config import CLASSES, FEATURE_SETS, FEATURES, FINAL_CSV  # noqa: E402

OUT = ROOT / "slides" / "data" / "slides_data.json"
#: Molécula de HDAC1 que a árvore lê como EGFR e que tem o grupo C(=O)NO; aparece nos slides 4 e 8.
EXAMPLE_ID = "CHEMBL1085117"


def node_summary(model, node, total):
    """Fatia das moléculas que chegam ao nó e a classe mais comum nele."""
    tree = model.tree_
    counts = tree.value[node][0]
    share = counts / counts.sum()
    top = int(np.argmax(share))
    return {
        "fatia": float(tree.weighted_n_node_samples[node] / total),
        "classe": str(model.classes_[top]),
        "fatia_classe": float(share[top]),
    }


def split_of(model, node, names):
    tree = model.tree_
    return {"atributo": names[tree.feature[node]], "limiar": float(tree.threshold[node])}


def tree_rules(model, names):
    """Raiz e os dois filhos da árvore: a pergunta de cada nó e o que chega a ele."""
    tree = model.tree_
    total = tree.weighted_n_node_samples[0]
    left, right = int(tree.children_left[0]), int(tree.children_right[0])
    return {
        "raiz": split_of(model, 0, names),
        "esquerda": {**node_summary(model, left, total), "pergunta": split_of(model, left, names)},
        "direita": {**node_summary(model, right, total), "pergunta": split_of(model, right, names)},
        "folhas": int(model.get_n_leaves()),
    }


def multiseed_block(results):
    """Médias de 10 seeds para os gráficos e os textos grandes, mais as macros já formatadas."""
    scenarios = {}
    for features in results_tables.FEATURES:
        random, grouped = results_tables.paired(results, features)
        scenarios[features] = {
            "aleatoria": float(random["acurácia"].mean() * 100),
            "agrupada": float(grouped["acurácia"].mean() * 100),
            "dp_aleatoria": float(random["acurácia"].std() * 100),
            "dp_agrupada": float(grouped["acurácia"].std() * 100),
        }
    chosen = results[(results["features"] == "descritores + SMILES") & (results["split"] == "agrupada")]
    reference = {model: float(chosen[chosen["modelo"] == model]["acurácia"].mean() * 100)
                 for model in results_tables.MODELS}
    return {
        "cenarios": scenarios,
        "referencia": reference,
        "dp_maximo": max(max(v["dp_aleatoria"], v["dp_agrupada"]) for v in scenarios.values()),
        "macros": results_tables.macros(results),
    }


def main():
    final = pd.read_csv(FINAL_CSV)
    results = pd.read_csv(ROOT / "report" / "results" / "multiseed.csv")

    accuracy, baseline = eda.single_feature_accuracy(final)
    classes = final["Protein"].value_counts().reindex(CLASSES)

    example = final[final["ChEMBL ID"] == EXAMPLE_ID].iloc[0]
    counts = modeling.smiles_features(pd.Series([example["SMILES"]])).iloc[0]

    dados = modeling.prepare(final)
    comparacao, modelos = modeling.tune_all(dados)
    tree = modelos[modeling.CHOSEN]
    names = FEATURE_SETS[modeling.CHOSEN[0]]
    _, matrix = modeling.evaluation(tree, dados)
    errors = modeling.error_overview(tree, dados)
    pair = errors[errors.apply(lambda r: {r["real"], r["prevista"]} == {"HDAC1", "EGFR"}, axis=1)]
    confidence = modeling.confidence_table(tree, dados)

    n_test = int(matrix.to_numpy().sum())
    n_wrong = int(n_test - np.trace(matrix.to_numpy()))
    payload = {
        "seed": 42,
        "classes": {c: {"moleculas": int(classes[c]), "percentual": float(classes[c] / classes.sum() * 100)} for c in CLASSES},
        "total_moleculas": int(classes.sum()),
        "descritor_sozinho": {k: float(v * 100) for k, v in accuracy.items()},
        "piso": float(baseline * 100),
        "exemplo": {
            "id": EXAMPLE_ID,
            "classe": str(example["Protein"]),
            "smiles": str(example["SMILES"]),
            "descritores": {name: float(example[name]) for name in FEATURES},
            "contagens": {k: int(v) for k, v in counts.items()},
        },
        "arvore": tree_rules(tree, names),
        "matriz_confusao": {"classes": CLASSES, "valores": matrix.to_numpy().tolist()},
        "erros": {
            "total": n_wrong,
            "teste": n_test,
            "percentual_erro": float(n_wrong / n_test * 100),
            "par_hdac1_egfr": float(pair["% dos erros"].sum()),
            "previsoes_com_confianca_100": float(confidence["% do teste"].iloc[-1]),
        },
        "multiseed": multiseed_block(results),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("gravado:", OUT)


if __name__ == "__main__":
    main()
