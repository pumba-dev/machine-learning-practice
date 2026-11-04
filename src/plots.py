"""Gráficos do projeto, com estilo e cores fixos por classe.

Cada classe tem sempre a mesma cor em todos os gráficos (slots 1 a 4 da paleta
categórica). Chame `set_style()` uma vez antes de plotar.
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap
from sklearn.tree import plot_tree

from src.config import ACTIVE_THRESHOLD, CLASSES, FEATURES

CLASS_COLORS = dict(zip(CLASSES, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]))
SERIES_COLOR = "#2a78d6"
CONTEXT_GRAY = "#d6d5ce"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
SURFACE = "#fcfcfb"
DIVERGING = LinearSegmentedColormap.from_list("diverging", ["#2a78d6", "#f0efec", "#e34948"])
# Para grandeza que vai de zero a um máximo (contagem, acerto). A DIVERGING é centrada no meio da
# escala e pintaria de neutro valores médios, que aqui não têm nada de neutro.
SEQUENTIAL = LinearSegmentedColormap.from_list("sequential", ["#fcfcfb", "#2a78d6"])


def set_style():
    """Tema visual comum a todos os gráficos."""
    sns.set_theme(style="whitegrid", rc={
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": "#e1e0d9",
        "axes.labelcolor": TEXT_SECONDARY,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "grid.color": "#e1e0d9",
        "grid.linewidth": 0.6,
        "xtick.color": TEXT_SECONDARY,
        "ytick.color": TEXT_SECONDARY,
        "text.color": TEXT_PRIMARY,
        "figure.dpi": 110,
    })


def _thousands(value):
    return f"{value:,}".replace(",", ".")


def potency_histograms(pairs, threshold=ACTIVE_THRESHOLD):
    """Histograma do pChEMBL mediano por alvo, com o limiar de atividade marcado."""
    fig, axes = plt.subplots(1, len(CLASSES), figsize=(14, 3.2), sharex=True, sharey=True)
    for ax, protein in zip(axes, CLASSES):
        values = pairs.loc[pairs["protein"] == protein, "pchembl"]
        ax.hist(values, bins=np.arange(3, 12.25, 0.25), color=CLASS_COLORS[protein], edgecolor=SURFACE, linewidth=0.6)
        ax.axvline(threshold, color=TEXT_PRIMARY, linewidth=1, linestyle="--")
        ax.set_title(f"{protein}  (n = {_thousands(len(values))})")
        ax.set_xlabel("pChEMBL mediano")
    axes[0].set_ylabel("pares molécula-alvo")
    top = axes[0].get_ylim()[1] * 0.92
    axes[0].annotate(f"limiar {threshold:g}", xy=(threshold, top), xytext=(threshold + 0.2, top), color=TEXT_SECONDARY, fontsize=9)
    fig.suptitle("Distribuição da potência por alvo", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    plt.show()


def class_counts(final):
    """Barras horizontais com o número de moléculas por classe."""
    counts = final["Protein"].value_counts().reindex(CLASSES)
    order = CLASSES[::-1]
    fig, ax = plt.subplots(figsize=(7, 2.6))
    ax.barh(order, [counts[c] for c in order], color=[CLASS_COLORS[c] for c in order], height=0.6)
    for y, protein in enumerate(order):
        ax.text(counts[protein] + 100, y, f"{_thousands(counts[protein])}  ({counts[protein] / counts.sum():.1%})", va="center", color=TEXT_SECONDARY, fontsize=9)
    ax.set_xlim(0, counts.max() * 1.25)
    ax.set_xlabel("moléculas")
    ax.grid(axis="y", visible=False)
    ax.set_title("Moléculas por proteína-alvo", loc="left")
    fig.tight_layout()
    plt.show()


def feature_boxplots(final):
    """Um boxplot por feature, com as classes lado a lado (outliers ocultos)."""
    fig, axes = plt.subplots(1, len(FEATURES), figsize=(16, 3.8))
    for ax, feature in zip(axes, FEATURES):
        sns.boxplot(
            data=final, x="Protein", y=feature, order=CLASSES, hue="Protein", hue_order=CLASSES,
            palette=CLASS_COLORS, showfliers=False, width=0.6, linewidth=1, legend=False, ax=ax,
        )
        ax.set_title(feature, loc="left")
        ax.set_xlabel("")
        ax.set_ylabel("")
    fig.suptitle("Features por proteína-alvo (outliers ocultos; caixas = quartis, hastes = 1,5 × IQR)", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    plt.show()


def single_feature_accuracy(accuracy, baseline):
    """Barras com a acurácia de cada feature sozinha e a linha de referência da classe majoritária."""
    fig, ax = plt.subplots(figsize=(7, 3.1))
    ax.barh(accuracy.index, accuracy.tolist(), color=SERIES_COLOR, height=0.6)
    for y, value in enumerate(accuracy.tolist()):
        ax.text(value + 0.005, y, f"{value:.1%}", va="center", color=TEXT_SECONDARY, fontsize=9)
    ax.axvline(baseline, color=TEXT_PRIMARY, linewidth=1, linestyle="--")
    ax.text(baseline + 0.005, -0.85, f"classe majoritária ({baseline:.1%})", color=TEXT_SECONDARY, fontsize=9)
    ax.set_ylim(-1.1, len(accuracy) - 0.5)
    ax.set_xlim(0, 1)
    ax.set_xlabel("acurácia em validação cruzada (árvore de profundidade 3, uma feature)")
    ax.grid(axis="y", visible=False)
    ax.set_title("Quanto cada feature, sozinha, separa os alvos", loc="left")
    fig.tight_layout()
    plt.show()


def correlation_heatmap(complete):
    """Matriz de correlação de Spearman entre as features."""
    correlation = complete[FEATURES].corr(method="spearman")
    fig, ax = plt.subplots(figsize=(5.8, 4.6))
    sns.heatmap(correlation, vmin=-1, vmax=1, cmap=DIVERGING, annot=True, fmt=".2f", square=True,
                linewidths=2, linecolor=SURFACE, cbar_kws={"shrink": 0.8, "label": "correlação de Spearman"}, ax=ax)
    ax.set_title("Correlação entre features", loc="left")
    fig.tight_layout()
    plt.show()


def logp_tpsa_by_class(complete):
    """Dispersão LogP × TPSA, um painel por classe sobre todas as moléculas em cinza."""
    data = complete[(complete["TPSA"] <= 250) & complete["LogP"].between(-2, 10)]
    fig, axes = plt.subplots(1, len(CLASSES), figsize=(16, 4), sharex=True, sharey=True)
    for ax, protein in zip(axes, CLASSES):
        ax.scatter(data["LogP"], data["TPSA"], s=3, color=CONTEXT_GRAY, alpha=0.5, rasterized=True)
        subset = data[data["Protein"] == protein]
        ax.scatter(subset["LogP"], subset["TPSA"], s=3, color=CLASS_COLORS[protein], alpha=0.5, rasterized=True)
        ax.set_title(protein, loc="left")
        ax.set_xlabel("LogP")
    axes[0].set_ylabel("TPSA (Å²)")
    fig.suptitle("Cada painel destaca uma classe sobre todas as moléculas (cinza)", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    plt.show()


def pchembl_by_class(final):
    """Boxplot do pChEMBL por classe."""
    fig, ax = plt.subplots(figsize=(7, 3.2))
    sns.boxplot(data=final, x="Protein", y="pChEMBL", order=CLASSES, hue="Protein", hue_order=CLASSES,
                palette=CLASS_COLORS, showfliers=False, width=0.6, linewidth=1, legend=False, ax=ax)
    ax.set_xlabel("")
    ax.set_title("pChEMBL mediano por proteína-alvo", loc="left")
    fig.tight_layout()
    plt.show()


# --- Notebook 03: árvore de decisão ------------------------------------------------------------

def model_comparison(comparacao, baseline=None):
    """Barras de acurácia por conjunto de features, com os dois splits lado a lado."""
    wide = comparacao.pivot(index="features", columns="split", values="acurácia teste")
    positions = np.arange(len(wide))
    fig, ax = plt.subplots(figsize=(9, 3.4))
    for offset, (split, color) in zip([-0.19, 0.19], [("aleatória", CONTEXT_GRAY), ("agrupada", SERIES_COLOR)]):
        ax.bar(positions + offset, wide[split], width=0.36, color=color, label=f"divisão {split}")
        for x, value in zip(positions + offset, wide[split]):
            ax.text(x, value + 0.015, f"{value:.3f}", ha="center", color=TEXT_SECONDARY, fontsize=9)
    if baseline:
        ax.axhline(baseline, color=TEXT_PRIMARY, linewidth=1, linestyle="--")
        ax.text(-0.45, baseline + 0.03, f"classe majoritária ({baseline:.1%})", color=TEXT_SECONDARY, fontsize=9)
    ax.set_xticks(positions, wide.index)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("acurácia no teste")
    ax.grid(axis="x", visible=False)
    # Acima do gráfico e à direita: as barras passam de 0,9 e cobririam qualquer canto interno,
    # e o título ocupa a esquerda.
    ax.legend(frameon=False, loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=2)
    ax.set_title("Acurácia por conjunto de features e por tipo de divisão", loc="left")
    fig.tight_layout()
    plt.show()


def depth_curve(curva):
    """Acurácia de treino e de validação por profundidade, com a diferença sombreada."""
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.fill_between(curva.index, curva["validação"], curva["treino"], color=CONTEXT_GRAY, alpha=0.6,
                    label="diferença (overfitting)")
    ax.plot(curva.index, curva["treino"], color="#eb6834", linewidth=2, marker="o", markersize=4, label="treino")
    ax.plot(curva.index, curva["validação"], color=SERIES_COLOR, linewidth=2, marker="o", markersize=4, label="validação")
    ax.set_xlabel("profundidade máxima")
    ax.set_ylabel("acurácia")
    ax.set_ylim(0.5, 1.02)
    ax.legend(frameon=False, loc="lower right")
    ax.set_title("A árvore decora o treino, a validação estaciona", loc="left")
    fig.tight_layout()
    plt.show()


def pruning_curve(curva):
    """`ccp_alpha` em escala log contra acurácia, com o número de folhas no eixo da direita."""
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    x = curva.index.to_numpy()
    x = np.where(x == 0, curva.index[curva.index > 0].min() / 3, x)  # zero não existe em escala log
    ax.set_xscale("log")
    ax.plot(x, curva["treino"], color="#eb6834", linewidth=2, marker="o", markersize=4, label="treino")
    ax.plot(x, curva["validação"], color=SERIES_COLOR, linewidth=2, marker="o", markersize=4, label="validação")
    ax.set_xlabel("ccp_alpha (o primeiro ponto é 0, sem poda)")
    ax.set_ylabel("acurácia")
    ax.legend(frameon=False, loc="lower left")
    leaves = ax.twinx()
    leaves.plot(x, curva["folhas"], color=TEXT_SECONDARY, linewidth=1, linestyle=":", marker="s", markersize=3)
    leaves.set_yscale("log")
    leaves.set_ylabel("folhas (linha pontilhada)", color=TEXT_SECONDARY)
    leaves.grid(visible=False)
    ax.set_title("Poda por custo-complexidade", loc="left")
    fig.tight_layout()
    plt.show()


def decision_tree(model, dados=None, feature_names=None, max_depth=2, fontsize=9, label="all"):
    """Desenha só as primeiras camadas da árvore: completa, ela é ilegível."""
    names = feature_names if feature_names is not None else list(dados.X.columns)
    fig, ax = plt.subplots(figsize=(16, 7))
    plot_tree(model, max_depth=max_depth, feature_names=names, class_names=sorted(CLASSES),
              filled=True, proportion=True, rounded=True, impurity=False, fontsize=fontsize, label=label, ax=ax)
    ax.set_title(f"Primeiras {max_depth} camadas da árvore escolhida", loc="left")
    fig.tight_layout()
    plt.show()


def feature_importances(tabela):
    """Importância por impureza e por permutação, na mesma ordem de features.

    Sem importância por impureza (coluna toda NaN, caso do gradient boosting), só o painel da permutação.
    """
    if tabela["impureza"].isna().all():
        fig, ax = plt.subplots(figsize=(7, 4.6))
        axes = [ax]
    else:
        fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), sharey=True)
        axes[0].barh(tabela.index, tabela["impureza"], color=SERIES_COLOR, height=0.7)
        axes[0].set_title("Por impureza (durante o treino)", loc="left")
    axes[-1].barh(tabela.index, tabela["permutação"], xerr=tabela["desvio"], color=SERIES_COLOR, height=0.7,
                  error_kw={"ecolor": TEXT_SECONDARY, "elinewidth": 1})
    axes[-1].set_title("Por permutação (no teste)", loc="left")
    for ax in axes:
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("queda de desempenho atribuída à feature")
    fig.suptitle("Importância das features", x=0.01, ha="left", fontweight="bold")
    fig.tight_layout()
    plt.show()


def learning_curve(curva):
    """Acurácia de treino e de validação por tamanho do conjunto de treino."""
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.fill_between(curva.index, curva["validação"], curva["treino"], color=CONTEXT_GRAY, alpha=0.6,
                    label="diferença (overfitting)")
    ax.plot(curva.index, curva["treino"], color="#eb6834", linewidth=2, marker="o", markersize=4, label="treino")
    ax.plot(curva.index, curva["validação"], color=SERIES_COLOR, linewidth=2, marker="o", markersize=4, label="validação")
    ax.set_xlabel("linhas de treino")
    ax.set_ylabel("acurácia")
    ax.set_ylim(0.5, 1.02)
    ax.legend(frameon=False, loc="lower right")
    ax.set_title("A validação ainda sobe quando os dados acabam", loc="left")
    fig.tight_layout()
    plt.show()


def error_pairs(tabela, top=8, title="Onde a árvore erra"):
    """Barras dos pares de confusão mais frequentes, coloridas pela classe real."""
    data = tabela.head(top).iloc[::-1]
    labels = data["real"] + " lido como " + data["prevista"]
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    ax.barh(labels, data["erros"], color=[CLASS_COLORS[c] for c in data["real"]], height=0.7)
    for y, (count, share) in enumerate(zip(data["erros"], data["% dos erros"])):
        ax.text(count + 1.5, y, f"{count}  ({share}%)", va="center", color=TEXT_SECONDARY, fontsize=9)
    ax.set_xlim(0, data["erros"].max() * 1.25)
    ax.set_xlabel("erros no conjunto de teste")
    ax.grid(axis="y", visible=False)
    ax.set_title(title, loc="left")
    fig.tight_layout()
    plt.show()


def confusion_matrix(matriz):
    """Matriz de confusão: cor pela proporção da linha, número em contagem bruta."""
    share = matriz.div(matriz.sum(axis=1), axis=0)
    labels = matriz.map(lambda v: f"{v:,}".replace(",", "."))
    fig, ax = plt.subplots(figsize=(6, 4.8))
    sns.heatmap(share, cmap=SEQUENTIAL, vmin=0, vmax=1, annot=labels, fmt="", square=True,
                linewidths=2, linecolor=SURFACE, cbar_kws={"shrink": 0.8, "label": "proporção da classe real"}, ax=ax)
    ax.set_title("Matriz de confusão no conjunto de teste", loc="left")
    fig.tight_layout()
    plt.show()


# --- Notebooks 04 a 07: Random Tree, conjuntos de árvores e comparação ---------------------------

TRAIN_COLOR = "#eb6834"


def _train_val(ax, curva, x=None):
    """Linhas de treino (se houver) e validação, com a diferença sombreada."""
    x = curva.index if x is None else x
    if "treino" in curva:
        ax.fill_between(x, curva["validação"], curva["treino"], color=CONTEXT_GRAY, alpha=0.6,
                        label="diferença (overfitting)")
        ax.plot(x, curva["treino"], color=TRAIN_COLOR, linewidth=2, marker="o", markersize=4, label="treino")
    ax.plot(x, curva["validação"], color=SERIES_COLOR, linewidth=2, marker="o", markersize=4, label="validação")


def max_features_curve(curva, weka_k=None):
    """Acurácia de treino e de validação por K, com o K do Weka e o K = todos (árvore de decisão) marcados."""
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    _train_val(ax, curva)
    best = curva["validação"].idxmax()
    # Rótulos na horizontal, na faixa vazia abaixo da validação: o do Weka à direita da linha, o da
    # árvore de decisão à esquerda da última linha.
    marks = [(curva.index.max(), "sem sorteio = árvore de decisão ", "right")]
    if weka_k is not None:
        marks.append((weka_k, f" padrão do Weka (K = {weka_k})", "left"))
    for k, text, align in marks:
        ax.axvline(k, color=TEXT_SECONDARY, linewidth=1, linestyle=":")
        ax.text(k, 0.715, text, color=TEXT_SECONDARY, fontsize=8, va="bottom", ha=align)
    ax.annotate(f"melhor validação: K = {best} ({curva.loc[best, 'validação']:.3f})",
                (best, curva.loc[best, "validação"]), xytext=(0, -24), textcoords="offset points",
                ha="center", color=TEXT_SECONDARY, fontsize=8, arrowprops={"arrowstyle": "-", "color": TEXT_SECONDARY})
    ax.set_xticks(curva.index)
    ax.set_xlabel(curva.index.name)
    ax.set_ylabel("acurácia")
    ax.set_ylim(0.7, 1.02)
    ax.legend(frameon=False, loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=3)
    ax.set_title("Quantos atributos sortear em cada nó", loc="left", pad=22)
    fig.tight_layout()
    plt.show()


def seed_variance(variancia):
    """Acurácia de teste por semente: uma linha de pontos por modelo, com a média marcada."""
    models = list(dict.fromkeys(variancia["modelo"]))
    colors = {models[0]: SERIES_COLOR, **{m: TEXT_SECONDARY for m in models[1:]}}
    rng = np.random.default_rng(0)
    fig, ax = plt.subplots(figsize=(7.5, 2.9))
    for y, model in enumerate(models):
        values = variancia.loc[variancia["modelo"] == model, "acurácia teste"]
        ax.scatter(values, y + rng.uniform(-0.12, 0.12, len(values)), s=36, color=colors[model],
                   edgecolor=SURFACE, linewidth=1, alpha=0.85)
        ax.plot([values.mean()] * 2, [y - 0.25, y + 0.25], color=TEXT_PRIMARY, linewidth=2)
        ax.text(values.mean(), y + 0.3, f"média {values.mean():.3f}  (de {values.min():.3f} a {values.max():.3f})",
                ha="center", color=TEXT_SECONDARY, fontsize=8)
    ax.set_yticks(range(len(models)), models)
    ax.set_ylim(-0.6, len(models) - 0.15)
    ax.set_xlabel("acurácia no teste (mesmo split, só a semente muda)")
    ax.grid(axis="y", visible=False)
    ax.set_title(f"A mesma configuração com {variancia['semente'].nunique()} sementes", loc="left")
    fig.tight_layout()
    plt.show()


def n_trees_curve(curva):
    """Acurácia de validação por número de árvores da floresta, em escala log."""
    fig, ax = plt.subplots(figsize=(7.5, 3.4))
    ax.set_xscale("log")
    _train_val(ax, curva)
    last = curva.index[-1]
    ax.text(last, curva.loc[last, "validação"] - 0.012, f"{curva.loc[last, 'validação']:.3f}",
            ha="center", va="top", color=TEXT_SECONDARY, fontsize=9)
    ax.set_xticks(curva.index, [str(n) for n in curva.index])
    ax.minorticks_off()
    ax.set_xlabel("árvores na floresta")
    ax.set_ylabel("acurácia de validação")
    ax.set_title("Acurácia por número de árvores", loc="left")
    fig.tight_layout()
    plt.show()


def iterations_curve(curva):
    """Acurácia de treino e de validação por iteração do boosting."""
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    _train_val(ax, curva)
    ax.set_xlabel("iterações (árvores somadas)")
    ax.set_ylabel("acurácia")
    ax.set_ylim(0.75, 1.02)
    ax.legend(frameon=False, loc="lower right")
    ax.set_title("Acurácia por iteração do boosting", loc="left")
    fig.tight_layout()
    plt.show()


def bridge(matriz):
    """Desenho 2×2: barras por sorteio de atributos, 1 árvore em cinza e o conjunto em azul."""
    rows = ["sem sorteio", "com sorteio"]
    cols = list(matriz.columns)  # "1 árvore", "300 árvores"
    positions = np.arange(len(rows))
    labels = {"sem sorteio": "sem sorteio de atributos", "com sorteio": "com sorteio de atributos"}
    names = {("sem sorteio", cols[0]): "Árvore de decisão", ("com sorteio", cols[0]): "Random Tree",
             ("sem sorteio", cols[1]): "Bagging", ("com sorteio", cols[1]): "Random Forest"}
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    for offset, (col, color) in zip([-0.19, 0.19], [(cols[0], CONTEXT_GRAY), (cols[1], SERIES_COLOR)]):
        values = matriz.loc[rows, col]
        ax.bar(positions + offset, values, width=0.36, color=color, label=col)
        for x, row, value in zip(positions + offset, rows, values):
            ax.text(x, value + 0.4, f"{value:.1f}%", ha="center", color=TEXT_PRIMARY, fontsize=9)
            ax.text(x, 80.5, names[(row, col)], ha="center", va="bottom", rotation=90,
                    color=TEXT_PRIMARY if color == CONTEXT_GRAY else SURFACE, fontsize=8)
    ax.set_xticks(positions, [labels[r] for r in rows])
    ax.set_ylim(80, 100)
    ax.set_ylabel("acurácia no teste (%)\neixo a partir de 80")
    ax.grid(axis="x", visible=False)
    ax.legend(frameon=False, loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=2)
    ax.set_title("De onde vem o ganho da Random Forest", loc="left", pad=22)
    fig.tight_layout()
    plt.show()


def bridge_curve(curva):
    """Acurácia de validação por número de árvores, bagging contra Random Forest, com rótulo no fim da linha."""
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.set_xscale("log")
    for column, color in zip(curva.columns, [TEXT_SECONDARY, SERIES_COLOR]):
        ax.plot(curva.index, curva[column], color=color, linewidth=2, marker="o", markersize=4, label=column)
        ax.text(curva.index[-1] * 1.15, curva[column].iloc[-1], f"{curva[column].iloc[-1]:.3f}",
                va="center", color=TEXT_PRIMARY, fontsize=8)
    ax.set_xticks(curva.index, [str(n) for n in curva.index])
    ax.minorticks_off()
    ax.set_xlim(curva.index[0] * 0.8, curva.index[-1] * 2)
    ax.set_xlabel("árvores")
    ax.set_ylabel("acurácia de validação")
    ax.legend(frameon=False, loc="lower right")
    ax.set_title("Bagging e Random Forest por número de árvores", loc="left")
    fig.tight_layout()
    plt.show()


def models_summary(tabela, low=None):
    """Barras horizontais com a acurácia média de cada modelo e o desvio entre seeds."""
    data = tabela.iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 0.42 * len(data) + 1.2))
    ax.barh(data.index, data["acurácia (%)"], xerr=data["desvio (pontos)"], color=SERIES_COLOR, height=0.65,
            error_kw={"ecolor": TEXT_PRIMARY, "elinewidth": 1, "capsize": 2})
    for y, (value, sd) in enumerate(zip(data["acurácia (%)"], data["desvio (pontos)"])):
        ax.text(value + sd + 0.2, y, f"{value:.1f} ± {sd:.1f}", va="center", color=TEXT_SECONDARY, fontsize=8)
    low = 80 if low is None else low
    ax.set_xlim(low, 100)
    ax.set_xlabel(f"acurácia no teste (%), média das seeds; eixo a partir de {low}")
    ax.grid(axis="y", visible=False)
    ax.set_title("Todos os modelos no mesmo cenário", loc="left")
    fig.tight_layout()
    plt.show()


def tree_to_forest(ponte):
    """Árvore de decisão, Random Tree e Random Forest lado a lado: o sorteio de atributos numa árvore só e
    em 300 árvores. `ponte` é a tabela de `comparison.bridge`; a célula sem sorteio com 300 árvores fica de fora.
    As árvores únicas mostram a média e o desvio entre sementes."""
    rows = [("sem sorteio", "1 árvore", "Árvore de decisão", CONTEXT_GRAY),
            ("com sorteio", "1 árvore", "Random Tree", CONTEXT_GRAY),
            ("com sorteio", ponte["árvores"].iloc[-1], "Random Forest", SERIES_COLOR)]
    values, errors = [], []
    for sorteio, arvores, _, _ in rows:
        row = ponte[(ponte["sorteio de atributos"] == sorteio) & (ponte["árvores"] == arvores)].iloc[0]
        values.append(row["acurácia teste"] * 100)
        sd = row["desvio entre sementes"]
        errors.append(0 if pd.isna(sd) else sd * 100)
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    positions = np.arange(len(rows))
    ax.bar(positions, values, yerr=errors, width=0.6, color=[r[3] for r in rows],
           error_kw={"ecolor": TEXT_PRIMARY, "elinewidth": 1, "capsize": 3})
    for x, value, sd in zip(positions, values, errors):
        ax.text(x, value + sd + 0.6, f"{value:.1f}%", ha="center", va="bottom", color=TEXT_PRIMARY, fontsize=9)
    ax.set_xticks(positions, [r[2] for r in rows])
    ax.set_ylim(80, 100)
    ax.set_ylabel("acurácia no teste (%)\neixo a partir de 80")
    ax.grid(axis="x", visible=False)
    ax.set_title("Sorteio de atributos numa árvore e em 300", loc="left")
    fig.tight_layout()
    plt.show()
