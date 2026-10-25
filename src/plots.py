"""Gráficos do projeto, com estilo e cores fixos por classe.

Cada classe tem sempre a mesma cor em todos os gráficos (slots 1 a 4 da paleta
categórica). Chame `set_style()` uma vez antes de plotar.
"""
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.colors import LinearSegmentedColormap

from src.config import ACTIVE_THRESHOLD, CLASSES, FEATURES

CLASS_COLORS = dict(zip(CLASSES, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]))
SERIES_COLOR = "#2a78d6"
CONTEXT_GRAY = "#d6d5ce"
TEXT_PRIMARY = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
SURFACE = "#fcfcfb"
DIVERGING = LinearSegmentedColormap.from_list("diverging", ["#2a78d6", "#f0efec", "#e34948"])


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
