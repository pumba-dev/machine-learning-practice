"""Rede neural (MLP) da base de renda: a mesma configuração e a mesma grade da atividade 3
(`emprestimos/src/rede.py`), com o pré-processamento desta base (one-hot + padronização)."""
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline

from src import avaliacao

#: Paciência do early stopping (épocas seguidas sem melhora na validação), a mesma da atividade 3.
PACIENCIA = 30

#: Busca em grade da atividade 3: arquitetura, regularização L2 e taxa de aprendizado.
GRADE = {
    "mlp__hidden_layer_sizes": [(8,), (16,), (32,), (64,), (32, 16), (64, 32)],
    "mlp__alpha": [1e-4, 1e-2],
    "mlp__learning_rate_init": [1e-3, 1e-2],
}


def rede(seed=0, camadas=(16,), **parametros):
    """Pipeline com o pré-processamento e uma MLP com ReLU e otimizador Adam.

    Early stopping com 10% do treino como validação e paciência `PACIENCIA`.
    """
    opcoes = {"hidden_layer_sizes": camadas, "early_stopping": True,
              "n_iter_no_change": PACIENCIA, "max_iter": 1000}
    opcoes.update(parametros)
    return Pipeline([
        ("prep", avaliacao.preprocessador()),
        ("mlp", MLPClassifier(random_state=seed, **opcoes)),
    ])
