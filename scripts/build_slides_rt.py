"""Monta slides/apresentacao_random_tree.pptx: a segunda apresentação, que compara a árvore de decisão com
a Random Tree e com conjuntos de árvores (Random Forest, gradient boosting).

Passos, a partir da raiz do projeto:

    python scripts/slides_rt_data.py      # números (10 seeds + seed 42), alguns minutos
    python scripts/build_slides_rt.py     # slides/apresentacao_random_tree.pptx e slides/notas_random_tree.md
    powershell -File scripts/export_slides_pdf.ps1 slides/apresentacao_random_tree.pptx   # PDF para validar

Mesmo template, paleta e regras de acessibilidade da primeira apresentação (slides_common.py): texto de no
mínimo 18 pt, gráficos e tabelas nativos do PowerPoint.
"""
import json
from pathlib import Path

from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_MARKER_STYLE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from slides_common import (GRAY_BAR, GREEN, GREEN_DK, INK, MIN_FONT, MUTED, RED, RED_TINT, TINT, Deck, alt,
                           audit_fonts, br, card, label_points, rgb, shape, style_chart, text_box, thousands, write)
from slides_rt_notes import build_notes

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "slides" / "data" / "slides_rt_data.json"
OUT = ROOT / "slides" / "apresentacao_random_tree.pptx"
NOTES_MD = ROOT / "slides" / "notas_random_tree.md"

TITLE = "Árvore de decisão, Random Tree e conjuntos de árvores na classificação de alvos proteicos"
SPEAKERS = {1: "Thiago", 2: "Paulo", 3: "Bernan"}
BLOCK_OF_SLIDE = [1, 1, 1, 2, 2, 2, 3, 3, 3, 3]
BLOCK_TITLE = {1: "Onde paramos e os cinco modelos",
               2: "Como comparamos, o resultado e a Random Tree",
               3: "De onde vem o ganho, ajuste, confiança e conclusão"}
HANDOFF = {
    2: (2, "Cinco modelos, a mesma peça. Mas como comparar de forma justa?"),
    5: (3, "Se a Random Tree perde sozinha, por que a Random Forest, feita delas, ganha?"),
}
GRAY_TINT = "EEF1F0"


def points(value):
    """Diferença em pontos, com sinal: +5,4 ou −1,9."""
    return f"+{br(value)}" if value >= 0 else f"−{br(-value)}"


# --- Peças deste deck --------------------------------------------------------------------------

def table(slide, x, y, widths, height, rows, name, description, header_fill=GREEN_DK, size=20, fills=None):
    """Tabela nativa: primeira linha é o cabeçalho (texto branco sobre verde-escuro)."""
    shape_ = slide.shapes.add_table(len(rows), len(widths), Inches(x), Inches(y), Inches(sum(widths)),
                                    Inches(height * len(rows)))
    shape_.name = name
    alt(shape_, description)
    grid = shape_.table
    grid.first_row = True
    grid.horz_banding = False
    for index, width in enumerate(widths):
        grid.columns[index].width = Inches(width)
    for row in grid.rows:
        row.height = Inches(height)
    for r, values in enumerate(rows):
        for c, value in enumerate(values):
            cell = grid.cell(r, c)
            cell.fill.solid()
            if r == 0:
                fill, color, bold = header_fill, "FFFFFF", True
            else:
                fill = (fills or {}).get(r, "FFFFFF" if r % 2 else GRAY_TINT)
                color, bold = INK, c == 0
            cell.fill.fore_color.rgb = rgb(fill)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = cell.margin_right = Inches(0.08)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            frame = cell.text_frame
            frame.text = ""
            frame.word_wrap = True
            spec = value if isinstance(value, dict) else {"text": value}
            write(frame, [spec], size=size, bold=spec.get("bold", bold), color=spec.get("color", color),
                  align=PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER)
    return grid


