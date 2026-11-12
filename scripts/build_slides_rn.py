"""Monta slides/apresentacao_redes_neurais.pptx: a terceira apresentação, com a rede neural na base de
empréstimos comparada com a árvore de decisão e modelos de referência, incluindo o tempo de execução.

Passos, a partir da raiz do projeto:

    python scripts/rn_data.py             # números (10 seeds + seed 42), cerca de 30 s
    python scripts/build_slides_rn.py     # slides/apresentacao_redes_neurais.pptx e slides/notas_redes_neurais.md
    powershell -File scripts/export_slides_pdf.ps1 slides/apresentacao_redes_neurais.pptx   # PDF (exige PowerPoint)

Mesmo template, paleta, regras de acessibilidade (texto de no mínimo 18 pt) e peças da segunda apresentação
(slides_common.py e build_slides_rt.py): gráficos e tabelas nativos do PowerPoint.
"""
import json
from pathlib import Path

from pptx.chart.data import CategoryChartData, XyChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_MARKER_STYLE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

from build_slides_rt import GRAY_TINT, hbar_chart, line_chart, pill, points, table
from slides_common import (GOLD, GRAY_BAR, GREEN, GREEN_DK, INK, MIN_FONT, MUTED, RED, RED_TINT, TINT, Deck, alt,
                           audit_fonts, br, card, line_between, rgb, shape, style_chart, text_box, thousands, write)
from slides_rn_notes import build_notes

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "report" / "results" / "rn_dados.json"
OUT = ROOT / "slides" / "apresentacao_redes_neurais.pptx"
NOTES_MD = ROOT / "slides" / "notas_redes_neurais.md"

TITLE = "Redes neurais na aprovação de empréstimos"
SPEAKERS = {1: "Thiago", 2: "Paulo", 3: "Bernan"}
BLOCK_OF_SLIDE = [1, 1, 1, 2, 2, 2, 3, 3, 3, 3]
BLOCK_TITLE = {1: "A base e o degrau no score",
               2: "A rede neural: padronização, épocas e paciência",
               3: "Resultado, tempo, onde a rede erra e conclusão"}
HANDOFF = {
    2: (2, "Se uma regra simples já acerta 95%, o que uma rede neural acrescenta?"),
    5: (3, "Com a rede ajustada, como ela se sai contra os outros modelos?"),
}
APPROVED, REJECTED = "1BAF7A", RED


def scatter_chart(slide, x, y, w, h, score, prob, real, description):
    """Dispersão nativa: probabilidade de aprovação por score, uma série por situação real."""
    data = XyChartData()
    for label, classe in [("aprovado", 1), ("rejeitado", 0)]:
        series = data.add_series(label)
        for s, p, r in zip(score, prob, real):
            if r == classe:
                series.add_data_point(s, 100 * p)
    frame = slide.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, Inches(x), Inches(y), Inches(w), Inches(h), data)
    alt(frame, description)
    chart = frame.chart
    style_chart(chart)
    chart.has_legend = False
    for item, color in zip(chart.plots[0].series, [APPROVED, REJECTED]):
        item.format.line.fill.background()
        item.marker.style = XL_MARKER_STYLE.CIRCLE
        item.marker.size = 4
        item.marker.format.fill.solid()
        item.marker.format.fill.fore_color.rgb = rgb(color)
        item.marker.format.line.fill.background()
    xaxis, yaxis = chart.category_axis, chart.value_axis
    xaxis.minimum_scale, xaxis.maximum_scale, xaxis.major_unit = 300, 900, 100
    yaxis.minimum_scale, yaxis.maximum_scale, yaxis.major_unit = 0, 100, 50
    for axis in (xaxis, yaxis):
        axis.has_major_gridlines = axis is yaxis
        axis.tick_labels.font.size = Pt(MIN_FONT)
        axis.tick_labels.font.color.rgb = rgb(MUTED)
        axis.format.line.color.rgb = rgb(GRAY_BAR)
    yaxis.major_gridlines.format.line.color.rgb = rgb("DDE5E3")
    yaxis.tick_labels.number_format = '0"%"'
    yaxis.tick_labels.number_format_is_linked = False
    return chart


