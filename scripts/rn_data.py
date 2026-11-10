"""Números da terceira parte (rede neural na base de empréstimos), para o relatório e a apresentação.

Grava report/results/rn_dados.json, lido por rn_report.py (figuras, tabelas e números do LaTeX) e por
build_slides_rn.py (slides e roteiro). Duas fontes:

- emprestimos/resultados/referencias.csv e rede.csv: as 10 seeds dos notebooks 03 e 04, sem refazer;
- o que os notebooks mostram e não fica em CSV, refeito com as mesmas funções de emprestimos/src:
  a base (notebooks 01 e 02), a padronização (10 seeds), a curva de neurônios, as curvas por época e
  os erros por faixa de score (seed 42).

Uso, a partir da raiz do projeto (cerca de 2 minutos):

    python scripts/rn_data.py
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "emprestimos"))  # o pacote `src` da atividade 3, não o da raiz

from sklearn.exceptions import ConvergenceWarning  # noqa: E402
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split  # noqa: E402
from sklearn.tree import DecisionTreeClassifier  # noqa: E402

from src import avaliacao, config, rede  # noqa: E402

OUT = ROOT / "report" / "results" / "rn_dados.json"
#: Ordem dos modelos nas tabelas e nos slides.
MODELOS = ["classe majoritária", "regra de um corte", "regressão logística", "árvore de decisão", "random forest",
           "rede neural"]
GRADE_ARVORE = {"criterion": ["gini", "entropy"], "max_depth": [3, 5, 8, 12, None], "min_samples_leaf": [1, 5, 20]}
NEURONIOS = [1, 2, 4, 8, 16, 32, 64]
FAIXAS = ([299, 499, 549, 599, 900], ["< 500", "500 a 549", "550 a 599", "≥ 600"])

warnings.filterwarnings("ignore", category=ConvergenceWarning)


def base_block():
    """A base processada: tamanho, classes, o degrau no score e a exceção dos prazos curtos."""
    bruta = pd.read_csv(config.RAW_CSV)
    bruta.columns = bruta.columns.str.strip()
    base = pd.read_csv(config.PROCESSED_CSV)
    score, aprovado = base["cibil_score"], base[config.TARGET]
    faixa = (score // 25) * 25
    por_faixa = aprovado.groupby(faixa).mean()
    abaixo = base[score < 550]
    por_prazo = abaixo.groupby("loan_term")[config.TARGET].mean()
    correlacao = base[config.FEATURES + [config.TARGET]].corr()
    return {
        "linhas": int(len(base)),
        "atributos": len(config.FEATURES),
        "aprovados": float(100 * aprovado.mean()),
        "negativos_residencial": int((bruta["residential_assets_value"] < 0).sum()),
        "regra_550_base": float(100 * ((score >= 550).astype(int) == aprovado).mean()),
        "aprovacao_abaixo_550": float(100 * aprovado[score < 550].mean()),
        "aprovacao_acima_550": float(100 * aprovado[score >= 550].mean()),
        "aprovacao_por_faixa": {int(k): float(100 * v) for k, v in por_faixa.items()},
        # faixas de 50 pontos para os slides; 900, o máximo, entra na faixa de 850
        "aprovacao_por_faixa_50": {int(k): float(100 * v) for k, v in
                                   aprovado.groupby((score.clip(upper=899) // 50) * 50).mean().items()},
        "aprovacao_abaixo_550_por_prazo": {int(k): float(100 * v) for k, v in por_prazo.items()},
        "corr_score_alvo": float(correlacao.loc["cibil_score", config.TARGET]),
        "corr_prazo_alvo": float(correlacao.loc["loan_term", config.TARGET]),
        "corr_renda_valor": float(correlacao.loc["income_annum", "loan_amount"]),
        "corr_renda_luxo": float(correlacao.loc["income_annum", "luxury_assets_value"]),
        "score_quartis": [float(q) for q in score.quantile([0.25, 0.5, 0.75])],
        "score_min_max": [int(score.min()), int(score.max())],
    }


def seeds_block():
    """Os seis modelos nas 10 seeds: média, desvio, tempos e comparações seed a seed."""
    todos = pd.concat([pd.read_csv(config.RESULTS_DIR / "referencias.csv"),
                       pd.read_csv(config.RESULTS_DIR / "rede.csv")], ignore_index=True)
    modelos = {}
    for nome in MODELOS:
        linhas = todos[todos["modelo"] == nome]
        modelos[nome] = {
            "acuracia": float(100 * linhas["acurácia"].mean()),
            "desvio": float(100 * linhas["acurácia"].std()),
            "f1": float(100 * linhas["F1 macro"].mean()),
            "auc": float(100 * linhas["AUC"].mean()),
            "erros": float(linhas["erros"].mean()),
            "treino_ms": float(1000 * linhas["tempo de treino (s)"].median()),
            "busca_s": None if linhas["tempo da busca (s)"].isna().all() else float(linhas["tempo da busca (s)"].median()),
            "previsao_ms": float(linhas["tempo de previsão (ms)"].median()),
        }
    pares = todos.pivot(index="seed", columns="modelo", values="acurácia")

    def comparar(a, b):
        diferenca = 100 * (pares[a] - pares[b])
        return {"pontos": float(diferenca.mean()), "desvio": float(diferenca.std()), "seeds": int((diferenca > 0).sum())}

    comparacoes = {f"{a} × {b}": comparar(a, b) for a, b in [
        ("rede neural", "regra de um corte"), ("rede neural", "regressão logística"),
        ("rede neural", "árvore de decisão"), ("rede neural", "random forest"),
        ("regra de um corte", "regressão logística"), ("árvore de decisão", "regra de um corte"),
        ("random forest", "árvore de decisão")]}

    rn = todos[todos["modelo"] == "rede neural"]
    escolhas = rn["hiperparâmetros"].map(eval)
    camadas = escolhas.map(lambda p: p["mlp__hidden_layer_sizes"])
    return {
        "seeds": int(todos["seed"].nunique()),
        "modelos": modelos,
        "comparacoes": comparacoes,
        "rede": {
            "taxa_001": int(escolhas.map(lambda p: p["mlp__learning_rate_init"] == 0.01).sum()),
            "duas_camadas": int(camadas.map(len).eq(2).sum()),
            "arquiteturas": {"-".join(map(str, k)): int(v) for k, v in camadas.value_counts().items()},
            "alpha": {str(k): int(v) for k, v in escolhas.map(lambda p: p["mlp__alpha"]).value_counts().items()},
            "epocas": [int(rn["épocas"].min()), float(rn["épocas"].median()), int(rn["épocas"].max())],
            "combinacoes": int(np.prod([len(v) for v in rede.GRADE.values()])),
            "combinacoes_arvore": int(np.prod([len(v) for v in GRADE_ARVORE.values()])),
        },
    }


def padronizacao_block(X, y):
    """A mesma rede (16 neurônios) com e sem padronização, nas 10 seeds (notebook 04, seção 2)."""
    def fabrica(seed):
        return {"sem": rede.rede(camadas=(16,), seed=seed, padronizar=False),
                "com": rede.rede(camadas=(16,), seed=seed)}

    resultados = avaliacao.rodar_seeds(fabrica, X, y)
    grupos = resultados.groupby("modelo")
    return {nome: {"acuracia": float(100 * grupos["acurácia"].mean()[nome]),
                   "desvio": float(100 * grupos["acurácia"].std()[nome]),
                   "auc": float(100 * grupos["AUC"].mean()[nome])} for nome in ["sem", "com"]}


def seed42_block(X, y):
    """Primeira rede, curva de neurônios, curvas por época e erros por faixa de score (seed 42)."""
    X_tr, X_te, y_tr, y_te = avaliacao.dividir(X, y, config.RANDOM_STATE)
    cv = avaliacao.validacao_cruzada(config.RANDOM_STATE)

    metricas, primeira = avaliacao.treinar_e_medir(rede.rede(camadas=(16,), seed=0), X_tr, y_tr, X_te, y_te)
    bloco = {"primeira_rede": {"acuracia": 100 * metricas["acurácia"], "erros": metricas["erros"],
                               "epocas": metricas["épocas"]},
             "treino": int(len(X_tr)), "teste": int(len(X_te))}

    bloco["neuronios"] = {"neuronios": NEURONIOS}
    for n_camadas in [1, 2]:
        bloco["neuronios"][f"{n_camadas}_camada"] = [
            float(100 * cross_val_score(rede.rede(camadas=(n,) * n_camadas, seed=0, learning_rate_init=0.01,
                                                  early_stopping=False), X_tr, y_tr, cv=cv, n_jobs=-1).mean())
            for n in NEURONIOS]

    X_sub, X_val, y_sub, y_val = train_test_split(X_tr, y_tr, test_size=0.2, stratify=y_tr, random_state=0)
    curvas, paradas = {}, []
    for taxa in [1e-3, 1e-2]:
        curva = rede.curva_por_epoca(X_sub, y_sub, X_val, y_val, camadas=(32,), epocas=400, seed=0,
                                     learning_rate_init=taxa)
        curvas[str(taxa)] = {coluna: [float(v) for v in curva[coluna]] for coluna in curva}
        for paciencia in [10, 30]:
            epoca = int(rede.epoca_de_parada(curva["acurácia validação"], paciencia))
            paradas.append({"taxa": taxa, "paciencia": paciencia, "epoca": epoca,
                            "acuracia": float(100 * curva.loc[epoca, "acurácia validação"]),
                            "melhor": float(100 * curva["acurácia validação"].max())})
    bloco["epocas"] = {"curvas": curvas, "paradas": paradas}

    melhor_rede = GridSearchCV(rede.rede(seed=0), rede.GRADE, cv=cv, n_jobs=-1).fit(X_tr, y_tr)
    melhor_arvore = GridSearchCV(DecisionTreeClassifier(random_state=0), GRADE_ARVORE, cv=cv, n_jobs=-1).fit(X_tr, y_tr)
    faixa = pd.cut(X_te["cibil_score"], FAIXAS[0], labels=FAIXAS[1])
    excecao = (X_te["cibil_score"] < 550) & (X_te["loan_term"] <= 4)
    erros = {"faixas": FAIXAS[1], "pedidos": [int(v) for v in faixa.value_counts().sort_index()],
             "excecao_pedidos": int(excecao.sum())}
    dispersao = {"score": [int(v) for v in X_te["cibil_score"]], "real": [int(v) for v in y_te]}
    for nome, modelo in {"rede neural": melhor_rede, "árvore de decisão": melhor_arvore}.items():
        erro = pd.Series(modelo.predict(X_te) != y_te.to_numpy(), index=X_te.index)
        erros[nome] = {"por_faixa": [int(v) for v in erro.groupby(faixa, observed=False).sum()],
                       "total": int(erro.sum()), "na_excecao": int((erro & excecao).sum()),
                       "fora_excecao": int((erro & ~excecao).sum()),
                       "parametros": {k: str(v) for k, v in melhor_rede.best_params_.items()}
                       if nome == "rede neural" else {k: str(v) for k, v in melhor_arvore.best_params_.items()}}
        dispersao[nome] = [round(float(p), 4) for p in modelo.predict_proba(X_te)[:, 1]]
    probabilidade = np.array(dispersao["rede neural"])
    perto = (X_te["cibil_score"].to_numpy() >= 500) & (X_te["cibil_score"].to_numpy() < 600)
    erros["rede_intermediarias_500_600"] = float(100 * ((probabilidade > 0.1) & (probabilidade < 0.9))[perto].mean())
    erros["arvore_intermediarias_500_600"] = float(100 * ((np.array(dispersao["árvore de decisão"]) > 0.1)
                                                          & (np.array(dispersao["árvore de decisão"]) < 0.9))[perto].mean())
    bloco["erros"] = erros
    bloco["dispersao"] = dispersao
    return bloco


def main():
    X, y = avaliacao.carregar()
    dados = {"base": base_block(), "multiseed": seeds_block()}
    print("base e 10 seeds: ok")
    dados["padronizacao"] = padronizacao_block(X, y)
    print("padronização:", {k: round(v["acuracia"], 1) for k, v in dados["padronizacao"].items()})
    dados["seed42"] = seed42_block(X, y)
    print("seed 42: ok")
    OUT.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    print("gravado:", OUT)


if __name__ == "__main__":
    main()