def hbar_chart(slide, x, y, w, h, categories, values, colors, description, vmin=80, vmax=100):
    """Barras horizontais com o eixo a partir de `vmin`, para diferenças de 1 a 2 pontos aparecerem."""
    data = CategoryChartData(number_format='0.0"%"')
    data.categories = categories
    data.add_series("Acurácia", values)
    frame = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), data)
    alt(frame, description)
    chart = frame.chart
    style_chart(chart)
    chart.has_legend = False
    plot = chart.plots[0]
    plot.gap_width = 40
    plot.vary_by_categories = False
    plot.has_data_labels = True
    labels = plot.data_labels
    labels.position = XL_LABEL_POSITION.OUTSIDE_END
    labels.font.size = Pt(MIN_FONT)
    series = plot.series[0]
    for index, color in enumerate(colors):
        point = series.points[index]
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = rgb(color)
    label_points(series, values, MIN_FONT)
    chart.category_axis.reverse_order = True
    chart.category_axis.tick_labels.font.size = Pt(MIN_FONT)
    chart.category_axis.format.line.color.rgb = rgb(GRAY_BAR)
    axis = chart.value_axis
    axis.minimum_scale, axis.maximum_scale, axis.major_unit = vmin, vmax, 5
    axis.has_major_gridlines = True
    axis.major_gridlines.format.line.color.rgb = rgb("DDE5E3")
    axis.format.line.fill.background()
    axis.tick_labels.number_format = '0"%"'
    axis.tick_labels.number_format_is_linked = False
    axis.tick_labels.font.size = Pt(MIN_FONT)
    axis.tick_labels.font.color.rgb = rgb(MUTED)
    return chart


def line_chart(slide, x, y, w, h, categories, series, colors, description, vmin, vmax, unit=5):
    """Linhas com marcadores, valores em %; legenda embaixo."""
    data = CategoryChartData(number_format='0.0"%"')
    data.categories = categories
    for name, values in series:
        data.add_series(name, values)
    frame = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(x), Inches(y), Inches(w), Inches(h), data)
    alt(frame, description)
    chart = frame.chart
    style_chart(chart)
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.legend.include_in_layout = False
    chart.legend.font.size = Pt(MIN_FONT)
    for item, color in zip(chart.plots[0].series, colors):
        item.smooth = False
        item.format.line.color.rgb = rgb(color)
        item.format.line.width = Pt(3)
        item.marker.style = XL_MARKER_STYLE.CIRCLE
        item.marker.size = 8
        item.marker.format.fill.solid()
        item.marker.format.fill.fore_color.rgb = rgb(color)
        item.marker.format.line.color.rgb = rgb(color)
    axis = chart.value_axis
    axis.minimum_scale, axis.maximum_scale, axis.major_unit = vmin, vmax, unit
    axis.has_major_gridlines = True
    axis.major_gridlines.format.line.color.rgb = rgb("DDE5E3")
    axis.format.line.fill.background()
    axis.tick_labels.number_format = '0"%"'
    axis.tick_labels.number_format_is_linked = False
    axis.tick_labels.font.size = Pt(MIN_FONT)
    axis.tick_labels.font.color.rgb = rgb(MUTED)
    chart.category_axis.tick_labels.font.size = Pt(MIN_FONT)
    chart.category_axis.format.line.color.rgb = rgb(GRAY_BAR)
    return chart


def pill(slide, x, y, w, h, text, fill=GREEN, color="FFFFFF", name=None):
    item = card(slide, x, y, w, h, fill, [text], name=name, size=20, bold=True, color=color,
                align=PP_ALIGN.CENTER, pad=0.05)
    item.adjustments[0] = 0.5
    return item


# --- Slides ------------------------------------------------------------------------------------

def slide_title(deck, d):
    slide = deck.slide("Slide de Título", TITLE, title_size=40)
    slide.shapes.title.text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM
    frame = slide.placeholders[1].text_frame
    frame.text = ""
    write(frame, [
        {"text": "Segunda parte: comparação de modelos", "size": 24, "bold": True, "color": GREEN, "space_after": 8},
        {"text": "Bernan R. do Nascimento · Paulo E. R. Araujo · Thiago R. P. de Carvalho", "size": 22, "bold": True,
         "space_after": 6},
        {"text": "Universidade Federal do Piauí (UFPI)", "size": 20},
        {"text": "PPGCC010 – Aprendizagem de Máquina (2026.2) · Prof. Vinicius Ponte Machado", "size": 20},
    ], align=PP_ALIGN.CENTER)


