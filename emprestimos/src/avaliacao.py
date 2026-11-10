"""Protocolo de avaliação da atividade 3, usado pelos pontos de referência e pela rede neural.

Para cada seed: divisão estratificada 80/20, ajuste no treino (com validação cruzada estratificada
dentro do treino quando o modelo tem busca de hiperparâmetros) e avaliação única no teste.

Medição de tempo, para comparar algoritmos e não núcleos de processador:
- tudo roda com um único núcleo (`n_jobs=1` e `threadpool_limits(1)`, que limita também as
  bibliotecas de álgebra linear usadas pelo numpy);
- uma rodada de aquecimento é feita e descartada antes da primeira medição;
- o tempo de treino é o do modelo final; numa busca em grade, o tempo da busca é medido à parte,
  e o modelo final é treinado de novo com os hiperparâmetros escolhidos para medir só o treino;
- o resumo usa a mediana das seeds, menos sensível a uma medição isolada com o computador ocupado.
"""
from time import perf_counter

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from threadpoolctl import threadpool_limits

from src import config


def carregar():
    """(X, y) da base processada: os 11 atributos e o alvo (1 = aprovado)."""
    base = pd.read_csv(config.PROCESSED_CSV)
    return base[config.FEATURES], base[config.TARGET]


def dividir(X, y, seed):
    """Divisão estratificada 80/20: treino e teste mantêm a proporção de aprovados."""
    return train_test_split(X, y, test_size=config.TEST_SIZE, stratify=y, random_state=seed)


def validacao_cruzada(seed):
    """Validação cruzada estratificada de 5 partes, usada dentro do treino nas buscas em grade."""
    return StratifiedKFold(n_splits=config.CV_FOLDS, shuffle=True, random_state=seed)


def treinar_e_medir(modelo, X_tr, y_tr, X_te, y_te):
    """Treina, mede os tempos e avalia no teste. Devolve (métricas, modelo final treinado)."""
    with threadpool_limits(1):
        inicio = perf_counter()
        modelo.fit(X_tr, y_tr)
        tempo_fit = perf_counter() - inicio

        if hasattr(modelo, "best_estimator_"):
            tempo_busca = tempo_fit
            final = clone(modelo.best_estimator_)
            inicio = perf_counter()
            final.fit(X_tr, y_tr)
            tempo_treino = perf_counter() - inicio
        else:
            tempo_busca, final, tempo_treino = np.nan, modelo, tempo_fit

        inicio = perf_counter()
        previsto = final.predict(X_te)
        tempo_previsao = perf_counter() - inicio
        probabilidade = final.predict_proba(X_te)[:, 1]

    metricas = {
        "acurácia": accuracy_score(y_te, previsto),
        "F1 macro": f1_score(y_te, previsto, average="macro"),
        "AUC": roc_auc_score(y_te, probabilidade),
        "erros": int((previsto != y_te.to_numpy()).sum()),
        "tempo de treino (s)": tempo_treino,
        "tempo da busca (s)": tempo_busca,
        "tempo de previsão (ms)": 1000 * tempo_previsao,
    }
    ultimo_passo = final.steps[-1][1] if hasattr(final, "steps") else final
    if isinstance(getattr(ultimo_passo, "n_iter_", None), (int, np.integer)):  # só a rede neural
        metricas["épocas"] = int(ultimo_passo.n_iter_)
    if hasattr(modelo, "best_params_"):
        metricas["hiperparâmetros"] = str(modelo.best_params_)
    return metricas, final


def rodar_seeds(fabrica, X, y, seeds=None, aquecer=True):
    """Roda todos os modelos de `fabrica(seed)` em cada seed. Devolve uma linha por seed e modelo.

    `fabrica` é uma função que recebe a seed e devolve um dicionário {nome: modelo novo}, para que
    cada seed comece com modelos sem treino.
    """
    seeds = config.SEEDS if seeds is None else seeds
    if aquecer:
        X_tr, X_te, y_tr, y_te = dividir(X, y, seeds[0])
        for modelo in fabrica(seeds[0]).values():
            treinar_e_medir(modelo, X_tr, y_tr, X_te, y_te)

    linhas = []
    for seed in seeds:
        X_tr, X_te, y_tr, y_te = dividir(X, y, seed)
        for nome, modelo in fabrica(seed).items():
            metricas, _ = treinar_e_medir(modelo, X_tr, y_tr, X_te, y_te)
            linhas.append({"seed": seed, "modelo": nome, **metricas})
    return pd.DataFrame(linhas)


def resumir(resultados):
    """Média ± desvio das métricas de acerto e mediana dos tempos, por modelo."""
    grupos = resultados.groupby("modelo", sort=False)
    resumo = pd.DataFrame(index=grupos.size().index)
    for metrica in ["acurácia", "F1 macro", "AUC"]:
        resumo[metrica] = grupos[metrica].mean().mul(100).round(1).astype(str) + " ± " + \
            grupos[metrica].std().mul(100).round(1).astype(str)
    resumo["erros (média)"] = grupos["erros"].mean().round(1)
    for tempo in ["tempo de treino (s)", "tempo da busca (s)", "tempo de previsão (ms)"]:
        resumo[tempo + " · mediana"] = grupos[tempo].median().round(4)
    return resumo