def score_chart(slide, x, y, w, h, bands, description):
    """Colunas da taxa de aprovação por faixa de score: cinza abaixo de 550, verde a partir de 550."""
    data = CategoryChartData(number_format='0"%"')
    data.categories = [str(k) for k in bands]
    data.add_series("Aprovados", list(bands.values()))
    frame = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), data)
    alt(frame, description)
    chart = frame.chart
    style_chart(chart)
    chart.has_legend = False
    plot = chart.plots[0]
    plot.gap_width = 30
    plot.vary_by_categories = False
    for index, start in enumerate(bands):
        point = plot.series[0].points[index]
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = rgb(GREEN if int(start) >= 550 else GRAY_BAR)
    axis = chart.value_axis
    axis.minimum_scale, axis.maximum_scale, axis.major_unit = 0, 100, 25
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


# --- Slides ------------------------------------------------------------------------------------

def slide_title(deck, d):
    slide = deck.slide("Slide de Título", TITLE, title_size=44)
    slide.shapes.title.text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM
    frame = slide.placeholders[1].text_frame
    frame.text = ""
    write(frame, [
        {"text": "Terceira parte: redes neurais", "size": 24, "bold": True, "color": GREEN, "space_after": 8},
        {"text": "Bernan R. do Nascimento · Paulo E. R. Araujo · Thiago R. P. de Carvalho", "size": 22, "bold": True,
         "space_after": 6},
        {"text": "Universidade Federal do Piauí (UFPI)", "size": 20},
        {"text": "PPGCC010 – Aprendizagem de Máquina (2026.2) · Prof. Vinicius Ponte Machado", "size": 20},
    ], align=PP_ALIGN.CENTER)


def slide_base(deck, d):
    base = d["base"]
    slide = deck.slide("Somente Título", f"{thousands(base['linhas'])} pedidos de empréstimo, 11 atributos")
    items = [
        ("Quem pede", "dependentes, graduado, autônomo"),
        ("Dinheiro", "renda, valor pedido, 4 tipos de patrimônio"),
        ("Crédito e prazo", "score de 300 a 900; prazo de 2 a 20 anos"),
    ]
    for index, (head, detail) in enumerate(items):
        y = 2.0 + index * 1.45
        card(slide, 0.92, y, 6.3, 1.25, TINT, [
            {"text": head, "size": 24, "bold": True, "color": GREEN_DK, "space_after": 2},
            {"text": detail, "size": 20},
        ], name=f"Atributos {index + 1}", anchor=MSO_ANCHOR.MIDDLE, pad=0.25)
    text_box(slide, 0.92, 6.4, 6.3, 0.45, [
        {"runs": [("Curadoria: ", {"bold": True}),
                  (f"{base['negativos_residencial']} patrimônios negativos → 0", {})]},
    ], size=18, name="Curadoria")
    text_box(slide, 7.7, 2.0, 4.3, 1.4, [{"text": f"{br(base['aprovados'])}%", "size": 72, "bold": True,
                                          "color": GREEN}], name="Aprovados")
    text_box(slide, 7.7, 3.45, 4.3, 0.9, ["dos pedidos aprovados: responder sempre ‘aprovado’ é o piso"], size=20,
             name="Legenda dos aprovados")
    card(slide, 7.7, 4.85, 4.3, 1.45, GREEN_DK, ["Rótulo: o pedido foi aprovado?"], name="Pergunta",
         size=24, bold=True, color="FFFFFF", align=PP_ALIGN.CENTER)