def slide_recap(deck, d):
    tree = d["multiseed"]["modelos"]["Árvore de decisão"]
    slide = deck.slide("Somente Título", f"Na primeira parte, a árvore de decisão chegou a {br(tree['acuracia'])}%")
    items = [
        (f"{thousands(d['moleculas'])} moléculas", "do ChEMBL, cada uma associada a 1 de 4 proteínas"),
        ("17 atributos", "5 descritores físico-químicos + 12 contagens do SMILES"),
        ("Divisão agrupada", "moléculas gêmeas (mesmos descritores) sempre do mesmo lado"),
    ]
    for index, (head, detail) in enumerate(items):
        y = 2.0 + index * 1.5
        card(slide, 0.92, y, 6.3, 1.3, TINT, [
            {"text": head, "size": 26, "bold": True, "color": GREEN_DK, "space_after": 2},
            {"text": detail, "size": 20},
        ], name=f"Resumo {index + 1}", anchor=MSO_ANCHOR.MIDDLE, pad=0.25)
    text_box(slide, 7.7, 2.0, 4.3, 1.4, [{"text": f"{br(tree['acuracia'])}%", "size": 72, "bold": True, "color": GREEN}],
             name="Acurácia da árvore")
    text_box(slide, 7.7, 3.45, 4.3, 0.9, ["acurácia da árvore de decisão, média de 10 seeds"], size=20,
             name="Legenda da acurácia")
    card(slide, 7.7, 4.85, 4.3, 1.45, GREEN_DK, ["Uma árvore só é o melhor que dá para fazer?"], name="Pergunta",
         size=24, bold=True, color="FFFFFF", align=PP_ALIGN.CENTER)


def slide_models(deck, d):
    slide = deck.slide("Somente Título", "Quatro modelos feitos da mesma peça: a árvore")
    rows = [
        ["Modelo", "Árvores", "Atributos por nó", "Como combina"],
        ["Árvore de decisão", "1", "todos", "–"],
        ["Random Tree (Weka)", "1", "K sorteados", "–"],
        ["Random Forest", "300", "K sorteados", "voto; cada uma vê uma amostra"],
        ["Gradient boosting", "300", "todos", "soma; cada uma corrige as anteriores"],
    ]
    table(slide, 0.92, 2.0, [2.85, 1.2, 2.2, 4.85], 0.75, rows, "Tabela dos modelos",
          "Tabela: os quatro modelos. Árvore de decisão: 1 árvore, todos os atributos. Random Tree: 1 árvore, K "
          "atributos sorteados por nó. Random Forest: 300 árvores, K sorteados, votação; cada árvore vê uma amostra do "
          "treino. Gradient boosting: 300 árvores em sequência, cada uma corrige as anteriores.",
          fills={2: "FFF1CC", 3: "FFF1CC"})
    text_box(slide, 0.92, 6.0, 11.1, 0.45, [
        {"runs": [("Destaque: ", {"bold": True}), ("a Random Forest é feita de 300 Random Trees", {})]},
    ], size=20, name="Nota do sorteio")


def slide_protocol(deck, d):
    grids = d["seed42"]["grids"]
    slide = deck.slide("Somente Título", "Mesma régua para todos os modelos")
    steps = [
        ("Mesmo treino e teste", "divisão agrupada, 80% e 20%"),
        ("Busca de hiperparâmetros", "validação cruzada agrupada, 5 partes"),
        ("10 seeds", "média e desvio de cada modelo"),
    ]
    for index, (head, detail) in enumerate(steps):
        y = 2.0 + index * 1.2
        card(slide, 0.92, y, 0.7, 0.7, GREEN, [str(index + 1)], name=f"Passo {index + 1}", size=26, bold=True,
             color="FFFFFF", align=PP_ALIGN.CENTER, pad=0.02).adjustments[0] = 0.5
        text_box(slide, 1.85, y - 0.05, 4.8, 1.1, [
            {"text": head, "size": 24, "bold": True, "space_after": 0},
            {"text": detail, "size": 20},
        ], name=f"Texto do passo {index + 1}")

    text_box(slide, 6.9, 2.0, 5.1, 0.45, ["Combinações testadas"], size=24, bold=True, color=GREEN_DK)
    rows = [["Modelo", "Busca"],
            ["Árvore de decisão", f"{grids['Árvore de decisão']}, em 6 cenários"],
            ["Random Tree", f"{grids['Random Tree']}, em 6 cenários"],
            ["Random Forest", f"{grids['Random Forest']}, cenário principal"],
            ["Gradient boosting", f"{grids['Gradient boosting']}, cenário principal"]]
    table(slide, 6.9, 2.55, [2.55, 2.55], 0.6, rows, "Tabela das buscas",
          "Tabela: combinações de hiperparâmetros testadas. Árvore de decisão 72 e Random Tree 54, nos 6 cenários; "
          "Random Forest 6 e gradient boosting 9, no cenário principal.", size=18)

    card(slide, 0.92, 5.6, 11.1, 1.1, RED_TINT, [
        {"runs": [("Desligados: ", {"bold": True, "color": RED}),
                  ("estimativa out-of-bag e parada antecipada. Os dois sorteiam uma validação aleatória e deixariam "
                   "gêmeas dos dois lados.", {})]},
    ], name="Atalhos desligados", size=20, pad=0.25)


