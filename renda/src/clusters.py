"""Clusterização da atividade 5: K-means nos 10 atributos da base de renda, sem ver a renda.

Não há divisão treino/teste: os grupos são formados na base inteira. A renda, a raça e o sexo
entram só depois, para comparar os grupos encontrados.

Pré-processamento: o mesmo da atividade 4 (`avaliacao.preprocessador`, 80 colunas), com uma
opção a mais, o log (`log1p`) no ganho e na perda de capital antes da padronização. Sem ele,
quem tem ganho de 99.999 fica a 13,3 desvios da média e tende a formar um grupo próprio.

Tempos medidos num único núcleo (`threadpool_limits(1)`), como nas outras partes.
"""
from itertools import combinations
from time import perf_counter

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score, silhouette_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler
from threadpoolctl import threadpool_limits

from src import config

CAPITAL = ["capital.gain", "capital.loss"]
KS = list(range(2, 11))
N_INIT = 10
K_ESCOLHIDO = 6  # cotovelo, ARI de 0,995 entre as seeds e quatro perfis para quem não tem capital
AMOSTRA_SILHUETA = 10_000  # a silhueta compara todos os pares; numa amostra fixa, cabe em segundos


def carregar():
    """(X, renda, sensíveis): os 10 atributos, a renda (1 = >50K) e raça e sexo, no mesmo índice."""
    base = pd.read_csv(config.PROCESSED_CSV)
    return base[config.FEATURES], base[config.TARGET], base[config.SENSIVEIS]


def preprocessador(log_capital=True):
    """Padronização dos numéricos e one-hot dos de texto; com `log_capital`, log1p no capital antes."""
    if log_capital:
        outros = [c for c in config.NUMERICAS if c not in CAPITAL]
        numericos = [
            ("numericos", StandardScaler(), outros),
            ("capital", make_pipeline(FunctionTransformer(np.log1p, feature_names_out="one-to-one"),
                                      StandardScaler()), CAPITAL),
        ]
    else:
        numericos = [("numericos", StandardScaler(), config.NUMERICAS)]
    return ColumnTransformer(numericos + [
        ("categoricos", OneHotEncoder(sparse_output=False), config.CATEGORICAS),
    ], verbose_feature_names_out=False)


def transformar(X, log_capital=True):
    """Matriz de 80 colunas usada pelo K-means, como DataFrame (as colunas trazem o nome de origem)."""
    prep = preprocessador(log_capital)
    Z = prep.fit_transform(X)
    return pd.DataFrame(Z, columns=prep.get_feature_names_out(), index=X.index)


def atributo_de(coluna):
    """Atributo original de uma coluna transformada ('occupation_Sales' -> 'occupation')."""
    return next(a for a in config.FEATURES if coluna == a or coluna.startswith(a + "_"))


def peso_na_distancia(Z):
    """Quanto cada atributo contribui, em média, para a distância ao quadrado entre duas pessoas.

    Para duas pessoas sorteadas ao acaso, a esperança de (z_i - z_j)² numa coluna é 2 × variância.
    Somando as colunas de cada atributo: um numérico padronizado dá 2; um categórico dá
    2 × (1 − Σp²), a chance de as duas pessoas terem categorias diferentes vezes o custo da troca.
    """
    contribuicao = (2 * Z.var(ddof=0)).groupby(atributo_de).sum()
    tabela = pd.DataFrame({"contribuição média": contribuicao})
    tabela["parte do total (%)"] = 100 * tabela["contribuição média"] / tabela["contribuição média"].sum()
    tabela["tipo"] = ["numérico" if a in config.NUMERICAS else "categórico" for a in tabela.index]
    return tabela.loc[config.FEATURES].rename(index=config.NOMES)


def kmeans(k, seed, n_init=N_INIT):
    """K-means com k-means++ e `n_init` inicializações; fica com a de menor inércia."""
    return KMeans(n_clusters=k, n_init=n_init, random_state=seed)


def ajustar(Z, k, seed, n_init=N_INIT):
    """Ajusta um K-means num núcleo só. Devolve (modelo, tempo em segundos)."""
    modelo = kmeans(k, seed, n_init)
    with threadpool_limits(1):
        inicio = perf_counter()
        modelo.fit(Z)
        tempo = perf_counter() - inicio
    return modelo, tempo


