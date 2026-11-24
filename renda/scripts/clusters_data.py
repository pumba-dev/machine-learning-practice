"""Números da quinta parte (K-means na base de renda), para o relatório e a apresentação.

Grava report/results/clusters_dados.json, lido por build_slides_clusters.py (slides e roteiro) e pelo
script do relatório. Fontes:

- renda/resultados/clusters_curvas.csv e clusters_estabilidade.csv: as curvas de k = 2 a 10 nas 10 seeds
  do notebook 07, sem refazer;
- renda/resultados/clusters_grupos.csv e clusters_kmeans.csv: a partição escolhida (k = 6, seed 42);
- renda/resultados/svm.csv: a acurácia da SVM RBF, para comparar com a pureza;
- o que o notebook mostra e não fica em CSV, refeito com as mesmas funções de renda/src/clusters.py: o peso
  de cada atributo na distância, a comparação com e sem log (k = 4, seed 42) e a projeção em 2D (alguns
  segundos).

Uso, a partir da raiz do repositório:

    python renda/scripts/clusters_data.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # o pacote `src` de renda/

from src import clusters, config  # noqa: E402

OUT = ROOT / "report" / "results" / "clusters_dados.json"
RES = config.RESULTS_DIR
PONTOS_PCA = 1500  # pessoas desenhadas no gráfico em 2D (amostra fixa)

#: Nome curto de cada grupo da partição k = 6, seed 42 (renumerados de 1 a 6 pelo % >50K),
#: tirado do perfil no notebook 07. Conferido abaixo pelo tamanho de cada grupo.
NOMES_GRUPOS = {1: "Jovens solteiros", 2: "Mais velhos sem cônjuge", 3: "Casados em ofícios manuais",
                4: "Profissionais com muito estudo", 5: "Com perda de capital", 6: "Com ganho de capital"}
TAMANHOS = {1: 8439, 2: 5443, 3: 6538, 4: 5791, 5: 1427, 6: 2501}


def pct(value):
    return round(100 * float(value), 4)  # arredondar só na exibição, para não arredondar duas vezes


def num(value, digits=4):
    return round(float(value), digits)


def comparar_log(X, renda):
    """k = 4, seed 42, com e sem log: tamanho, % com ganho, % com perda e % >50K de cada grupo."""
    tem_ganho, tem_perda = X["capital.gain"] > 0, X["capital.loss"] > 0
    saida = {}
    for log in (False, True):
        Z = clusters.transformar(X, log_capital=log)
        modelo, _ = clusters.ajustar(Z.values, k=4, seed=config.RANDOM_STATE)
        g = pd.Series(modelo.labels_, index=X.index)
        grupos = []
        for rotulo in g.value_counts().index:  # do maior para o menor
            m = g == rotulo
            grupos.append({"pessoas": int(m.sum()), "com_ganho": pct(tem_ganho[m].mean()),
                           "com_perda": pct(tem_perda[m].mean()), "ganho_medio": num(X.loc[m, "capital.gain"].mean(), 1),
                           "positivos": pct(renda[m].mean())})
        saida["com" if log else "sem"] = {"grupos": grupos, "ganho_max_desvios": num(Z["capital.gain"].max(), 2),
                                           "ganho_zero_desvios": num(Z.loc[~tem_ganho, "capital.gain"].iloc[0], 2)}
    return saida


def main():
    X, renda, _ = clusters.carregar()
    Z = clusters.transformar(X)

    peso = clusters.peso_na_distancia(Z)
    tem_ganho, tem_perda = X["capital.gain"] > 0, X["capital.loss"] > 0
    base = {
        "linhas": len(X), "colunas": Z.shape[1], "positivos": pct(renda.mean()),
        "com_ganho": pct(tem_ganho.mean()), "com_perda": pct(tem_perda.mean()),
        "com_capital": pct((tem_ganho | tem_perda).mean()),
        "ganho_teto": int((X["capital.gain"] == 99999).sum()),
        "desvio_idade": num(X["age"].std(ddof=0), 2),
        # duas pessoas com categorias diferentes ficam a 2 de distância ao quadrado: √2 desvios de um numérico
        "troca_em_anos": num(np.sqrt(2) * X["age"].std(ddof=0), 1),
        "peso": {nome: {"parte": num(linha["parte do total (%)"], 2), "tipo": linha["tipo"]}
                 for nome, linha in peso.iterrows()},
        "parte_categoricos": num(peso.loc[peso["tipo"] == "categórico", "parte do total (%)"].sum(), 2),
    }

    curvas = pd.read_csv(RES / "clusters_curvas.csv")
    estab = pd.read_csv(RES / "clusters_estabilidade.csv")
    c10, c1 = curvas[curvas["n_init"] == clusters.N_INIT], curvas[curvas["n_init"] == 1]
    e10 = estab[estab["n_init"] == clusters.N_INIT].set_index("k")
    e1 = estab[estab["n_init"] == 1].set_index("k")
    media10, desvio10 = c10.groupby("k").mean(numeric_only=True), c10.groupby("k").std(numeric_only=True)
    media1 = c1.groupby("k").mean(numeric_only=True)
    por_k = {}
    for k in clusters.KS:
        por_k[str(k)] = {
            "inercia": num(media10.loc[k, "inércia"], 1), "inercia_desvio": num(desvio10.loc[k, "inércia"], 1),
            "silhueta": num(media10.loc[k, "silhueta"]), "silhueta_desvio": num(desvio10.loc[k, "silhueta"]),
            "db": num(media10.loc[k, "Davies-Bouldin"]), "db_desvio": num(desvio10.loc[k, "Davies-Bouldin"]),
            "ari": num(e10.loc[k, "ARI médio"]), "ari_min": num(e10.loc[k, "ARI mínimo"]),
            "ari_1": num(e1.loc[k, "ARI médio"]), "ari_min_1": num(e1.loc[k, "ARI mínimo"]),
            "inercia_piora_1": num(100 * (media1.loc[k, "inércia"] / media10.loc[k, "inércia"] - 1), 2),
            "tempo_s": num(c10[c10["k"] == k]["tempo (s)"].median(), 3),
            "tempo_1_s": num(c1[c1["k"] == k]["tempo (s)"].median(), 3),
            "iteracoes": num(c10[c10["k"] == k]["iterações"].mean(), 1),
        }
    quedas = {f"{k}-{k + 1}": num(media10.loc[k, "inércia"] - media10.loc[k + 1, "inércia"], 1)
              for k in clusters.KS[:-1]}

    grupos_csv = pd.read_csv(RES / "clusters_grupos.csv", index_col="grupo")
    for g, n in TAMANHOS.items():
        assert grupos_csv.loc[g, "pessoas"] == n, "a partição mudou: revise NOMES_GRUPOS"
    grupos = []
    for g, linha in grupos_csv.iterrows():
        grupos.append({
            "grupo": int(g), "nome": NOMES_GRUPOS[g], "pessoas": int(linha["pessoas"]),
            "parte": num(linha["% das pessoas"], 2), "positivos": num(linha["% >50K"], 2),
            "idade": num(linha["idade"], 1), "estudo": num(linha["anos de estudo"], 1),
            "horas": num(linha["horas por semana"], 1), "ganho": num(linha["ganho de capital"], 1),
            "perda": num(linha["perda de capital"], 1), "com_ganho": num(linha["% com ganho de capital"], 1),
            "com_perda": num(linha["% com perda de capital"], 1),
            **{chave: linha[config.NOMES[col]] for chave, col in [("estado_civil", "marital.status"),
                                                                 ("ocupacao", "occupation"),
                                                                 ("relacionamento", "relationship"),
                                                                 ("classe", "workclass")]},
        })

    km = pd.read_csv(RES / "clusters_kmeans.csv").iloc[0]
    escolha = {"k": int(km["k"]), "seed": int(km["seed"]), "inercia": num(km["inércia"], 1),
               "silhueta": num(km["silhueta"]), "db": num(km["Davies-Bouldin"]), "iteracoes": int(km["iterações"]),
               "tempo_s": num(km["tempo (s)"], 3), "pureza": pct(km["pureza"]),
               "ari_renda": num(km["ARI contra a renda"]), "chute": pct(km["chute (classe majoritária)"])}

    # A mesma partição de novo, para a projeção em 2D e para conferir que bate com o CSV
    modelo, _ = clusters.ajustar(Z.values, escolha["k"], seed=escolha["seed"])
    grupo = clusters.ordenar_por_renda(modelo.labels_, renda)
    assert np.isclose(modelo.inertia_, km["inércia"]), "a partição não bate com clusters_kmeans.csv"
    coords, variancia = clusters.pca_2d(Z)
    amostra = np.random.default_rng(config.RANDOM_STATE).choice(len(Z), PONTOS_PCA, replace=False)
    pca = {"variancia": [pct(v) for v in variancia],
           "centros": {str(g): [num(v, 3) for v in coords[grupo == g].mean(axis=0)] for g in range(1, escolha["k"] + 1)},
           "pontos": {str(g): [[num(x, 3), num(y, 3)] for x, y in coords[amostra][grupo[amostra] == g]]
                      for g in range(1, escolha["k"] + 1)}}

    svm = pd.read_csv(RES / "svm.csv")
    svm_rbf = svm[svm["modelo"] == "SVM RBF"]
    referencia = {"svm_rbf_acuracia": pct(svm_rbf["acurácia"].mean()),
                  "svm_rbf_treino_s": num(svm_rbf["tempo de treino (s)"].median(), 2)}

    dados = {"base": base, "log": comparar_log(X, renda), "por_k": por_k, "quedas_inercia": quedas,
             "escolha": escolha, "grupos": grupos, "pca": pca, "referencia": referencia,
             "estudo_total_ajustes": int(len(curvas))}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    print("gravado:", OUT)


if __name__ == "__main__":
    main()