def slide_score(deck, d):
    base = d["base"]
    bands = base["aprovacao_por_faixa_50"]
    slide = deck.slide("Somente Título", "A aprovação salta em 550 de score")
    text_box(slide, 0.92, 2.0, 7.2, 0.45, ["Pedidos aprovados por faixa de score"], size=24, bold=True,
             color=GREEN_DK)
    score_chart(slide, 0.92, 2.5, 7.3, 4.2, bands,
                "Gráfico de colunas: proporção de aprovados por faixa de 50 pontos de score. " + "; ".join(
                    f"{k} a {int(k) + 49}: {br(v, 0)}%" for k, v in bands.items()) + ".")
    text_box(slide, 0.92, 6.75, 7.3, 0.4, ["Faixas de 50 pontos; 300 = 300 a 349"], size=18, color=MUTED,
             name="Nota do eixo")
    text_box(slide, 8.6, 2.0, 3.4, 1.5, [
        {"text": f"{br(base['regra_550_base'])}%", "size": 54, "bold": True, "color": GREEN, "space_after": 0},
        {"text": "acerto da regra ‘score ≥ 550’", "size": 20},
    ], name="Regra")
    text_box(slide, 8.6, 3.75, 3.4, 1.3, [
        {"text": f"{br(base['aprovacao_abaixo_550'], 0)}% → {br(base['aprovacao_acima_550'], 0)}%", "size": 36,
         "bold": True, "color": GREEN_DK, "space_after": 0},
        {"text": "aprovação abaixo e acima de 550", "size": 20},
    ], name="Degrau")
    card(slide, 8.6, 5.25, 3.4, 1.45, GRAY_TINT, [
        {"text": "Exceção", "size": 20, "bold": True, "color": GREEN_DK, "space_after": 0},
        {"text": "abaixo de 550, só prazos de 2 e 4 anos são aprovados", "size": 18},
    ], name="Exceção", anchor=MSO_ANCHOR.MIDDLE, pad=0.2)


def slide_network(deck, d):
    slide = deck.slide("Somente Título", "A rede neural: neurônios em camadas")
    layers = [(1.45, 6, "11 atributos"), (3.35, 7, "32 neurônios"), (5.15, 5, "16 neurônios"), (6.7, 1, "saída")]
    top, bottom, size = 2.55, 5.95, 0.36
    centers = []
    for x, count, _ in layers:
        if count == 1:
            ys = [(top + bottom) / 2]
        else:
            ys = [top + i * (bottom - top) / (count - 1) for i in range(count)]
        centers.append([(x, yy) for yy in ys])
    for left, right in zip(centers, centers[1:]):
        for x1, y1 in left:
            for x2, y2 in right:
                line_between(slide, x1 + size / 2, y1 + size / 2, x2 + size / 2, y2 + size / 2, "C9D3D1", width=0.75)
    fills = [GRAY_BAR, GREEN, GREEN, GREEN_DK]
    for (x, count, label), nodes, fill in zip(layers, centers, fills):
        for index, (nx, ny) in enumerate(nodes):
            node = shape(slide, MSO_SHAPE.OVAL, nx, ny, size, size, fill, name=f"Neurônio {label} {index + 1}")
            node.line.color.rgb = rgb("FFFFFF")
        text_box(slide, x - 0.55, 2.0, 1.45, 0.45, [label], size=18, bold=True, color=GREEN_DK, align=PP_ALIGN.CENTER,
                 name=f"Rótulo {label}")
    text_box(slide, 0.92, 6.45, 6.6, 0.45, ["Entrada · 2 camadas ocultas (ReLU) · saída (sigmoide)"], size=18,
             color=MUTED, align=PP_ALIGN.CENTER, name="Legenda do diagrama")
    cards = [
        ("Um neurônio", "soma das entradas × pesos, mais o viés (um ajuste fixo aprendido), depois a ReLU"),
        ("A saída", "sigmoide: probabilidade de aprovação; acima de 50%, ‘aprovado’"),
        ("O treino", "pesos sorteados, ajustados a cada época para reduzir o erro"),
    ]
    for index, (head, detail) in enumerate(cards):
        card(slide, 7.75, 2.0 + index * 1.55, 4.3, 1.4, TINT if index != 1 else GRAY_TINT, [
            {"text": head, "size": 22, "bold": True, "color": GREEN_DK, "space_after": 2},
            {"text": detail, "size": 18},
        ], name=f"Explicação {index + 1}", anchor=MSO_ANCHOR.MIDDLE, pad=0.2)


