"""Notebook 07: comparação entre os modelos.

Duas fontes:

- `report/results/multiseed.csv`, gerado por `scripts/multiseed.py`: cada modelo ajustado com 10
  seeds, o que dá média e desvio. `multiseed_table`, `per_class_f1` e `rt_vs_dt` leem esse arquivo.
- O experimento-ponte (`bridge` e `bridge_curve`), rodado aqui com a seed 42.

O experimento-ponte separa as duas coisas que a Random Forest acrescenta à árvore de decisão:
o sorteio de atributos em cada nó (que transforma a árvore numa Random Tree) e a média de muitas
árvores treinadas em amostras bootstrap (bagging). Os quatro modelos usam a mesma árvore base,
sem poda; só mudam K e o número de árvores.
"""
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

from src import modeling
from src.config import CLASSES
from src.random_forest import TREE_COUNTS, staged_accuracy

N_TREES = 300
#: Sementes da árvore única no experimento-ponte: uma Random Tree varia com a semente, então a
#: célula "1 árvore" mostra a média de várias.
SINGLE_SEEDS = 10

#: Ordem e rótulo curto de cada modelo nas tabelas, a partir do nome gravado no multiseed.
MODELS = {
    "Dummy (classe majoritária)": "Classe majoritária",
    "Árvore de decisão": "Árvore de decisão",
    "Random Tree (padrão Weka)": "Random Tree (padrão Weka)",
    "Random Tree": "Random Tree (ajustada)",
    "Bagging (300 árvores)": "Bagging de árvores",
    "Random Forest (300 árvores)": "Random Forest (padrão)",
    "Random Forest (ajustada)": "Random Forest (ajustada)",
    "HistGradientBoosting": "Gradient boosting (padrão)",
    "Gradient boosting (ajustado)": "Gradient boosting (ajustado)",
}


def load_multiseed(path):
    """Linhas do multiseed no cenário escolhido (descritores + SMILES, divisão agrupada)."""
    results = pd.read_csv(path)
    features, split = modeling.CHOSEN
    return results[(results["features"] == features) & (results["split"] == split)]


def multiseed_table(results):
    """Média e desvio da acurácia e do F1 macro por modelo, em %, na ordem de `MODELS`."""
    present = [m for m in MODELS if m in set(results["modelo"])]
    grouped = results.groupby("modelo")
    table = pd.DataFrame({
        "acurácia (%)": grouped["acurácia"].mean() * 100,
        "desvio (pontos)": grouped["acurácia"].std() * 100,
        "F1 macro (%)": grouped["F1 macro"].mean() * 100,
        "tempo de treino (s)": grouped["tempo de treino (s)"].mean(),
        "seeds": results.groupby("modelo")["seed"].nunique(),
    }).loc[present].round(2)
    return table.rename(index=MODELS)


def gain_over_tree(results):
    """Ganho de cada modelo sobre a árvore de decisão, seed a seed (mesmo split), em pontos."""
    wide = results.pivot(index="seed", columns="modelo", values="acurácia")
    gain = wide.sub(wide["Árvore de decisão"], axis=0) * 100
    present = [m for m in MODELS if m in gain and m != "Árvore de decisão"]
    table = pd.DataFrame({"ganho médio (pontos)": gain[present].mean(), "desvio": gain[present].std(),
                          "seeds com ganho": (gain[present] > 0).sum()}).round(2)
    return table.rename(index=MODELS)


def per_class_f1(results):
    """F1 médio por classe e modelo, em %."""
    present = [m for m in MODELS if m in set(results["modelo"]) and m != "Dummy (classe majoritária)"]
    table = results.groupby("modelo")[[f"F1 {c}" for c in CLASSES]].mean().loc[present] * 100
    return table.rename(index=MODELS, columns=lambda c: c.removeprefix("F1 ")).round(1)


def rt_vs_dt(path):
    """Random Tree ajustada contra a árvore de decisão nos 6 cenários, média das seeds."""
    results = pd.read_csv(path)
    part = results[results["modelo"].isin(["Árvore de decisão", "Random Tree"])]
    wide = part.pivot_table(index=["features", "split"], columns="modelo", values="acurácia", aggfunc="mean") * 100
    paired = part.pivot_table(index=["features", "split", "seed"], columns="modelo", values="acurácia")
    diff = (paired["Random Tree"] - paired["Árvore de decisão"]) * 100
    wide["diferença (pontos)"] = diff.groupby(["features", "split"]).mean()
    wide["seeds com RT melhor"] = (diff > 0).groupby(["features", "split"]).sum()
    return wide.round(2)


def _bridge_models(seed, max_features):
    """As quatro células do experimento: (sorteio de atributos, número de árvores) -> modelo."""
    return {
        ("sem sorteio", "1 árvore"): DecisionTreeClassifier(random_state=seed),
        ("com sorteio", "1 árvore"): DecisionTreeClassifier(max_features=max_features, random_state=seed),
        ("sem sorteio", f"{N_TREES} árvores"): RandomForestClassifier(
            N_TREES, max_features=None, random_state=seed, n_jobs=-1),
        ("com sorteio", f"{N_TREES} árvores"): RandomForestClassifier(
            N_TREES, max_features=max_features, random_state=seed, n_jobs=-1),
    }


def bridge(dados, max_features="sqrt", single_seeds=SINGLE_SEEDS):
    """Acurácia de teste no desenho 2×2: sorteio de atributos (sim/não) × 1 ou 300 árvores.

    "Sem sorteio, 1 árvore" é a árvore de decisão sem poda; "com sorteio, 1 árvore" é a Random Tree;
    "sem sorteio, 300 árvores" é o bagging de árvores de decisão; "com sorteio, 300 árvores" é a
    Random Forest. As árvores únicas são a média de `single_seeds` sementes.
    """
    X_tr, X_te, y_tr, y_te = modeling._subset(dados)
    rows = []
    for (sorteio, arvores), _ in _bridge_models(dados.seed, max_features).items():
        seeds = range(single_seeds) if arvores == "1 árvore" else [dados.seed]
        scores = [_bridge_models(s, max_features)[(sorteio, arvores)].fit(X_tr, y_tr).score(X_te, y_te) for s in seeds]
        rows.append({"sorteio de atributos": sorteio, "árvores": arvores,
                     "acurácia teste": round(pd.Series(scores).mean(), 4),
                     "desvio entre sementes": round(pd.Series(scores).std(), 4) if len(scores) > 1 else None})
    return pd.DataFrame(rows)


def bridge_matrix(table):
    """A tabela do `bridge` como matriz 2×2 (linhas = sorteio, colunas = número de árvores), em %."""
    return (table.pivot(index="sorteio de atributos", columns="árvores", values="acurácia teste") * 100).round(1)


def bridge_curve(dados, max_features="sqrt", counts=TREE_COUNTS):
    """Acurácia de validação agrupada por número de árvores, com e sem sorteio de atributos."""
    X_fit, X_val, y_fit, y_val = modeling.validation_fold(dados)
    curves = {}
    for name, k in [("bagging (sem sorteio)", None), ("Random Forest (com sorteio)", max_features)]:
        forest = RandomForestClassifier(max(counts), max_features=k, random_state=dados.seed, n_jobs=-1).fit(X_fit, y_fit)
        curves[name] = staged_accuracy(forest, X_val, y_val, counts)
    return pd.DataFrame(curves).round(3).rename_axis("árvores")
