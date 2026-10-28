"""Exporta para report/figures/ as figuras dos notebooks 02 e 03, no tamanho final do relatório.

As funções de `src/plots.py` terminam em `plt.show()`; aqui `show` é trocado por um `savefig`, então
os gráficos são exatamente os dos notebooks. O que muda para o papel: tamanho em polegadas (largura
útil do template SBC = 15 cm), fonte menor, fundo branco e sem título dentro da figura, porque a
legenda do LaTeX faz esse papel. Títulos de painel (nome da feature, da classe) ficam.

Uso, a partir da raiz do projeto:

    python scripts/export_figures.py            # PDF em report/figures/
    python scripts/export_figures.py --png      # também PNG, para conferir a olho

Sobre a seed: usa a padrão (42), a mesma dos notebooks. A tabela com várias seeds sai de multiseed.py.
"""
import argparse
import sys
from contextlib import contextmanager
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import PercentFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import eda, modeling, plots  # noqa: E402
from src.config import FINAL_CSV  # noqa: E402

OUT_DIR = ROOT / "report" / "figures"

FULL = 5.9  # largura do texto em polegadas (15 cm)
HALF = 2.85  # duas figuras lado a lado

# nome da função em plots -> (largura, altura) em polegadas
SIZES = {
    "class_counts": (HALF, 1.7),
    "feature_boxplots": (FULL, 2.2),
    "single_feature_accuracy": (HALF, 2.0),
    "correlation_heatmap": (HALF, 2.5),
    "logp_tpsa_by_class": (FULL, 1.9),
    "model_comparison": (FULL, 2.5),
    "depth_curve": (HALF, 2.1),
    "pruning_curve": (HALF, 2.1),
    "decision_tree": (FULL, 3.0),
    "feature_importances": (FULL, 2.6),
    "confusion_matrix": (HALF, 2.2),
    "learning_curve": (HALF, 2.2),
    "error_pairs": (HALF, 2.3),
}

#: Figuras com vários painéis: o título de cada painel (feature, classe, medida) fica; nas demais
#: o título é a legenda do LaTeX.
PANEL_TITLES = {"feature_boxplots", "logp_tpsa_by_class", "feature_importances"}

REPORT_RC = {
    "font.size": 8,
    "axes.titlesize": 8.5,
    "axes.labelsize": 8,
    "xtick.labelsize": 7.5,
    "ytick.labelsize": 7.5,
    "legend.fontsize": 7.5,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
}


def rotate_xticks(fig):
    """Cinco boxplots em 15 cm não deixam espaço para os nomes das classes na horizontal."""
    for ax in fig.axes:
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")


def shorten_heatmap_labels(fig):
    """Nomes cheios sobrepõem-se num mapa de 2,85 in; a legenda do LaTeX define MW."""
    ax = fig.axes[0]
    labels = ["MW" if t.get_text() == "Molecular Weight" else t.get_text() for t in ax.get_xticklabels()]
    ax.set_xticklabels(labels, rotation=0)
    ax.set_yticklabels(labels, rotation=0)


#: Nomes do código -> nomes que o leitor do relatório entende.
NOMES = {
    "Molecular Weight": "Massa molecular",
    "smiles_len": "Comprimento do SMILES",
    "n_N": "Átomos de N",
    "n_O": "Átomos de O",
    "n_S": "Átomos de S",
    "n_halogen": "Halogênios",
    "n_rings": "Anéis",
    "n_branch": "Ramificações",
    "n_aromatic": "Átomos aromáticos",
    "n_double": "Ligações duplas",
    "n_triple": "Ligações triplas",
    "n_charge": "Cargas",
    "n_stereo": "Estereoquímica",
}


def rename_boxplot_titles(fig):
    for ax in fig.axes:
        ax.set_title(NOMES.get(ax.get_title(loc="left"), ax.get_title(loc="left")), loc="left")
    rotate_xticks(fig)


def rename_importances(fig):
    # Os dois painéis compartilham o eixo y: renomear só o primeiro, senão o segundo (rótulos ocultos) apaga tudo.
    left = fig.axes[0]
    left.set_yticklabels([NOMES.get(t.get_text(), t.get_text()) for t in left.get_yticklabels()])
    left.tick_params(axis="y", labelsize=6.5)  # 17 rótulos em 2,6 in de altura
    for ax in fig.axes:
        ax.set_xlabel("queda de desempenho atribuída ao atributo")