def slide_scaling(deck, d):
    pad, base = d["padronizacao"], d["base"]
    slide = deck.slide("Somente Título", "Sem padronização, a rede não aprende")
    cells = [("Sem padronização", pad["sem"], RED_TINT, RED), ("Com padronização", pad["com"], TINT, GREEN_DK)]
    for index, (name, info, fill, color) in enumerate(cells):
        x = 0.92 + index * 3.0
        card(slide, x, 2.0, 2.75, 2.1, fill, [
            {"text": f"{br(info['acuracia'])}%", "size": 44, "bold": True, "color": color, "align": PP_ALIGN.CENTER,
             "space_after": 0},
            {"text": name, "size": 20, "align": PP_ALIGN.CENTER},
        ], name=f"Cartão {name}")
    text_box(slide, 0.92, 4.25, 5.75, 0.8, [
        f"mesma rede, 10 seeds; piso (sempre ‘aprovado’): {br(base['aprovados'])}%"], size=18, color=MUTED,
        name="Nota")
    text_box(slide, 7.2, 2.0, 4.8, 0.45, ["Escalas muito diferentes"], size=24, bold=True, color=GREEN_DK)
    rows = [["Atributo", "Faixa"], ["dependentes", "0 a 5"], ["score", "300 a 900"],
            ["renda anual", "até 9,9 milhões"]]
    table(slide, 7.2, 2.55, [2.4, 2.4], 0.55, rows, "Tabela de escalas",
          "Tabela: faixas dos atributos. Dependentes de 0 a 5; score de 300 a 900; renda anual até 9,9 milhões.",
          size=20)
    card(slide, 0.92, 5.2, 11.1, 1.45, GRAY_TINT, [
        {"runs": [("Padronizar: ", {"bold": True, "color": GREEN_DK}),
                  ("(valor − média) ÷ desvio padrão, em cada atributo", {})], "space_after": 2},
        {"text": "Todos ficam em torno de 0, na mesma escala. Média e desvio vêm só do treino.", "color": MUTED},
    ], name="Fórmula", size=22, pad=0.3, anchor=MSO_ANCHOR.MIDDLE)


