"""Notebook 06: gradient boosting por histogramas.

O gradient boosting também combina muitas árvores, mas em sequência: cada árvore nova corrige o
erro das anteriores, em vez de votar de forma independente como na Random Forest. A versão por
histogramas (`HistGradientBoostingClassifier`) agrupa cada atributo em até 255 faixas antes de
procurar cortes, o que a deixa rápida em bases deste tamanho.

A ordem de uso é a do notebook:

1. `modeling.tune_chosen(dados, estimator(seed), PARAM_GRID)`  busca em grade leve
2. `iterations_curve`  acurácia de treino e validação a cada iteração
3. `modeling.evaluation` / `importances` / `confidence_table`

A parada antecipada (`early_stopping`) fica desligada: ela separa uma validação aleatória do
treino, que deixaria gêmeas de descritores dos dois lados. O número de iterações é fixo e a
curva de iterações mostra se ele basta.
"""
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score

from src import modeling

N_ITER = 300
#: Uma primeira rodada com taxas 0,05 a 0,2 e 15 a 63 folhas escolheu o canto (0,2 e 63); o grid
#: foi deslocado para que o escolhido fique dentro dele, não na borda.
PARAM_GRID = {
    "learning_rate": [0.1, 0.2, 0.3],
    "max_leaf_nodes": [31, 63, 127],
}
STEPS = [1, 5, 10, 25, 50, 100, 150, 200, 250, 300]


def estimator(seed, **params):
    """Gradient boosting com 300 iterações fixas; o grid decide taxa de aprendizado e folhas."""
    return HistGradientBoostingClassifier(max_iter=N_ITER, early_stopping=False, random_state=seed, **params)


def iterations_curve(dados, params=None, steps=STEPS):
    """Acurácia de treino e de validação agrupada depois de cada iteração listada em `steps`."""
    X_fit, X_val, y_fit, y_val = modeling.validation_fold(dados)
    model = estimator(dados.seed, **(params or {})).fit(X_fit, y_fit)
    wanted = set(steps)
    rows = {}
    for i, (train_pred, val_pred) in enumerate(zip(model.staged_predict(X_fit), model.staged_predict(X_val)), start=1):
        if i in wanted:
            rows[i] = {"treino": accuracy_score(y_fit, train_pred), "validação": accuracy_score(y_val, val_pred)}
    return pd.DataFrame.from_dict(rows, orient="index").round(3).rename_axis("iterações")
