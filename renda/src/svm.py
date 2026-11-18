"""SVM da atividade 4: fábricas dos modelos e grades de busca."""
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC, LinearSVC

from src import avaliacao

#: Mapa C × gamma do kernel RBF, explorado numa seed só (notebook 04). O gamma padrão do
#: scikit-learn ("scale") vale cerca de 0,10 nesta base, perto do meio da faixa.
GRADE_MAPA = {
    "modelo__C": [0.01, 0.1, 1, 10, 100],
    "modelo__gamma": [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1],
}

#: Grade do RBF para a comparação em 10 seeds (notebook 05), escolhida a partir do mapa: cobre o
#: platô de cerca de 85% e deixa de fora gamma = 1 (sobreajuste, treino mais caro) e C = 0,01
#: (subajuste).
GRADE_RBF = {
    "modelo__C": [0.1, 1, 10, 100],
    "modelo__gamma": [0.01, 0.03, 0.1, 0.3],
}

#: SVM linear (LinearSVC): só o C. Treina em décimos de segundo, então a grade pode ser larga.
GRADE_LINEAR = {"modelo__C": [0.001, 0.01, 0.1, 1, 10]}

#: Kernel polinomial: grau e C (coef0 fixo em 1).
GRADE_POLI = {"modelo__degree": [2, 3], "modelo__C": [0.1, 1, 10]}


def svm(kernel="rbf", padronizar=True, **parametros):
    """Pipeline com o pré-processamento (one-hot + padronização) e a SVC.

    No kernel polinomial, coef0 = 1: com o padrão do scikit-learn (0), o grau 2 só teria os
    produtos de pares de atributos, sem os termos lineares.
    """
    if kernel == "poly":
        parametros.setdefault("coef0", 1)
    return Pipeline([
        ("prep", avaliacao.preprocessador(padronizar)),
        ("modelo", SVC(kernel=kernel, **parametros)),
    ])


def svm_linear(padronizar=True, **parametros):
    """Pipeline com o pré-processamento e a LinearSVC, a SVM linear de treino rápido."""
    opcoes = {"max_iter": 10000}
    opcoes.update(parametros)
    return Pipeline([
        ("prep", avaliacao.preprocessador(padronizar)),
        ("modelo", LinearSVC(**opcoes)),
    ])