def slide_epochs(deck, d):
    s42, r = d["seed42"], d["multiseed"]["rede"]
    curvas = s42["epocas"]["curvas"]
    paradas = {(p["taxa"], p["paciencia"]): p for p in s42["epocas"]["paradas"]}
    slide = deck.slide("Somente Título", "Épocas e paciência: quando parar o treino")
    keys = [10, 20, 37, 50, 100, 150, 217, 300, 400]
    series = [(f"taxa {label}", [100 * curvas[taxa]["acurácia validação"][k - 1] for k in keys])
              for taxa, label in [("0.001", "0,001"), ("0.01", "0,01")]]
    text_box(slide, 0.92, 2.0, 6.6, 0.45, ["Acurácia de validação por época"], size=24, bold=True, color=GREEN_DK)
    line_chart(slide, 0.92, 2.5, 6.7, 4.3, [str(k) for k in keys], series, [GRAY_BAR, GREEN],
               "Gráfico de linhas: acurácia de validação por época, seed 42. " + "; ".join(
                   f"época {k}: taxa 0,001 {br(a)}%, taxa 0,01 {br(b)}%" for k, a, b in
                   zip(keys, series[0][1], series[1][1])) + ".", vmin=85, vmax=100)
    card(slide, 7.95, 2.0, 4.1, 1.5, TINT, [
        {"runs": [("Época: ", {"bold": True, "color": GREEN_DK}), ("uma passada pelo treino", {})], "space_after": 4},
        {"runs": [("Paciência: ", {"bold": True, "color": GREEN_DK}), ("épocas sem melhora antes de parar", {})]},
    ], name="Definições", size=18, pad=0.2, anchor=MSO_ANCHOR.MIDDLE)
    lenta10, lenta30 = paradas[(0.001, 10)], paradas[(0.001, 30)]
    rows = [["Taxa 0,001", "Parada", "Validação"],
            ["paciência 10", str(lenta10["epoca"]), {"text": f"{br(lenta10['acuracia'])}%", "bold": True,
                                                       "color": RED}],
            ["paciência 30", str(lenta30["epoca"]), f"{br(lenta30['acuracia'])}%"]]
    table(slide, 7.95, 3.7, [1.6, 1.35, 1.15], 0.6, rows, "Tabela de paradas",
          f"Tabela: com taxa 0,001, paciência 10 para na época {lenta10['epoca']} com {br(lenta10['acuracia'])}%; "
          f"paciência 30 para na época {lenta30['epoca']} com {br(lenta30['acuracia'])}%.", size=18)
    text_box(slide, 7.95, 5.65, 4.1, 1.2, [
        {"runs": [("Usamos paciência 30; ", {"bold": True}),
                  (f"a busca escolheu a taxa 0,01 em {r['taxa_001']} de 10 seeds", {})]},
    ], size=18, name="Escolha")


def slide_results(deck, d):
    m, c = d["multiseed"]["modelos"], d["multiseed"]["comparacoes"]
    order = [("random forest", "Random Forest"), ("árvore de decisão", "Árvore de decisão"),
             ("rede neural", "Rede neural"), ("regra de um corte", "Regra de um corte"),
             ("regressão logística", "Regressão logística")]
    values = [m[name]["acuracia"] for name, _ in order]
    colors = [GREEN, GREEN, GREEN_DK, GRAY_BAR, GRAY_BAR]
    slide = deck.slide("Somente Título", "A rede supera a logística, mas não a árvore")
    text_box(slide, 0.92, 2.0, 7.0, 0.45, ["Acurácia no teste, média de 10 seeds"], size=24, bold=True, color=GREEN_DK)
    hbar_chart(slide, 0.92, 2.5, 7.2, 3.65, [label for _, label in order], values, colors,
               "Gráfico de barras, eixo de 85% a 100%: " + "; ".join(
                   f"{label} {br(value)}%" for (_, label), value in zip(order, values)) + ".", vmin=85, vmax=100)
    text_box(slide, 0.92, 6.2, 7.2, 0.4, [f"Eixo a partir de 85%; piso (sempre ‘aprovado’): "
                                           f"{br(m['classe majoritária']['acuracia'])}%"], size=18, name="Nota do eixo")
    text_box(slide, 0.92, 6.65, 7.2, 0.45, [{"runs": [
        ("AUC: ", {"bold": True, "color": GREEN_DK}),
        (f"rede {br(m['rede neural']['auc'])}% · árvore {br(m['árvore de decisão']['auc'])}% · "
         f"floresta {br(m['random forest']['auc'])}%", {})]}], size=18, name="AUC")
    for index, (key, label, color) in enumerate([
            ("rede neural × regressão logística", "rede sobre a logística", GREEN),
            ("rede neural × regra de um corte", "rede sobre a regra de um corte", GOLD),
            ("rede neural × árvore de decisão", "rede contra a árvore", RED)]):
        info = c[key]
        text_box(slide, 8.5, 2.0 + index * 1.55, 3.5, 1.45, [
            {"text": points(info["pontos"]).replace("%", " pt"), "size": 36, "bold": True,
             "color": color if color != GOLD else "9A7A00", "space_after": 0},
            {"text": f"{label}; melhor em {info['seeds']} de 10 seeds", "size": 18},
        ], name=f"Comparação {index + 1}")