def metricas_internas(Z, rotulos):
    """Silhueta (numa amostra fixa, a mesma para todo k e seed) e Davies-Bouldin (na base toda)."""
    with threadpool_limits(1):
        silhueta = silhouette_score(Z, rotulos, sample_size=min(AMOSTRA_SILHUETA, len(Z)),
                                    random_state=config.RANDOM_STATE)
        db = davies_bouldin_score(Z, rotulos)
    return silhueta, db


def curvas(Z, ks=None, seeds=None, n_init=N_INIT):
    """Roda o K-means para cada k e seed. Devolve (tabela, rótulos).

    A tabela tem uma linha por k e seed: inércia, silhueta, Davies-Bouldin, iterações e tempo.
    `rotulos[k][seed]` guarda a partição, para medir a estabilidade.
    """
    ks = KS if ks is None else ks
    seeds = config.SEEDS if seeds is None else seeds
    Z = np.asarray(Z)
    ajustar(Z, ks[0], seeds[0], n_init)  # aquecimento, descartado

    linhas, rotulos = [], {k: {} for k in ks}
    for k in ks:
        for seed in seeds:
            modelo, tempo = ajustar(Z, k, seed, n_init)
            silhueta, db = metricas_internas(Z, modelo.labels_)
            rotulos[k][seed] = modelo.labels_
            linhas.append({"k": k, "seed": seed, "n_init": n_init, "inércia": modelo.inertia_,
                           "silhueta": silhueta, "Davies-Bouldin": db,
                           "iterações": modelo.n_iter_, "tempo (s)": tempo})
    return pd.DataFrame(linhas), rotulos


def estabilidade(rotulos):
    """ARI entre as partições de seeds diferentes, para cada k (45 pares com 10 seeds)."""
    linhas = []
    for k, por_seed in rotulos.items():
        aris = [adjusted_rand_score(por_seed[a], por_seed[b]) for a, b in combinations(por_seed, 2)]
        linhas.append({"k": k, "ARI médio": np.mean(aris), "ARI mínimo": np.min(aris), "pares": len(aris)})
    return pd.DataFrame(linhas)


def resumir_curvas(tabela, estab=None):
    """Média e desvio de cada métrica por k; com `estab`, acrescenta a estabilidade."""
    metricas = ["inércia", "silhueta", "Davies-Bouldin", "tempo (s)"]
    resumo = tabela.groupby("k")[metricas].agg(["mean", "std"])
    resumo.columns = [f"{m} ({'média' if e == 'mean' else 'desvio'})" for m, e in resumo.columns]
    if estab is not None:
        resumo = resumo.join(estab.set_index("k")[["ARI médio", "ARI mínimo"]])
    return resumo


def ordenar_por_renda(rotulos, renda):
    """Renumera os grupos de 1 a k, do menor para o maior % >50K.

    O número que o K-means dá a cada grupo é arbitrário e muda com a seed; ordenar pela renda
    deixa as tabelas e figuras mais fáceis de ler. A renda não influencia a formação dos grupos.
    """
    ordem = pd.Series(renda.values).groupby(rotulos).mean().sort_values().index
    novo = {antigo: i + 1 for i, antigo in enumerate(ordem)}
    return np.array([novo[r] for r in rotulos])


def comparar_renda(rotulos, renda):
    """Por grupo: tamanho e % >50K. Mais a pureza e o ARI da partição contra a renda.

    Pureza: cada grupo "responde" sua renda mais comum; é a fração de pessoas que acertariam.
    Como 75,1% ganham até 50 mil, uma partição sem relação com a renda já tem pureza de 75,1%.
    """
    tabela = pd.crosstab(np.asarray(rotulos), np.asarray(renda))
    por_grupo = pd.DataFrame({
        "pessoas": tabela.sum(axis=1),
        "% das pessoas": 100 * tabela.sum(axis=1) / len(renda),
        "% >50K": 100 * tabela[1] / tabela.sum(axis=1),
    }).rename_axis("grupo")
    resumo = {
        "pureza": tabela.max(axis=1).sum() / len(renda),
        "ARI contra a renda": adjusted_rand_score(renda, rotulos),
        "chute (classe majoritária)": renda.value_counts(normalize=True).max(),
    }
    return por_grupo, resumo