def percent_axis(fig):
    """Acurácia de 0 a 1 vira 0% a 100% no eixo vertical do painel principal."""
    ax = fig.axes[0]
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.set_ylabel("acurácia")
    legend = ax.get_legend()
    if legend is not None:
        for text in legend.get_texts():
            text.set_text(text.get_text().replace("overfitting", "sobreajuste"))


def tidy_pruning(fig):
    percent_axis(fig)
    fig.axes[0].set_xlabel("α da poda (primeiro ponto: sem poda)")


def translate_tree_edges(fig):
    """plot_tree escreve "True  " e "  False" nas arestas da raiz; os espaços afastam o texto da seta."""
    for text in fig.axes[0].texts:
        text.set_text(text.get_text().replace("True", "sim").replace("False", "não"))


#: Ajustes por figura depois do redimensionamento.
POST = {
    "decision_tree": translate_tree_edges,
    "feature_boxplots": rename_boxplot_titles,
    "correlation_heatmap": shorten_heatmap_labels,
    "feature_importances": rename_importances,
    "depth_curve": percent_axis,
    "learning_curve": percent_axis,
    "pruning_curve": tidy_pruning,
}


def finish(fig, name):
    """Tira os títulos que a legenda substitui, ajusta o tamanho e refaz o layout."""
    if fig._suptitle is not None:
        fig._suptitle.set_visible(False)
    if name not in PANEL_TITLES:
        for ax in fig.axes:
            # As funções de plots usam loc="left"; o título central é outro objeto.
            for loc in ("left", "center", "right"):
                ax.set_title("", loc=loc)
    fig.set_size_inches(*SIZES[name])
    if name in POST:
        POST[name](fig)
    fig.tight_layout()


@contextmanager
def capture(name, png):
    """Dentro do bloco, `plt.show()` salva a figura corrente em vez de abri-la."""
    original = plt.show

    def save(*args, **kwargs):
        fig = plt.gcf()
        finish(fig, name)
        fig.savefig(OUT_DIR / f"{name}.pdf", bbox_inches="tight")
        if png:
            fig.savefig(OUT_DIR / f"{name}.png", bbox_inches="tight", dpi=150)
        plt.close(fig)
        print("salvo:", name, flush=True)

    plt.show = save
    try:
        yield
    finally:
        plt.show = original


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--png", action="store_true", help="salva também PNG ao lado de cada PDF")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plots.set_style()
    plt.rcParams.update(REPORT_RC)

    final = pd.read_csv(FINAL_CSV)
    complete = eda.complete_rows(final)

    def draw(name, *call_args, **call_kwargs):
        with capture(name, args.png):
            getattr(plots, name)(*call_args, **call_kwargs)

    # Notebook 02: só dependem da base final.
    draw("class_counts", final)
    draw("feature_boxplots", final)
    accuracy, baseline = eda.single_feature_accuracy(final)
    draw("single_feature_accuracy", accuracy, baseline)
    draw("correlation_heatmap", complete)
    draw("logp_tpsa_by_class", complete)

    # Notebook 03: mesma sequência de chamadas do notebook, seed 42.
    dados = modeling.prepare(final)
    comparacao, modelos = modeling.tune_all(dados)
    arvore = modelos[modeling.CHOSEN]
    draw("model_comparison", comparacao, baseline=0.293)
    draw("depth_curve", modeling.depth_curve(dados))
    draw("pruning_curve", modeling.pruning_curve(dados))
    # Três camadas cabem em 15 cm só sem os rótulos "samples =", "value =", "class =" e com fonte menor;
    # a legenda do LaTeX explica as quatro linhas de cada nó.
    draw("decision_tree", arvore, feature_names=[NOMES.get(c, c) for c in dados.X.columns],
         max_depth=2, fontsize=7, label="none")
    draw("feature_importances", modeling.importances(arvore, dados))
    _, matriz = modeling.evaluation(arvore, dados)
    draw("confusion_matrix", matriz)
    draw("learning_curve", modeling.learning_curve_table(dados))
    draw("error_pairs", modeling.error_overview(arvore, dados))


if __name__ == "__main__":
    main()
