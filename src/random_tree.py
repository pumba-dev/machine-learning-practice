"""Notebook 04: Random Tree, a árvore aleatória do Weka.

A RandomTree do Weka é uma árvore única que, em cada nó, sorteia K atributos e escolhe o melhor
corte só entre eles. Não tem poda nem limite de profundidade, e o padrão é K = log2(atributos) + 1.
No scikit-learn ela é um `DecisionTreeClassifier` com `max_features=K`: o sorteio de atributos por
nó é o mesmo; a diferença para a árvore de decisão do notebook 03 é só esse sorteio.

A ordem de uso é a do notebook:

1. `weka_default` / `default_all`  a configuração padrão do Weka nos 6 cenários, sem ajuste
2. `modeling.tune_all(dados, PARAM_GRID, estimator(seed))`  busca em grade nos 6 cenários
3. `versus_tree`         diferença para a árvore de decisão, cenário a cenário
4. `max_features_curve`  treino e validação para K de 1 a 17
5. `seed_variance`       quanto o resultado muda só trocando a semente do sorteio
"""
import math

import pandas as pd
from sklearn.tree import DecisionTreeClassifier

from src import modeling
from src.config import FEATURE_SETS

#: Grid com o mesmo papel do grid da árvore de decisão. `max_features` em fração porque o conjunto
#: "descritores" tem só 5 colunas: 0,25, 0,5 e 0,75 viram K = 1, 2, 3 ali e K = 4, 8, 12 com 17 colunas.
PARAM_GRID = {
    "criterion": ["gini", "entropy"],
    "max_features": [0.25, 0.5, 0.75],
    "max_depth": [12, 16, None],
    "min_samples_leaf": [1, 5, 20],
}
N_SEEDS = 50


def weka_k(n_features):
    """K padrão do Weka: int(log2(n)) + 1. Dá 3 com 5 atributos, 4 com 12 e 5 com 17."""
    return int(math.log2(n_features)) + 1


def estimator(seed, **params):
    """Random Tree sem parâmetros fixados além da semente; o grid decide o resto."""
    return DecisionTreeClassifier(random_state=seed, **params)


def weka_default(seed, n_features):
    """A RandomTree com os padrões do Weka: ganho de informação, K = log2(n) + 1, sem poda."""
    return estimator(seed, criterion="entropy", max_features=weka_k(n_features))


def default_all(dados):
    """Random Tree padrão do Weka nos 6 cenários, sem busca de hiperparâmetros."""
    rows, models = [], {}
    for features, columns in FEATURE_SETS.items():
        for split in modeling.SPLITS:
            X_tr, _, y_tr, _ = modeling._subset(dados, features, split)
            tree = weka_default(dados.seed, len(columns)).fit(X_tr, y_tr)
            models[(features, split)] = tree
            rows.append({"features": features, "split": split, "K": weka_k(len(columns)),
                         **modeling.test_scores(tree, dados, features, split),
                         "folhas": tree.get_n_leaves(), "profundidade": tree.get_depth()})
    return pd.DataFrame(rows), models


def versus_tree(random_tree, decision_tree):
    """Acurácia de teste da Random Tree e da árvore de decisão lado a lado, por cenário."""
    keys = ["features", "split"]
    table = random_tree[keys + ["acurácia teste", "folhas"]].merge(
        decision_tree[keys + ["acurácia teste", "folhas"]], on=keys, suffixes=(" RT", " DT"))
    table["diferença (pontos)"] = ((table["acurácia teste RT"] - table["acurácia teste DT"]) * 100).round(1)
    return table


def max_features_curve(dados, params=None):
    """Treino e validação agrupada para K = 1 a 17 no cenário escolhido.

    `params` fixa os demais hiperparâmetros (em geral os escolhidos pelo grid). K = 17 desliga o
    sorteio: é a árvore de decisão com os mesmos parâmetros.
    """
    n = len(FEATURE_SETS[modeling.CHOSEN[0]])
    values = list(range(1, n + 1))
    params = {k: v for k, v in (params or {}).items() if k != "max_features"}
    curve = modeling._sweep(dados, "max_features", values, None, None, estimator(dados.seed, **params))
    return curve.set_index(pd.Index(values, name="K (atributos sorteados por nó)"))


def seed_variance(dados, params, n=N_SEEDS):
    """Acurácia de teste da mesma Random Tree com `n` sementes diferentes, no mesmo split.

    A semente muda só o sorteio de atributos; dados e split ficam fixos. Também ajusta a árvore de
    decisão com os mesmos parâmetros (sem `max_features`) e as mesmas sementes, como comparação.
    """
    X_tr, X_te, y_tr, y_te = modeling._subset(dados)
    no_k = {k: v for k, v in params.items() if k != "max_features"}
    rows = []
    for seed in range(n):
        for name, model in [("Random Tree", estimator(seed, **params)),
                            ("Árvore de decisão", estimator(seed, **no_k))]:
            model.fit(X_tr, y_tr)
            rows.append({"modelo": name, "semente": seed, "acurácia teste": model.score(X_te, y_te)})
    return pd.DataFrame(rows)


def seed_summary(variance):
    """Média, desvio, mínimo e máximo da acurácia por modelo na varredura de sementes."""
    return variance.groupby("modelo", sort=False)["acurácia teste"].agg(["mean", "std", "min", "max"]).round(4)
