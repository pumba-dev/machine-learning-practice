"""Números da quarta parte (SVM na base de renda), para o relatório e a apresentação.

Grava report/results/svm_dados.json, lido por build_slides_svm.py (slides e roteiro) e, depois, pelo
script do relatório. Fontes:

- renda/resultados/referencias.csv, svm.csv e rede.csv: as 10 seeds dos notebooks 03, 05 e 06, sem refazer;
- renda/resultados/svm_mapa.csv e svm_tempo_por_tamanho.csv: o estudo numa seed do notebook 04;
- o que os notebooks mostram e não fica em CSV, refeito com as mesmas funções de renda/src: a curadoria e a
  análise exploratória (notebooks 01 e 02) e, na seed 0 do notebook 04, os kernels com C = 1 e o efeito da
  padronização (cerca de 1 minuto).

Uso, a partir da raiz do repositório:

    python renda/scripts/svm_data.py
"""
import ast
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # o pacote `src` de renda/

from src import avaliacao, config, svm  # noqa: E402

OUT = ROOT / "report" / "results" / "svm_dados.json"
RES = config.RESULTS_DIR
#: Ordem dos modelos nas tabelas e nos slides.
MODELOS = ["classe majoritária", "regra de um corte", "regressão logística", "árvore de decisão", "random forest",
           "SVM linear", "SVM RBF", "SVM polinomial", "SVM RBF com pesos", "rede neural"]
ESTADO_CIVIL = {"Married-civ-spouse": "casado(a)", "Divorced": "divorciado(a)", "Widowed": "viúvo(a)",
                "Separated": "separado(a)", "Never-married": "nunca casou"}


def pct(value):
    return round(100 * float(value), 4)  # arredondar só na exibição, para não arredondar duas vezes


def base_block():
    """Curadoria (notebook 01) e o que a análise exploratória (notebook 02) mostra."""
    bruta = pd.read_csv(config.RAW_CSV)
    sem_dup = bruta.drop_duplicates()
    com_ausente = (sem_dup == "?").any(axis=1)
    base = pd.read_csv(config.PROCESSED_CSV)
    alvo = base[config.TARGET]

    estatisticas = base.groupby(config.FEATURES)[config.TARGET].agg(["nunique", "size", "sum"])
    conflito = estatisticas[estatisticas["nunique"] > 1]
    irredutivel = int(np.minimum(conflito["sum"], conflito["size"] - conflito["sum"]).sum())

    X, y = avaliacao.carregar()
    colunas = avaliacao.preprocessador().fit(X, y).get_feature_names_out()
    numericos = base[config.NUMERICAS].agg(["min", "max"])
    return {
        "brutas": int(len(bruta)),
        "positivos_brutos": pct((bruta[config.TARGET] == config.POSITIVO).mean()),
        "duplicadas": int(len(bruta) - len(sem_dup)),
        "com_ausente": int(com_ausente.sum()),
        "positivos_com_ausente": pct((sem_dup.loc[com_ausente, config.TARGET] == config.POSITIVO).mean()),
        "linhas": int(len(base)),
        "positivos": pct(alvo.mean()),
        "n_positivos": int(alvo.sum()),
        "piso": pct(1 - alvo.mean()),
        "colunas_modelo": int(len(colunas)),
        "correlacao_fnlwgt": round(float(pd.to_numeric(sem_dup.loc[~com_ausente, "fnlwgt"]).corr(
            (sem_dup.loc[~com_ausente, config.TARGET] == config.POSITIVO).astype(int))), 3),
        "perfis_conflito": int(len(conflito)),
        "linhas_conflito": int(conflito["size"].sum()),
        "erros_irredutiveis": irredutivel,
        "teto": round(100 - 100 * irredutivel / len(base), 2),
        "estado_civil": {rotulo: pct(alvo[base["marital.status"] == chave].mean())
                         for chave, rotulo in ESTADO_CIVIL.items()},
        "por_anos_de_estudo": {str(int(k)): pct(v) for k, v in alvo.groupby(base["education.num"]).mean().items()},
        "pessoas_por_anos_de_estudo": {str(int(k)): int(v) for k, v in base["education.num"].value_counts().sort_index().items()},
        "correlacao_alvo": {c: round(float(base[c].corr(alvo)), 3) for c in config.NUMERICAS},
        "repetem_perfil": int(len(base) - len(estatisticas)),
        "faixas": {coluna: [int(numericos.loc["min", coluna]), int(numericos.loc["max", coluna])]
                   for coluna in config.NUMERICAS},
    }