def perfil(X, rotulos):
    """Perfil de cada grupo na escala original: média dos numéricos e categoria mais comum (com %).

    A última coluna, "toda a base", serve de referência.
    """
    colunas = {}
    grupos = [(g, X[rotulos == g]) for g in np.unique(rotulos)] + [("toda a base", X)]
    for nome, parte in grupos:
        linha = {"pessoas": len(parte)}
        for c in config.NUMERICAS:
            linha[config.NOMES[c]] = parte[c].mean()
        for c in config.CATEGORICAS:
            freq = parte[c].value_counts(normalize=True)
            linha[config.NOMES[c]] = f"{freq.index[0]} ({100 * freq.iloc[0]:.0f}%)"
        colunas[nome] = linha
    return pd.DataFrame(colunas)


def proporcoes(X, rotulos, atributo):
    """% de cada categoria de um atributo dentro de cada grupo (linhas: categorias)."""
    return 100 * pd.crosstab(X[atributo].values, np.asarray(rotulos), normalize="columns",
                             rownames=[config.NOMES.get(atributo, atributo)], colnames=["grupo"])


def amostra_silhueta(n):
    """Índices da amostra fixa da silhueta: os mesmos que `silhouette_score` sorteia com a mesma seed."""
    return np.random.RandomState(config.RANDOM_STATE).permutation(n)[:min(AMOSTRA_SILHUETA, n)]


def silhueta_por_grupo(Z, rotulos):
    """Silhueta de cada pessoa da amostra fixa, resumida por grupo (média, quartis e % negativa).

    A média geral da amostra é a mesma silhueta de `metricas_internas`.
    """
    from sklearn.metrics import silhouette_samples
    idx = amostra_silhueta(len(Z))
    Z, rotulos = np.asarray(Z)[idx], np.asarray(rotulos)[idx]
    with threadpool_limits(1):
        s = pd.Series(silhouette_samples(Z, rotulos), name="silhueta")
    grupos = s.groupby(rotulos)
    return pd.DataFrame({
        "pessoas na amostra": grupos.size(), "média": grupos.mean(), "1º quartil": grupos.quantile(0.25),
        "mediana": grupos.median(), "3º quartil": grupos.quantile(0.75),
        "% negativa": 100 * grupos.apply(lambda v: (v < 0).mean()),
    }).rename_axis("grupo"), s, rotulos


def resumo_grupos(X, rotulos, renda):
    """Uma linha por grupo: tamanho, médias dos numéricos, % casados, % com capital, ocupação mais comum e % >50K."""
    linhas = []
    for g in np.unique(rotulos):
        m = np.asarray(rotulos) == g
        parte = X[m]
        ocupacao = parte["occupation"].value_counts(normalize=True)
        linhas.append({
            "grupo": g, "pessoas": int(m.sum()), "idade": parte["age"].mean(),
            "anos de estudo": parte["education.num"].mean(), "horas por semana": parte["hours.per.week"].mean(),
            "% casados": 100 * (parte["marital.status"] == "Married-civ-spouse").mean(),
            "% nunca casados": 100 * (parte["marital.status"] == "Never-married").mean(),
            "% com ganho": 100 * (parte["capital.gain"] > 0).mean(),
            "% com perda": 100 * (parte["capital.loss"] > 0).mean(),
            "ocupação mais comum": ocupacao.index[0], "% da ocupação": 100 * ocupacao.iloc[0],
            "% >50K": 100 * np.asarray(renda)[m].mean(),
        })
    return pd.DataFrame(linhas).set_index("grupo")


def curvas_uma_seed(Z, ks=None, seed=config.RANDOM_STATE):
    """Inércia, silhueta, Davies-Bouldin e tamanho do menor grupo para cada k, numa seed só."""
    ks = KS if ks is None else ks
    Z = np.asarray(Z)
    linhas = []
    for k in ks:
        modelo, tempo = ajustar(Z, k, seed)
        silhueta, db = metricas_internas(Z, modelo.labels_)
        linhas.append({"k": k, "inércia": modelo.inertia_, "silhueta": silhueta, "Davies-Bouldin": db,
                       "menor grupo": int(np.bincount(modelo.labels_).min()), "tempo (s)": tempo})
    return pd.DataFrame(linhas)


def pca_2d(Z, seed=config.RANDOM_STATE):
    """Projeção em 2 componentes principais, só para desenhar; devolve (coordenadas, variância explicada)."""
    pca = PCA(n_components=2, random_state=seed)
    return pca.fit_transform(np.asarray(Z)), pca.explained_variance_ratio_
