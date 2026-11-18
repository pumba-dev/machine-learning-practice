"""Protocolo de avaliação da atividade 4, o mesmo da atividade 3 (emprestimos/src/avaliacao.py).

Para cada seed: divisão estratificada 80/20, ajuste no treino (com validação cruzada estratificada
dentro do treino quando o modelo tem busca de hiperparâmetros) e avaliação única no teste.

Diferenças em relação à atividade 3, por causa da base:
- os atributos de texto viram números por one-hot, e os numéricos são padronizados, num
  `ColumnTransformer` que fica dentro do pipeline de cada modelo (ajustado só no treino);
- a AUC usa `predict_proba` quando o modelo tem, e `decision_function` quando não tem (a SVM);
- além do F1 macro, guarda o F1 da classe >50K, a classe de interesse e a menor.

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
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from threadpoolctl import threadpool_limits

from src import config


def carregar():
    """(X, y) da base processada: os 10 atributos dos modelos e o alvo (1 = ganha >50K).

    Raça e sexo (`config.SENSIVEIS`) ficam de fora; `carregar_sensiveis` os devolve à parte.
    """
    base = pd.read_csv(config.PROCESSED_CSV)
    return base[config.FEATURES], base[config.TARGET]


def carregar_sensiveis():
    """Raça e sexo, com o mesmo índice de `carregar`, para analisar os erros por grupo."""
    return pd.read_csv(config.PROCESSED_CSV)[config.SENSIVEIS]


def preprocessador(padronizar=True):
    """One-hot nos atributos de texto e padronização nos numéricos.

    `handle_unknown="ignore"`: uma categoria rara que só aparece no teste (um país com uma pessoa)
    vira uma linha de zeros em vez de erro. Com `padronizar=False`, os numéricos passam sem mudança.
    """
    numericos = StandardScaler() if padronizar else "passthrough"
    return ColumnTransformer([
        ("numericos", numericos, config.NUMERICAS),
        ("categoricos", OneHotEncoder(handle_unknown="ignore", sparse_output=False), config.CATEGORICAS),
    ])


def dividir(X, y, seed):
    """Divisão estratificada 80/20: treino e teste mantêm a proporção de >50K."""
    return train_test_split(X, y, test_size=config.TEST_SIZE, stratify=y, random_state=seed)


def validacao_cruzada(seed):
    """Validação cruzada estratificada de 5 partes, usada dentro do treino nas buscas em grade."""
    return StratifiedKFold(n_splits=config.CV_FOLDS, shuffle=True, random_state=seed)


def pontuacao(modelo, X):
    """Pontuação contínua para a AUC: probabilidade de >50K, ou a distância à fronteira (SVM)."""
    if hasattr(modelo, "predict_proba"):
        return modelo.predict_proba(X)[:, 1]
    return modelo.decision_function(X)


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
        nota = pontuacao(final, X_te)

    vn, fp, fn, vp = confusion_matrix(y_te, previsto, labels=[0, 1]).ravel()
    metricas = {
        "acurácia": accuracy_score(y_te, previsto),
        "F1 macro": f1_score(y_te, previsto, average="macro"),
        "F1 >50K": f1_score(y_te, previsto, pos_label=1, zero_division=0),
        "AUC": roc_auc_score(y_te, nota),
        "erros": int(fp + fn),
        "falsos positivos": int(fp),
        "falsos negativos": int(fn),
        "tempo de treino (s)": tempo_treino,
        "tempo da busca (s)": tempo_busca,
        "tempo de previsão (ms)": 1000 * tempo_previsao,
    }
    ultimo_passo = final.steps[-1][1] if hasattr(final, "steps") else final
    if hasattr(ultimo_passo, "support_"):  # só a SVM com kernel
        metricas["vetores de suporte"] = int(len(ultimo_passo.support_))
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
    for metrica in ["acurácia", "F1 macro", "F1 >50K", "AUC"]:
        resumo[metrica] = grupos[metrica].mean().mul(100).round(1).astype(str) + " ± " + \
            grupos[metrica].std().mul(100).round(1).astype(str)
    for erro in ["falsos positivos", "falsos negativos"]:
        resumo[erro + " (média)"] = grupos[erro].mean().round(1)
    for tempo in ["tempo de treino (s)", "tempo da busca (s)", "tempo de previsão (ms)"]:
        resumo[tempo + " · mediana"] = grupos[tempo].median().round(4)
    return resumo