def resultados():
    return pd.concat([pd.read_csv(RES / nome) for nome in ["referencias.csv", "svm.csv", "rede.csv"]],
                     ignore_index=True)


def modelos_block(todos):
    grupos = todos.groupby("modelo")
    saida = {}
    for nome in MODELOS:
        g = grupos.get_group(nome)
        info = {
            "acuracia": pct(g["acurácia"].mean()), "desvio": pct(g["acurácia"].std()),
            "f1": pct(g["F1 macro"].mean()), "desvio_f1": pct(g["F1 macro"].std()),
            "desvio_auc": pct(g["AUC"].std()), "f1_pos": pct(g["F1 >50K"].mean()), "auc": pct(g["AUC"].mean()),
            "fp": round(float(g["falsos positivos"].mean()), 1), "fn": round(float(g["falsos negativos"].mean()), 1),
            "treino_s": round(float(g["tempo de treino (s)"].median()), 4),
            "busca_s": None if g["tempo da busca (s)"].isna().all() else round(float(g["tempo da busca (s)"].median()), 2),
            "previsao_ms": round(float(g["tempo de previsão (ms)"].median()), 2),
        }
        if "vetores de suporte" in g and g["vetores de suporte"].notna().any():
            info["vetores"] = int(round(g["vetores de suporte"].mean()))
        if "épocas" in g and g["épocas"].notna().any():
            info["epocas"] = [int(g["épocas"].min()), int(g["épocas"].max())]
        if info["busca_s"] is not None:
            info["busca_total_min"] = round(float(g["tempo da busca (s)"].sum()) / 60, 1)
        saida[nome] = info
    return saida


def comparacoes_block(todos):
    pares = [("SVM RBF", "SVM linear"), ("SVM RBF", "random forest"), ("SVM RBF", "árvore de decisão"),
             ("SVM polinomial", "SVM RBF"), ("SVM linear", "regressão logística"), ("rede neural", "SVM RBF"),
             ("rede neural", "SVM linear"), ("rede neural", "árvore de decisão"), ("rede neural", "SVM polinomial"),
             ("rede neural", "regressão logística"), ("random forest", "árvore de decisão"),
             ("árvore de decisão", "regressão logística")]
    saida = {}
    for a, b in pares:
        saida[f"{a} × {b}"] = {}
        for chave, metrica in [("acuracia", "acurácia"), ("f1", "F1 macro"), ("auc", "AUC")]:
            tabela = todos.pivot(index="seed", columns="modelo", values=metrica)
            diff = tabela[a] - tabela[b]
            saida[f"{a} × {b}"][chave] = {"pontos": round(100 * float(diff.mean()), 2), "seeds": int((diff > 0).sum())}
    return saida


def escolhas_block(todos):
    """Hiperparâmetros escolhidos pela busca em cada seed."""
    saida = {}
    for nome in ["SVM linear", "SVM RBF", "SVM polinomial", "rede neural"]:
        textos = todos.loc[todos["modelo"] == nome, "hiperparâmetros"].map(ast.literal_eval)
        limpos = textos.map(lambda p: json.dumps({k.split("__")[1]: v for k, v in p.items()}, ensure_ascii=False))
        saida[nome] = {texto: int(n) for texto, n in limpos.value_counts().items()}
    arvore = todos.loc[todos["modelo"] == "árvore de decisão", "hiperparâmetros"].map(ast.literal_eval)
    profundidades = arvore.map(lambda p: p["modelo__max_depth"])
    saida["árvore de decisão"] = {"combinacoes": int(arvore.map(str).nunique()),
                                  "profundidade_min": int(profundidades.dropna().min()),
                                  "sem_limite": int(profundidades.isna().sum())}
    return saida


def gamma_block(todos):
    """SVM RBF: resultado no teste conforme o gamma escolhido pela busca."""
    rbf = todos[todos["modelo"] == "SVM RBF"].copy()
    rbf["gamma"] = rbf["hiperparâmetros"].map(lambda t: ast.literal_eval(t)["modelo__gamma"])
    saida = {}
    for gamma, g in rbf.groupby("gamma"):
        saida[str(gamma)] = {"seeds": int(len(g)), "acuracia": pct(g["acurácia"].mean()), "auc": pct(g["AUC"].mean()),
                             "vetores": int(round(g["vetores de suporte"].mean()))}
    return saida


