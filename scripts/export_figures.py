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
    "depth_curve": (HALF, 2.3),
    "pruning_curve": (HALF, 2.3),
    "decision_tree": (FULL, 2.9),
    "feature_importances": (FULL, 3.0),
    "confusion_matrix": (HALF, 2.5),
    "learning_curve": (HALF, 2.3),
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


#: Ajustes por figura depois do redimensionamento.
POST = {"feature_boxplots": rotate_xticks, "correlation_heatmap": shorten_heatmap_labels}


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
    # Só a raiz e os dois filhos: com 3 camadas os nós (texto de 36 caracteres) se sobrepõem em 15 cm.
    draw("decision_tree", arvore, dados, max_depth=1)
    draw("feature_importances", modeling.importances(arvore, dados))
    _, matriz = modeling.evaluation(arvore, dados)
    draw("confusion_matrix", matriz)
    draw("learning_curve", modeling.learning_curve_table(dados))
    draw("error_pairs", modeling.error_overview(arvore, dados))


if __name__ == "__main__":
    main()