def slide_results(deck, d):
    models = d["multiseed"]["modelos"]
    order = [("Gradient boosting (ajustado)", "Boosting ajustado"), ("Random Forest (ajustada)", "Floresta ajustada"),
             ("Random Forest (padrão)", "Floresta padrão"), ("Gradient boosting (padrão)", "Boosting padrão"),
             ("Árvore de decisão", "Árvore de decisão"),
             ("Random Tree (ajustada)", "Random Tree ajustada"), ("Random Tree (padrão Weka)", "Random Tree (Weka)")]
    values = [models[name]["acuracia"] for name, _ in order]
    colors = [GREEN, GREEN, GREEN, GREEN, GREEN_DK, GRAY_BAR, GRAY_BAR]
    gains = [models[name]["ganho_pontos"] for name in models if name not in ("Classe majoritária", "Árvore de decisão")
             and not name.startswith("Random Tree")]
    slide = deck.slide("Somente Título",
                       f"Conjuntos ganham de {br(min(gains), 0)} a {br(max(gains), 0)} pontos; a Random Tree perde para a árvore")
    text_box(slide, 0.92, 2.0, 7.0, 0.45, ["Acurácia no teste, média de 10 seeds"], size=24, bold=True, color=GREEN_DK)
    hbar_chart(slide, 0.92, 2.5, 7.2, 4.3, [label for _, label in order], values, colors,
               "Gráfico de barras, eixo de 80% a 100%: " + "; ".join(
                   f"{label} {br(value)}%" for (_, label), value in zip(order, values)) + ".")
    tree = models["Árvore de decisão"]
    gb = models["Gradient boosting (ajustado)"]
    text_box(slide, 8.5, 2.0, 3.5, 1.5, [
        {"text": points(gb["ganho_pontos"]), "size": 54, "bold": True, "color": GREEN, "space_after": 0},
        {"text": "pontos: boosting ajustado sobre a árvore", "size": 20},
    ], name="Ganho do boosting")
    text_box(slide, 8.5, 3.7, 3.5, 1.3, [
        {"text": "10 de 10", "size": 40, "bold": True, "color": GREEN, "space_after": 0},
        {"text": "seeds: todo conjunto supera a árvore", "size": 20},
    ], name="Seeds")
    rt = models["Random Tree (ajustada)"]
    text_box(slide, 8.5, 5.15, 3.5, 1.3, [
        {"text": points(rt["ganho_pontos"]), "size": 40, "bold": True, "color": RED, "space_after": 0},
        {"text": f"ponto: Random Tree ajustada contra a árvore ({br(tree['acuracia'])}%)", "size": 20},
    ], name="Perda da Random Tree")
    text_box(slide, 0.92, 6.82, 7.2, 0.4, ["Eixo a partir de 80%; piso (sempre EGFR): 29,3%"], size=18, name="Nota do eixo")


SCENARIO_LABEL = {"descritores": "Descritores (5)", "só SMILES": "SMILES (12)", "descritores + SMILES": "Ambos (17)"}