def mapa_block():
    mapa = pd.read_csv(RES / "svm_mapa.csv")
    tabela = mapa.pivot(index="C", columns="gamma", values="mean_test_score")
    melhor = mapa.loc[mapa["mean_test_score"].idxmax()]
    gamma1 = mapa[(mapa["C"] == 1) & (mapa["gamma"] == 1)].iloc[0]
    return {
        "C": [float(c) for c in tabela.index], "gamma": [float(g) for g in tabela.columns],
        "acuracia": [[pct(v) for v in linha] for linha in tabela.to_numpy()],
        "treino": [[pct(v) for v in linha] for linha in
                   mapa.pivot(index="C", columns="gamma", values="mean_train_score").to_numpy()],
        "tempo_s": [[round(float(v), 2) for v in linha] for linha in
                    mapa.pivot(index="C", columns="gamma", values="mean_fit_time").to_numpy()],
        "melhor": {"C": float(melhor["C"]), "gamma": float(melhor["gamma"]), "acuracia": pct(melhor["mean_test_score"])},
        "perto_do_melhor": int((mapa["mean_test_score"] >= melhor["mean_test_score"] - 0.005).sum()),
        "combinacoes": int(len(mapa)),
        "gamma1_C1": {"treino": pct(gamma1["mean_train_score"]), "validacao": pct(gamma1["mean_test_score"])},
    }


def tempo_block():
    tempos = pd.read_csv(RES / "svm_tempo_por_tamanho.csv")
    saida = {}
    for nome, g in tempos.groupby("modelo"):
        maiores = g[g["n"] >= 4000]  # como no notebook 04: nos tamanhos pequenos, o custo fixo pesa mais
        inclinacao = np.polyfit(np.log(maiores["n"]), np.log(maiores["tempo (s)"]), 1)[0]
        saida[nome] = {"n": g["n"].astype(int).tolist(), "tempo_s": [round(float(t), 4) for t in g["tempo (s)"]],
                       "inclinacao": round(float(inclinacao), 2)}
    return saida


def seed0_block():
    """Kernels com C = 1 e efeito da padronização, na seed 0 (notebook 04)."""
    X, y = avaliacao.carregar()
    X_tr, X_te, y_tr, y_te = avaliacao.dividir(X, y, 0)
    melhor = mapa_block()["melhor"]

    def medir(modelo):
        metricas, _ = avaliacao.treinar_e_medir(modelo, X_tr, y_tr, X_te, y_te)
        return {"acuracia": pct(metricas["acurácia"]), "f1_pos": pct(metricas["F1 >50K"]), "auc": pct(metricas["AUC"]),
                "treino_s": round(metricas["tempo de treino (s)"], 3), "vetores": metricas.get("vetores de suporte")}

    medir(svm.svm())  # aquecimento, descartado
    padrao = svm.svm().fit(X_tr, y_tr)  # RBF, C = 1, gamma padrão: a distância à fronteira (notebook 04, seção 1)
    distancia = padrao.decision_function(X_te)
    margem = {"dentro_da_margem": pct(np.mean(np.abs(distancia) < 1)),
              "vetores_por_classe": [int(v) for v in padrao.named_steps["modelo"].n_support_]}
    kernels = {
        "LinearSVC": medir(svm.svm_linear(C=1)),
        "SVC linear": medir(svm.svm("linear", C=1)),
        "SVC RBF": medir(svm.svm("rbf", C=1)),
        "SVC polinomial grau 2": medir(svm.svm("poly", degree=2, C=1)),
        "SVC polinomial grau 3": medir(svm.svm("poly", degree=3, C=1)),
    }
    parametros = {"C": melhor["C"], "gamma": melhor["gamma"]}
    padronizacao = {
        "RBF com": medir(svm.svm(**parametros)), "RBF sem": medir(svm.svm(padronizar=False, **parametros)),
        "LinearSVC com": medir(svm.svm_linear(C=1)), "LinearSVC sem": medir(svm.svm_linear(padronizar=False, C=1)),
    }
    return {"kernels": kernels, "padronizacao": padronizacao, "margem": margem, "treino": int(len(X_tr)),
            "teste": int(len(X_te)), "positivos_teste": int(y_te.sum())}


def main():
    todos = resultados()
    dados = {
        "base": base_block(),
        "modelos": modelos_block(todos),
        "comparacoes": comparacoes_block(todos),
        "escolhas": escolhas_block(todos),
        "gamma_rbf": gamma_block(todos),
        "mapa": mapa_block(),
        "tempo_por_tamanho": tempo_block(),
        "seed0": seed0_block(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    print("gravado:", OUT)


if __name__ == "__main__":
    main()