def slide_time(deck, d):
    m = d["multiseed"]["modelos"]
    slide = deck.slide("Somente Título", "A rede custa mais tempo, sobretudo na busca")

    def ms(value):
        return f"{br(value, 0 if value >= 100 else 1)} ms"

    rows = [["Modelo", "Treino", "Busca", "Previsão"]]
    for name, label in [("regra de um corte", "Regra de um corte"), ("regressão logística", "Regressão logística"),
                        ("árvore de decisão", "Árvore de decisão"), ("random forest", "Random Forest"),
                        ("rede neural", "Rede neural")]:
        info = m[name]
        busca = "–" if info["busca_s"] is None else f"{br(info['busca_s'], 2 if info['busca_s'] < 1 else 1)} s"
        rows.append([label, ms(info["treino_ms"]), busca, ms(info["previsao_ms"])])
    table(slide, 0.92, 2.0, [3.0, 1.55, 1.45, 1.6], 0.62, rows, "Tabela de tempos",
          "Tabela de tempos (mediana de 10 seeds, um núcleo): " + "; ".join(
              f"{row[0]}: treino {row[1]}, busca {row[2]}, previsão {row[3]}" for row in rows[1:]) + ".",
          fills={5: TINT}, size=20)
    total_min = 10 * m["rede neural"]["busca_s"] / 60
    text_box(slide, 0.92, 5.95, 7.6, 0.9, [
        {"runs": [("Busca em segundos, por seed (120 redes): ", {"bold": True}),
                  (f"nas 10 seeds, ≈ {br(total_min, 0)} min", {})], "space_after": 2},
        {"text": "Mediana de 10 seeds · um núcleo · aquecimento descartado · Ryzen 5 9600X", "color": MUTED},
    ], size=18, name="Como medimos")
    treino = m["rede neural"]["treino_ms"] / m["árvore de decisão"]["treino_ms"]
    busca = m["rede neural"]["busca_s"] / m["árvore de decisão"]["busca_s"]
    text_box(slide, 9.0, 2.0, 3.1, 2.0, [
        {"text": f"{br(treino, 0)}×", "size": 54, "bold": True, "color": GREEN_DK, "space_after": 0},
        {"text": "mais tempo para treinar a rede final do que a árvore", "size": 18},
    ], name="Razão de treino")
    text_box(slide, 9.0, 4.2, 3.1, 2.0, [
        {"text": f"{br(busca, 0)}×", "size": 54, "bold": True, "color": RED, "space_after": 0},
        {"text": "mais tempo na busca de hiperparâmetros da rede do que na da árvore", "size": 18},
    ], name="Razão de busca")


def slide_ramp(deck, d):
    s42 = d["seed42"]
    disp, erros = s42["dispersao"], s42["erros"]
    slide = deck.slide("Somente Título", "Árvore desenha um degrau; a rede, uma rampa")
    for index, (name, label) in enumerate([("árvore de decisão", "Árvore de decisão"), ("rede neural", "Rede neural")]):
        x = 0.92 + index * 5.65
        text_box(slide, x, 1.95, 5.4, 0.45, [label], size=22, bold=True, color=GREEN_DK, name=f"Título {label}")
        scatter_chart(slide, x, 2.4, 5.45, 3.0, disp["score"], disp[name], disp["real"],
                      f"Gráfico de dispersão: probabilidade de aprovação prevista pela {label.lower()} para cada pedido "
                      "de teste (seed 42), por score de crédito, em verde os aprovados e em vermelho os rejeitados.")
    text_box(slide, 0.92, 5.45, 11.1, 0.4, [
        {"runs": [("● aprovado", {"color": APPROVED, "bold": True}), ("   ", {}),
                  ("● rejeitado", {"color": REJECTED, "bold": True}),
                  ("   eixo x: score de crédito · eixo y: probabilidade de aprovação (seed 42)", {"color": MUTED})]},
    ], size=18, name="Legenda")
    rede_f, arv_f = erros["rede neural"]["por_faixa"], erros["árvore de decisão"]["por_faixa"]
    card(slide, 0.92, 6.0, 11.1, 0.85, TINT, [
        {"runs": [("Score de 550 a 599: ", {"bold": True, "color": GREEN_DK}),
                  (f"a rede erra {rede_f[2]} pedidos; a árvore, {arv_f[2]}", {})]},
    ], name="Erros no degrau", size=22, pad=0.25)