def slide_random_tree(deck, d):
    scenarios = d["multiseed"]["rt_cenarios"]
    order = {(f, s): i for i, (f, s) in enumerate(
        [(f, s) for f in ["descritores", "só SMILES", "descritores + SMILES"] for s in ["aleatória", "agrupada"]])}
    scenarios = sorted(scenarios, key=lambda s: order[(s["features"], s["split"])])
    losses = sum(s["diferenca_pontos"] < 0 for s in scenarios)
    rt = d["seed42"]["random_tree"]["sementes"]
    slide = deck.slide("Somente Título", f"A Random Tree perde em {losses} de 6 cenários e varia com a semente")
    text_box(slide, 0.92, 2.0, 6.3, 0.45, ["Random Tree menos árvore (10 seeds)"], size=24, bold=True, color=GREEN_DK)
    rows = [["Atributos", "Divisão", "Pontos"]]
    for s in scenarios:
        diff = s["diferenca_pontos"]
        rows.append([SCENARIO_LABEL[s["features"]], s["split"],
                     {"text": points(diff) if round(diff, 1) != 0 else "0,0", "bold": True,
                      "color": RED if diff < -0.05 else INK}])
    table(slide, 0.92, 2.5, [2.55, 1.95, 1.6], 0.58, rows, "Tabela Random Tree contra árvore",
          "Tabela: diferença de acurácia da Random Tree ajustada para a árvore de decisão, em pontos, média de 10 seeds. "
          + "; ".join(f"{SCENARIO_LABEL[s['features']]}, {s['split']}: {points(s['diferenca_pontos'])}" for s in scenarios)
          + ".")

    text_box(slide, 7.6, 2.0, 4.4, 0.45, ["Só trocando a semente"], size=24, bold=True, color=GREEN_DK)
    text_box(slide, 7.6, 2.5, 4.4, 0.75, ["mesmos dados e mesma divisão, 50 sementes (seed 42)"], size=18)
    lo, hi = 87.5, 90.0
    x0, width = 7.6, 3.9

    def to_x(value):
        return x0 + (value - lo) / (hi - lo) * width

    for index, (name, color) in enumerate([("Random Tree", GREEN), ("Árvore de decisão", GREEN_DK)]):
        info = rt[name]
        y = 3.55 + index * 1.35
        text_box(slide, x0, y, width, 0.4, [name], size=20, bold=True, name=f"Rótulo {name}")
        bar = shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, to_x(info["min"]), y + 0.5, to_x(info["max"]) - to_x(info["min"]),
                    0.3, color, name=f"Faixa {name}")
        bar.adjustments[0] = 0.5
        alt(bar, f"{name}: de {br(info['min'])}% a {br(info['max'])}%, média {br(info['mean'])}%.")
        text_box(slide, x0, y + 0.85, width, 0.4, [f"{br(info['min'])}% a {br(info['max'])}%"], size=20,
                 name=f"Faixa em texto {name}")
    line_y = 6.25
    shape(slide, MSO_SHAPE.RECTANGLE, x0, line_y, width, 0.02, GRAY_BAR, name="Escala")
    for tick in (88, 89, 90):
        text_box(slide, to_x(tick) - 0.4, line_y + 0.05, 0.8, 0.4, [f"{tick}%"], size=18, color=MUTED,
                 align=PP_ALIGN.CENTER, name=f"Marca {tick}")


def slide_bridge(deck, d):
    three = d["seed42"]["tres_arvores"]
    dt, rt, rf = (three[k]["acuracia"] for k in ("arvore", "random_tree", "random_forest"))
    slide = deck.slide("Somente Título", "Sozinha, a Random Tree perde; 300 delas formam a Random Forest")
    width, gap, y = 2.9, 0.9, 2.6
    cells = [("Árvore de decisão", "1 árvore, sem sorteio", dt, GRAY_TINT, INK),
             ("Random Tree", "1 árvore, com sorteio", rt, GRAY_TINT, INK),
             ("Random Forest", "300 árvores, com sorteio", rf, GREEN, "FFFFFF")]
    for index, (name, caption, value, fill, color) in enumerate(cells):
        x = 0.92 + index * (width + gap)
        text_box(slide, x, 2.0, width, 0.45, [caption], size=20, bold=True, color=GREEN_DK, align=PP_ALIGN.CENTER,
                 name=f"Rótulo {name}")
        card(slide, x, y, width, 1.5, fill, [
            {"text": f"{br(value)}%", "size": 40, "bold": True, "color": color, "align": PP_ALIGN.CENTER, "space_after": 0},
            {"text": name, "size": 22, "color": color, "align": PP_ALIGN.CENTER},
        ], name=f"Cartão {name}")
    pill(slide, 0.92 + width + 0.05, y + 0.5, gap - 0.1, 0.5, points(rt - dt), fill=RED, name="Perda do sorteio sozinho")
    pill(slide, 0.92 + 2 * width + gap + 0.05, y + 0.5, gap - 0.1, 0.5, points(rf - rt), name="Ganho de 300 árvores")

    card(slide, 0.92, 4.45, 5.4, 1.65, GRAY_TINT, [
        {"text": "Numa árvore só", "size": 22, "bold": True, "color": GREEN_DK, "space_after": 2},
        {"text": "o sorteio esconde o melhor corte do nó", "size": 20},
    ], name="Árvore só", anchor=MSO_ANCHOR.MIDDLE, pad=0.25)
    card(slide, 6.62, 4.45, 5.4, 1.65, TINT, [
        {"text": "Em 300 árvores", "size": 22, "bold": True, "color": GREEN_DK, "space_after": 2},
        {"text": "o sorteio deixa as árvores diferentes: elas erram em moléculas diferentes e o voto cancela os erros",
         "size": 20},
    ], name="Conjunto", anchor=MSO_ANCHOR.MIDDLE, pad=0.25)
    text_box(slide, 0.92, 6.3, 9.0, 0.45, ["Seed 42, teste; mesma árvore base; árvore única = média de 10 sementes"],
             size=18, color=MUTED, name="Nota")


