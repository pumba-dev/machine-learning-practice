"""Notebook 05: Random Forest.

Uma Random Forest é a média de muitas Random Trees, cada uma treinada numa amostra bootstrap do
treino. Aqui ela é ajustada só no cenário escolhido (descritores + SMILES, divisão agrupada), com o
mesmo protocolo de validação agrupada da árvore de decisão.

A ordem de uso é a do notebook:

1. `modeling.tune_chosen(dados, estimator(seed), PARAM_GRID)`  busca em grade leve
2. `n_trees_curve`  acurácia de validação por número de árvores
3. `modeling.evaluation` / `importances` / `confidence_table`  as mesmas análises da árvore

O erro out-of-bag (OOB) não é usado: as amostras fora da bolsa ignoram os grupos de descritores
repetidos, então uma molécula teria a gêmea no treino da árvore que a avalia.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

from src import modeling

N_TREES = 300
#: `max_features` com 17 colunas: 0,15 -> K = 2, "sqrt" -> K = 4, 0,5 -> K = 8. Uma primeira rodada
#: também testou `max_depth=20`, que nunca superou a árvore sem limite e saiu do grid.
PARAM_GRID = {
    "max_features": [0.15, "sqrt", 0.5],
    "min_samples_leaf": [1, 3],
}
TREE_COUNTS = [1, 2, 5, 10, 25, 50, 100, 200, 300]


def estimator(seed, **params):
    """Random Forest com 300 árvores; o grid decide o resto."""
    return RandomForestClassifier(n_estimators=N_TREES, random_state=seed, n_jobs=-1, **params)


def staged_accuracy(forest, X, y, counts):
    """Acurácia das primeiras n árvores de uma floresta já ajustada, para cada n em `counts`.

    A floresta faz a média das probabilidades das árvores, então basta acumular `predict_proba`
    árvore a árvore em vez de treinar uma floresta por tamanho.
    """
    total, scores, wanted = np.zeros((len(X), len(forest.classes_))), {}, set(counts)
    values = X.to_numpy(dtype=np.float32)
    for i, tree in enumerate(forest.estimators_, start=1):
        total += tree.predict_proba(values)
        if i in wanted:
            scores[i] = accuracy_score(y, forest.classes_[total.argmax(axis=1)])
    return pd.Series(scores)


def n_trees_curve(dados, params=None, counts=TREE_COUNTS):
    """Acurácia de validação agrupada por número de árvores, com os hiperparâmetros dados."""
    X_fit, X_val, y_fit, y_val = modeling.validation_fold(dados)
    forest = estimator(dados.seed, **(params or {})).set_params(n_estimators=max(counts)).fit(X_fit, y_fit)
    curve = staged_accuracy(forest, X_val, y_val, counts).round(3)
    return curve.rename("validação").rename_axis("árvores").to_frame()