def slide_conclusion(deck, d):
    m, c = d["multiseed"]["modelos"], d["multiseed"]["comparacoes"]
    slide = deck.slide("Somente Título", "Conclusões")
    treino = m["rede neural"]["treino_ms"] / m["árvore de decisão"]["treino_ms"]
    cards = [
        (f"{br(m['rede neural']['acuracia'])}%", "rede neural: supera a regressão logística em 10 de 10 seeds"),
        (points(c["rede neural × árvore de decisão"]["pontos"]).replace("%", " pt"),
         "contra a árvore de decisão, em todas as seeds"),
        (f"{br(treino, 0)}×", "mais lenta que a árvore para treinar"),
    ]
    for index, (number, caption) in enumerate(cards):
        card(slide, 0.92 + index * 3.78, 2.0, 3.55, 2.0, TINT, [
            {"text": number, "size": 40, "bold": True, "color": GREEN_DK, "align": PP_ALIGN.CENTER, "space_after": 4},
            {"text": caption, "size": 18, "align": PP_ALIGN.CENTER},
        ], name=f"Número {index + 1}")
    text_box(slide, 0.92, 4.25, 11.1, 0.45, ["O que aprendemos"], size=24, bold=True, color=GREEN_DK)
    lessons = [("Padronizar", "sem isso, a rede não aprende"),
               ("Paciência e taxa", "decidem quando a rede para"),
               ("Forma da regra", "degrau favorece a árvore")]
    for index, (head, detail) in enumerate(lessons):
        card(slide, 0.92 + index * 3.78, 4.8, 3.55, 1.2, "FFFFFF", [
            {"text": head, "size": 22, "bold": True, "color": GREEN_DK, "align": PP_ALIGN.CENTER, "space_after": 0},
            {"text": detail, "size": 18, "align": PP_ALIGN.CENTER},
        ], name=f"Lição {index + 1}").line.color.rgb = rgb(GRAY_BAR)
    text_box(slide, 0.92, 6.4, 9.5, 0.4, [
        {"runs": [("Código e dados: ", {"bold": True}), ("github.com/pumba-dev/machine-learning-practice", {}),
                  ("  ·  Perguntas?", {"bold": True, "color": GREEN})]},
    ], size=20, name="Repositório")


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    deck = Deck(build_notes(data), out=OUT, notes_md=NOTES_MD, speakers=SPEAKERS, blocks=BLOCK_OF_SLIDE,
                block_titles=BLOCK_TITLE, handoff=HANDOFF, title=TITLE,
                author="Bernan R. do Nascimento; Paulo E. R. Araujo; Thiago R. P. de Carvalho",
                notes_title="Roteiro da terceira apresentação (10 min)")
    for build in (slide_title, slide_base, slide_score, slide_network, slide_scaling, slide_epochs, slide_results,
                  slide_time, slide_ramp, slide_conclusion):
        build(deck, data)
    deck.save()
    print("gravado:", OUT)
    small = audit_fonts(OUT)
    print("texto abaixo de", MIN_FONT, "pt:", small if small else "nenhum")


if __name__ == "__main__":
    main()