def slide_tuning(deck, d):
    models = d["multiseed"]["modelos"]
    boosting = d["seed42"]["ajuste"]["gradient_boosting"]
    slide = deck.slide("Somente Título", "Ajustar rende no boosting, não na floresta")
    pairs = [("Random Forest", models["Random Forest (padrão)"]["acuracia"], models["Random Forest (ajustada)"]["acuracia"]),
             ("Gradient boosting", models["Gradient boosting (padrão)"]["acuracia"],
              models["Gradient boosting (ajustado)"]["acuracia"])]
    text_box(slide, 0.92, 2.0, 4.6, 0.45, ["Padrão → ajustado (10 seeds)"], size=24, bold=True, color=GREEN_DK)
    for index, (name, before, after) in enumerate(pairs):
        y = 2.6 + index * 2.0
        diff = after - before
        card(slide, 0.92, y, 4.6, 1.75, TINT if index else GRAY_TINT, [
            {"text": name, "size": 22, "bold": True, "space_after": 2},
            {"runs": [(f"{br(before)}% → {br(after)}%", {"size": 28, "bold": True, "color": GREEN_DK})], "space_after": 2},
            {"text": "empate" if abs(diff) < 0.3 else f"{points(diff)} pontos", "size": 20, "bold": True,
             "color": MUTED if abs(diff) < 0.3 else GREEN},
        ], name=f"Ajuste {name}", anchor=MSO_ANCHOR.MIDDLE, pad=0.25)

    text_box(slide, 5.95, 2.0, 6.0, 0.45, ["Boosting por iteração (validação)"], size=24, bold=True, color=GREEN_DK)
    valid, train = boosting["curva_iteracoes"], boosting["curva_iteracoes_treino"]
    keys = [k for k in valid if k in {"1", "10", "25", "50", "100", "200", "300"}]
    line_chart(slide, 5.95, 2.5, 6.1, 4.2, keys, [("treino", [train[k] for k in keys]), ("validação", [valid[k] for k in keys])],
               [GRAY_BAR, GREEN],
               "Gráfico de linhas: acurácia do gradient boosting por iteração. " + "; ".join(
                   f"{k} iterações: treino {br(train[k])}%, validação {br(valid[k])}%" for k in keys) + ".",
               vmin=80, vmax=100)
    text_box(slide, 0.92, 6.55, 4.6, 0.4, ["Boosting: 300 iterações, sem parada antecipada"], size=18, color=MUTED,
             name="Nota")


