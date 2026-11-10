"""Rede neural (MLP) da atividade 3: o modelo, a grade de busca e a curva de aprendizado por época."""
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

#: Paciência do early stopping: épocas seguidas sem melhora na validação antes de parar. O padrão
#: do scikit-learn (10) para a rede cedo demais nesta base com a taxa de aprendizado de 0,001.
PACIENCIA = 30

#: Busca em grade: arquitetura (neurônios por camada), regularização L2 e taxa de aprendizado.
GRADE = {
    "mlp__hidden_layer_sizes": [(8,), (16,), (32,), (64,), (32, 16), (64, 32)],
    "mlp__alpha": [1e-4, 1e-2],
    "mlp__learning_rate_init": [1e-3, 1e-2],
}


def rede(camadas=(16,), seed=0, padronizar=True, **parametros):
    """Pipeline com padronização (calculada só com o treino) e MLP com ReLU e otimizador Adam.

    Por padrão usa early stopping com 10% do treino como validação e paciência `PACIENCIA`.
    """
    opcoes = {"early_stopping": True, "n_iter_no_change": PACIENCIA, "max_iter": 1000}
    opcoes.update(parametros)
    mlp = MLPClassifier(hidden_layer_sizes=camadas, random_state=seed, **opcoes)
    passos = [("padronizacao", StandardScaler())] if padronizar else []
    return Pipeline(passos + [("mlp", mlp)])


def curva_por_epoca(X_tr, y_tr, X_val, y_val, camadas=(16,), epocas=300, seed=0, **parametros):
    """Treina uma época por vez (`partial_fit`) e registra perda e acurácia no treino e na validação.

    A padronização é calculada só com `X_tr`. Sem early stopping: a curva mostra o treino inteiro.
    """
    padronizacao = StandardScaler().fit(X_tr)
    A_tr, A_val = padronizacao.transform(X_tr), padronizacao.transform(X_val)
    mlp = MLPClassifier(hidden_layer_sizes=camadas, random_state=seed, **parametros)
    classes = np.unique(y_tr)
    linhas = []
    for epoca in range(1, epocas + 1):
        mlp.partial_fit(A_tr, y_tr, classes=classes)
        linhas.append({
            "época": epoca,
            "perda treino": log_loss(y_tr, mlp.predict_proba(A_tr)),
            "perda validação": log_loss(y_val, mlp.predict_proba(A_val)),
            "acurácia treino": accuracy_score(y_tr, mlp.predict(A_tr)),
            "acurácia validação": accuracy_score(y_val, mlp.predict(A_val)),
        })
    return pd.DataFrame(linhas).set_index("época")


def epoca_de_parada(acuracia_validacao, paciencia, tol=1e-4):
    """Época em que o early stopping pararia: `paciencia` épocas seguidas sem superar o melhor valor
    da validação por mais de `tol` (a mesma regra do scikit-learn)."""
    melhor, sem_melhora = -np.inf, 0
    for epoca, valor in acuracia_validacao.items():
        if valor > melhor + tol:
            melhor, sem_melhora = valor, 0
        else:
            sem_melhora += 1
        if sem_melhora >= paciencia:
            return epoca
    return acuracia_validacao.index[-1]