def slide_confidence(deck, d):
    models = d["multiseed"]["modelos"]
    conf = d["seed42"]["confianca"]
    rf, gb = conf["Random Forest"], conf["Gradient boosting"]
    slide = deck.slide("Somente Título", "Só a Random Forest sabe quando está em dúvida")
    rows = [
        ["Modelo", "Acurácia", "Regras legíveis", "Confiança útil?"],
        ["Árvore de decisão", f"{br(models['Árvore de decisão']['acuracia'])}%", "sim", "não: 100% em tudo"],
        ["Random Tree", f"{br(models['Random Tree (ajustada)']['acuracia'])}%", "mudam com a semente", "não"],
        ["Random Forest", f"{br(models['Random Forest (padrão)']['acuracia'])}%", "não",
         {"text": f"sim: {br(rf['erros_abaixo_70'], 0)}% dos erros com ≤ 70%", "bold": True, "color": GREEN_DK}],
        ["Gradient boosting", f"{br(models['Gradient boosting (ajustado)']['acuracia'])}%", "não",
         f"pouco: {br(gb['erros_confianca_maxima'], 0)}% dos erros > 99,9%"],
    ]
    table(slide, 0.92, 2.0, [2.6, 1.45, 3.05, 4.0], 0.72, rows, "Tabela de confiança",
          "Tabela: acurácia (10 seeds), regras legíveis e utilidade da confiança. Árvore: sim, não. Random Tree: regras "
          "mudam com a semente, confiança não útil. Random Forest: sem regras; confiança útil. Gradient boosting: sem "
          "regras; confiança exagerada.", fills={3: TINT})
    card(slide, 0.92, 6.0, 11.1, 0.85, TINT, [
        {"runs": [("Na prática: ", {"bold": True, "color": GREEN_DK}),
                  (f"revisar os {br(rf['previsoes_abaixo_70'], 0)}% de previsões da floresta com confiança ≤ 70% "
                   f"pega {br(rf['erros_abaixo_70'], 0)}% dos erros", {})]},
    ], name="Uso prático", size=20, pad=0.25)


def slide_conclusion(deck, d):
    models = d["multiseed"]["modelos"]
    slide = deck.slide("Somente Título", "Conclusões")
    cards = [
        (f"{br(models['Gradient boosting (ajustado)']['acuracia'])}%", "gradient boosting ajustado, o mais preciso"),
        (points(models["Random Forest (padrão)"]["ganho_pontos"]), "pontos: Random Forest, 300 Random Trees juntas"),
        (points(models["Random Tree (ajustada)"]["ganho_pontos"]), "ponto: a Random Tree sozinha perde para a árvore"),
    ]
    for index, (number, caption) in enumerate(cards):
        card(slide, 0.92 + index * 3.78, 2.0, 3.55, 2.0, TINT, [
            {"text": number, "size": 40, "bold": True, "color": GREEN_DK, "align": PP_ALIGN.CENTER, "space_after": 4},
            {"text": caption, "size": 18, "align": PP_ALIGN.CENTER},
        ], name=f"Número {index + 1}")
    text_box(slide, 0.92, 4.25, 11.1, 0.45, ["Qual usar"], size=24, bold=True, color=GREEN_DK)
    uses = [("Acertar mais", "gradient boosting"), ("Saber quando duvidar", "Random Forest"),
            ("Explicar a previsão", "árvore de decisão")]
    for index, (need, model) in enumerate(uses):
        card(slide, 0.92 + index * 3.78, 4.8, 3.55, 1.2, "FFFFFF", [
            {"text": need, "size": 20, "align": PP_ALIGN.CENTER, "space_after": 0},
            {"text": model, "size": 22, "bold": True, "color": GREEN_DK, "align": PP_ALIGN.CENTER},
        ], name=f"Uso {index + 1}").line.color.rgb = rgb(GRAY_BAR)
    text_box(slide, 0.92, 6.4, 9.5, 0.4, [
        {"runs": [("Código e dados: ", {"bold": True}), ("github.com/pumba-dev/machine-learning-practice", {}),
                  ("  ·  Perguntas?", {"bold": True, "color": GREEN})]},
    ], size=20, name="Repositório")


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    deck = Deck(build_notes(data), out=OUT, notes_md=NOTES_MD, speakers=SPEAKERS, blocks=BLOCK_OF_SLIDE,
                block_titles=BLOCK_TITLE, handoff=HANDOFF, title=TITLE,
                author="Bernan R. do Nascimento; Paulo E. R. Araujo; Thiago R. P. de Carvalho",
                notes_title="Roteiro da segunda apresentação (10 min)")
    for build in (slide_title, slide_recap, slide_models, slide_protocol, slide_results, slide_random_tree,
                  slide_bridge, slide_tuning, slide_confidence, slide_conclusion):
        build(deck, data)
    deck.save()
    print("gravado:", OUT)
    small = audit_fonts(OUT)
    print("texto abaixo de", MIN_FONT, "pt:", small if small else "nenhum")


if __name__ == "__main__":
    main()
