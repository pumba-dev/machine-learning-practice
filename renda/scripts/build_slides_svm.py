"""Monta slides/apresentacao_svm.pptx: a quarta apresentação, com a SVM na base de renda comparada com os
modelos de referência e com a rede neural, incluindo o tempo de execução.

Passos, a partir da raiz do repositório:

    python renda/scripts/svm_data.py            # números (resultados das 10 seeds + seed 0), cerca de 1 min
    python renda/scripts/build_slides_svm.py    # slides/apresentacao_svm.pptx e slides/notas_svm.md
    powershell -File comum/export_slides_pdf.ps1 renda/slides/apresentacao_svm.pptx   # PDF (exige PowerPoint)

Mesmo template, paleta, regras de acessibilidade (texto de no mínimo 18 pt) e peças das apresentações
anteriores (comum/slides_common.py): gráficos e tabelas nativos do PowerPoint.
"""
import json
import sys
from pathlib import Path

from lxml import etree
from pptx.chart.data import XyChartData
from pptx.enum.chart import XL_AXIS_CROSSES, XL_CHART_TYPE, XL_LEGEND_POSITION, XL_MARKER_STYLE
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comum"))  # slides_common.py, compartilhado pelas bases

from slides_common import (GOLD, GRAY_BAR, GRAY_TINT, GREEN, GREEN_DK, INK, MIN_FONT, MUTED, RED, RED_TINT, TEAL_BAR,
                           TINT, Deck, alt, audit_fonts, br, card, column_chart, hbar_chart, line_between, rgb, shape,
                           style_chart, table, text_box, thousands, write)  # noqa: E402
from slides_svm_notes import build_notes  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "report" / "results" / "svm_dados.json"
OUT = ROOT / "slides" / "apresentacao_svm.pptx"
NOTES_MD = ROOT / "slides" / "notas_svm.md"

TITLE = "SVM na previsão de renda"
SPEAKERS = {1: "Thiago", 2: "Paulo", 3: "Bernan"}
BLOCK_OF_SLIDE = [1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3]
BLOCK_TITLE = {1: "A base, a curadoria e as réguas",
               2: "Como a SVM funciona: margem, kernel, C e gamma, padronização e custo",
               3: "O que a busca escolheu, resultado, AUC, rede neural e conclusão"}
HANDOFF = {
    4: (2, "Com essas réguas, como a SVM funciona e o que ela precisa para chegar lá?"),
    9: (3, "Com o modelo entendido, o que a busca escolheu e como ficou o resultado?"),
}
POS, NEG = GREEN, GRAY_BAR  # >50K e ≤50K no diagrama


def pts(value, digits=1):
    """Diferença em pontos com sinal: +0,6 pt ou −0,2 pt."""
    text = br(abs(value), digits)
    return f"+{text} pt" if value >= 0 else f"−{text} pt"


def seconds(value):
    if value >= 60:
        return f"{br(value / 60, 0 if value >= 600 else 1)} min"
    return f"{br(value, 0 if value >= 10 else 1 if value >= 1 else 2)} s"


def millis(value):
    return seconds(value / 1000) if value >= 1000 else f"{br(value, 0 if value >= 100 else 1)} ms"


def loglog_chart(slide, x, y, w, h, series, colors, description):
    """Dispersão com linhas, eixos em escala log: tempo de treino por tamanho do treino."""
    data = XyChartData()
    for name, ns, ts in series:
        item = data.add_series(name)
        for n, t in zip(ns, ts):
            item.add_data_point(n, 1000 * t)  # em ms: o eixo fica de 1 a 10.000
    frame = slide.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER_LINES_NO_MARKERS, Inches(x), Inches(y), Inches(w),
                                   Inches(h), data)
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
    xaxis, yaxis = chart.category_axis, chart.value_axis
    for axis, (low, high) in [(xaxis, (1000, 100000)), (yaxis, (1, 10000))]:
        scaling = axis._element.find(qn("c:scaling"))
        log = etree.SubElement(scaling, qn("c:logBase"))
        log.set("val", "10")
        scaling.remove(log)
        scaling.insert(0, log)
        axis.minimum_scale, axis.maximum_scale = low, high
        axis.tick_labels.font.size = Pt(MIN_FONT)
        axis.tick_labels.font.color.rgb = rgb(MUTED)
        axis.format.line.color.rgb = rgb(GRAY_BAR)
        axis.has_major_gridlines = True
        axis.major_gridlines.format.line.color.rgb = rgb("DDE5E3")
    xaxis.crosses = yaxis.crosses = XL_AXIS_CROSSES.MINIMUM  # eixos na borda, não no 1 da escala log
    # Rótulos como texto fixo: o separador de milhar de um formato numérico segue o idioma de quem abre o arquivo.
    xaxis.tick_labels.number_format = '[<5000]"1.000";[<50000]"10.000";"100.000"'
    xaxis.tick_labels.number_format_is_linked = False
    yaxis.tick_labels.number_format = '[<500]0;[<5000]"1.000";"10.000"'
    yaxis.tick_labels.number_format_is_linked = False
    return chart


def heat_color(value, low, high):
    """Escala sequencial de um matiz (verde): claro para valores baixos, escuro para altos."""
    light, dark = (0xEE, 0xF4, 0xF2), (0x0F, 0x43, 0x34)
    t = max(0.0, min(1.0, (value - low) / (high - low))) ** 1.6
    return "".join(f"{round(a + (b - a) * t):02X}" for a, b in zip(light, dark)), t


# --- Slides ------------------------------------------------------------------------------------

def slide_title(deck, d):
    slide = deck.slide("Slide de Título", TITLE, title_size=44)
    slide.shapes.title.text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM
    frame = slide.placeholders[1].text_frame
    frame.text = ""
    write(frame, [
        {"text": "Quarta parte: máquinas de vetores de suporte", "size": 24, "bold": True, "color": GREEN,
         "space_after": 8},
        {"text": "Bernan R. do Nascimento · Paulo E. R. Araujo · Thiago R. P. de Carvalho", "size": 22, "bold": True,
         "space_after": 6},
        {"text": "Universidade Federal do Piauí (UFPI)", "size": 20},
        {"text": "PPGCC010 – Aprendizagem de Máquina (2026.2) · Prof. Vinicius Ponte Machado", "size": 20},
    ], align=PP_ALIGN.CENTER)


def slide_base(deck, d):
    b = d["base"]
    slide = deck.slide("Somente Título", f"{thousands(b['linhas'])} pessoas do censo, 10 atributos")
    items = [
        ("5 numéricos", "idade, anos de estudo, ganho e perda de capital, horas por semana"),
        ("5 de texto", "classe de trabalho, estado civil, ocupação, relacionamento, país"),
        ("Para a SVM", f"texto vira colunas 0/1 (one-hot): {b['colunas_modelo']} colunas no total"),
    ]
    for index, (head, detail) in enumerate(items):
        card(slide, 0.92, 2.0 + index * 1.55, 6.5, 1.38, TINT if index < 2 else GRAY_TINT, [
            {"text": head, "size": 24, "bold": True, "color": GREEN_DK, "space_after": 2},
            {"text": detail, "size": 20},
        ], name=f"Atributos {index + 1}", anchor=MSO_ANCHOR.MIDDLE, pad=0.25)
    text_box(slide, 7.9, 2.0, 4.2, 1.4, [{"text": f"{br(b['positivos'])}%", "size": 72, "bold": True,
                                          "color": GREEN}], name="Renda alta")
    text_box(slide, 7.9, 3.45, 4.2, 0.9, [f"ganham mais de 50 mil: responder sempre ‘não’ acerta {br(b['piso'])}%"],
             size=20, name="Legenda da renda alta")
    card(slide, 7.9, 4.85, 4.2, 1.45, GREEN_DK, ["Rótulo: a renda anual passa de 50 mil dólares?"],
         name="Pergunta", size=24, bold=True, color="FFFFFF", align=PP_ALIGN.CENTER)
    text_box(slide, 7.9, 6.45, 4.2, 0.4, ["Base Adult (UCI), censo de 1994"], size=18, color=MUTED, name="Fonte")


def slide_curation(deck, d):
    b = d["base"]
    slide = deck.slide("Somente Título", f"Curadoria: {thousands(b['duplicadas'] + b['com_ausente'])} linhas e 2 atributos fora")
    steps = [(thousands(b["brutas"]), "linhas no arquivo", GRAY_TINT, INK),
             (thousands(b["brutas"] - b["duplicadas"]), f"− {b['duplicadas']} linhas repetidas", GRAY_TINT, INK),
             (thousands(b["linhas"]), f"− {thousands(b['com_ausente'])} com valor ‘?’", TINT, GREEN_DK)]
    for index, (number, caption, fill, color) in enumerate(steps):
        x = 0.92 + index * 3.85
        card(slide, x, 2.0, 3.35, 1.75, fill, [
            {"text": number, "size": 40, "bold": True, "color": color, "align": PP_ALIGN.CENTER, "space_after": 0},
            {"text": caption, "size": 18, "align": PP_ALIGN.CENTER},
        ], name=f"Etapa {index + 1}")
        if index < 2:
            arrow = shape(slide, MSO_SHAPE.RIGHT_ARROW, x + 3.45, 2.65, 0.32, 0.45, GREEN, name=f"Seta {index + 1}")
            alt(arrow, "seta para a próxima etapa")
    text_box(slide, 0.92, 4.05, 11.1, 0.45, ["Dois atributos fora"], size=24, bold=True, color=GREEN_DK)
    removed = [
        ("fnlwgt", f"peso amostral do censo, não uma característica da pessoa; correlação com a renda: "
                   f"{br(b['correlacao_fnlwgt'], 3).replace('-', '−')}"),
        ("education", "a escolaridade em texto repete os anos de estudo, nível a nível"),
    ]
    for index, (head, detail) in enumerate(removed):
        card(slide, 0.92 + index * 5.65, 4.6, 5.45, 1.75, "FFFFFF", [
            {"text": head, "size": 22, "bold": True, "color": GREEN_DK, "space_after": 2, "font": "Consolas"},
            {"text": detail, "size": 20},
        ], name=f"Removido {head}", anchor=MSO_ANCHOR.MIDDLE, pad=0.25).line.color.rgb = rgb(GRAY_BAR)


def slide_hard(deck, d):
    b = d["base"]
    ec = b["estado_civil"]
    slide = deck.slide("Somente Título", "Nenhum atributo decide sozinho")
    text_box(slide, 0.92, 2.0, 6.9, 0.45, ["Ganham mais de 50 mil, por estado civil"], size=24, bold=True,
             color=GREEN_DK)
    labels, values = list(ec), list(ec.values())
    chart = column_chart(slide, 0.92, 2.5, 6.9, 4.3, labels, [("% acima de 50 mil", values)], [GREEN],
                         "Gráfico de colunas: proporção de pessoas que ganham mais de 50 mil por estado civil. " + "; ".join(
                             f"{k}: {br(v)}%" for k, v in ec.items()) + ".", vmax=60)
    chart.has_legend = False
    text_box(slide, 8.3, 2.0, 3.8, 1.75, [
        {"text": f"{br(b['piso'])}%", "size": 48, "bold": True, "color": RED, "space_after": 0},
        {"text": "regra de um corte: pergunta ‘é casado?’ e responde ‘não’ dos dois lados", "size": 18},
    ], name="Regra de um corte")
    text_box(slide, 8.3, 3.95, 3.8, 1.6, [
        {"text": f"{br(b['teto'])}%", "size": 48, "bold": True, "color": GREEN_DK, "space_after": 0},
        {"text": f"teto: {b['perfis_conflito']} perfis idênticos aparecem com as duas rendas", "size": 18},
    ], name="Teto")
    card(slide, 8.3, 5.75, 3.8, 1.05, GRAY_TINT, [
        {"text": "Na base de empréstimos, um corte acertava 95,5%", "size": 18},
    ], name="Contraste", pad=0.2)


def slide_rulers(deck, d):
    m = d["modelos"]
    slide = deck.slide("Somente Título", "As réguas: 75% de chute, 85% dos clássicos")
    rows = [["Modelo", "Acurácia", "F1 macro", "AUC"]]
    for name, label in [("classe majoritária", "Classe majoritária"), ("regra de um corte", "Regra de um corte"),
                        ("regressão logística", "Regressão logística"), ("árvore de decisão", "Árvore ajustada"),
                        ("random forest", "Random Forest")]:
        info = m[name]
        rows.append([label, f"{br(info['acuracia'])}%", f"{br(info['f1'])}%", f"{br(info['auc'])}%"])
    table(slide, 0.92, 2.0, [3.2, 1.6, 1.6, 1.4], 0.62, rows, "Tabela de referências",
          "Tabela dos modelos de referência, média de 10 seeds: " + "; ".join(
              f"{r[0]}: acurácia {r[1]}, F1 macro {r[2]}, AUC {r[3]}" for r in rows[1:]) + ".",
          fills={3: TINT, 4: TINT, 5: TINT}, size=20)
    text_box(slide, 0.92, 6.0, 7.8, 0.8, [
        {"text": "Média de 10 seeds no teste; F1 macro e AUC porque há 3 pessoas abaixo para cada 1 acima",
         "color": MUTED},
    ], size=18, name="Nota")
    cards = [("Protocolo", "10 seeds · treino 80% e teste 20% · busca com validação cruzada só no treino · "
                           "tempo num único núcleo"),
             ("Meta da SVM", "passar de 85% de acurácia e 78% de F1 macro")]
    for index, (head, detail) in enumerate(cards):
        card(slide, 9.15, 2.0 + index * 2.25, 2.95, 2.05, TINT if index == 0 else GREEN_DK, [
            {"text": head, "size": 22, "bold": True, "color": GREEN_DK if index == 0 else "FFFFFF", "space_after": 4},
            {"text": detail, "size": 18, "color": INK if index == 0 else "FFFFFF"},
        ], name=head, anchor=MSO_ANCHOR.MIDDLE, pad=0.2)


def slide_margin(deck, d):
    m = d["modelos"]
    slide = deck.slide("Somente Título", "A SVM busca a fronteira de maior margem")
    x0, y0, w, h = 0.92, 2.0, 6.2, 4.4
    frame = shape(slide, MSO_SHAPE.RECTANGLE, x0, y0, w, h, "FFFFFF", line="DDE5E3", name="Área do diagrama")
    alt(frame, "Diagrama: pessoas de duas classes separadas por uma reta; duas retas tracejadas marcam a margem; "
               "os pontos sobre as retas tracejadas e um ponto do lado errado, destacados, são os vetores de suporte.")

    def at(u, v):  # coordenadas do diagrama (0 a 1) em polegadas; v cresce para cima
        return x0 + 0.3 + u * (w - 0.6), y0 + h - 0.3 - v * (h - 0.6)

    margin = 0.17
    for offset, dash, color, width in [(0, False, GREEN_DK, 3), (margin, True, MUTED, 1.75), (-margin, True, MUTED, 1.75)]:
        u1, u2 = max(0, -offset), min(1, 1 - offset)
        (ax, ay), (bx, by) = at(u1, u1 + offset), at(u2, u2 + offset)
        line_between(slide, ax, ay, bx, by, color, width=width, dash=dash, name="Fronteira" if offset == 0 else "Margem")
    positives = [(0.08, 0.55), (0.15, 0.82), (0.25, 0.68), (0.3, 0.92), (0.42, 0.85), (0.5, 0.95), (0.12, 0.35)]
    negatives = [(0.55, 0.12), (0.7, 0.3), (0.8, 0.15), (0.9, 0.45), (0.62, 0.05), (0.88, 0.7), (0.75, 0.5)]
    support_pos = [(0.25, 0.25 + margin), (0.55, 0.55 + margin)]
    support_neg = [(0.4, 0.4 - margin), (0.68, 0.68 - margin)]
    wrong = [(0.5, 0.45)]  # >50K do lado errado: também é vetor de suporte
    size = 0.28
    for points, fill, ring in [(positives, POS, False), (negatives, NEG, False), (support_pos, POS, True),
                               (support_neg, NEG, True), (wrong, POS, True)]:
        for u, v in points:
            px, py = at(u, v)
            dot = shape(slide, MSO_SHAPE.OVAL, px - size / 2, py - size / 2, size, size, fill, name="Pessoa")
            if ring:
                dot.line.color.rgb = rgb(GOLD)
                dot.line.width = Pt(4)
    text_box(slide, x0, 6.5, w, 0.4, [{"runs": [("● >50K", {"color": POS, "bold": True}), ("   ", {}),
                                                ("● ≤50K", {"color": NEG, "bold": True}), ("   ", {}),
                                                ("○ vetor de suporte", {"color": "9A7A00", "bold": True})]}],
             size=18, name="Legenda do diagrama")
    rbf = m["SVM RBF"]
    cards = [
        ("Vetores de suporte", "os pontos na margem ou do lado errado: só eles definem a fronteira"),
        ("C", "custo de cada erro: C pequeno, margem larga; C grande, estreita"),
        (f"≈ {thousands(round(rbf['vetores'], -2))}", f"vetores de suporte nesta base, "
                                                      f"{br(100 * rbf['vetores'] / d['seed0']['treino'], 0)}% do treino"),
    ]
    for index, (head, detail) in enumerate(cards):
        card(slide, 7.55, 2.0 + index * 1.55, 4.55, 1.4, TINT if index < 2 else GRAY_TINT, [
            {"text": head, "size": 22, "bold": True, "color": GREEN_DK, "space_after": 2},
            {"text": detail, "size": 18},
        ], name=f"Explicação {index + 1}", anchor=MSO_ANCHOR.MIDDLE, pad=0.2)


def slide_kernels(deck, d):
    k = d["seed0"]["kernels"]
    slide = deck.slide("Somente Título", "O kernel permite curvar a fronteira")
    rows = [["Com C = 1, seed 0", "Acurácia", "Treino"]]
    for name, label in [("LinearSVC", "Linear (LinearSVC)"), ("SVC linear", "Linear (SVC)"),
                        ("SVC polinomial grau 2", "Polinomial, grau 2"), ("SVC polinomial grau 3", "Polinomial, grau 3"),
                        ("SVC RBF", "RBF")]:
        rows.append([label, f"{br(k[name]['acuracia'])}%", seconds(k[name]["treino_s"])])
    table(slide, 0.92, 2.0, [3.6, 1.7, 1.5], 0.62, rows, "Tabela de kernels",
          "Tabela: os kernels com C = 1 na seed 0. " + "; ".join(
              f"{r[0]}: acurácia {r[1]}, treino {r[2]}" for r in rows[1:]) + ".", fills={1: TINT}, size=20)
    razao = k["SVC linear"]["treino_s"] / k["LinearSVC"]["treino_s"]
    text_box(slide, 0.92, 5.95, 6.8, 0.9, [
        {"runs": [("Mesma reta, ", {"bold": True}),
                  (f"{br(razao, 0)} vezes mais rápida: a comparação usa a LinearSVC", {})]},
    ], size=20, name="LinearSVC")
    cards = [("Linear", "uma reta (hiperplano) nas 80 colunas"),
             ("Polinomial", "produtos de atributos, como idade × horas"),
             ("RBF", "curva em torno dos pontos; gamma é o alcance de cada um")]
    for index, (head, detail) in enumerate(cards):
        card(slide, 8.2, 2.0 + index * 1.6, 3.9, 1.42, TINT if index != 2 else GREEN_DK, [
            {"text": head, "size": 22, "bold": True, "color": GREEN_DK if index != 2 else "FFFFFF", "space_after": 2},
            {"text": detail, "size": 18, "color": INK if index != 2 else "FFFFFF"},
        ], name=f"Kernel {head}", anchor=MSO_ANCHOR.MIDDLE, pad=0.2)


def slide_map(deck, d):
    mapa = d["mapa"]
    slide = deck.slide("Somente Título", "C e gamma formam um platô na diagonal")
    text_box(slide, 0.92, 1.95, 7.5, 0.45, ["Acurácia na validação (%), kernel RBF, seed 0"], size=22, bold=True,
             color=GREEN_DK)
    cw, ch, lx, top = 0.94, 0.66, 0.92, 2.5
    text_box(slide, lx, top, 1.05, ch, ["C \\ γ"], size=18, bold=True, color=MUTED, anchor=MSO_ANCHOR.MIDDLE,
             align=PP_ALIGN.CENTER, name="Canto")
    for j, gamma in enumerate(mapa["gamma"]):
        text_box(slide, lx + 1.05 + j * cw, top, cw, ch, [f"{br(gamma, 3).rstrip('0').rstrip(',')}"], size=18,
                 bold=True, color=MUTED, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, name=f"gamma {gamma}")
    best = mapa["melhor"]
    for i, C in enumerate(mapa["C"]):
        y = top + ch + i * ch
        text_box(slide, lx, y, 1.05, ch, [f"{br(C, 2).rstrip('0').rstrip(',')}"], size=18, bold=True, color=MUTED,
                 anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, name=f"C {C}")
        for j, gamma in enumerate(mapa["gamma"]):
            value = mapa["acuracia"][i][j]
            fill, t = heat_color(value, 75, best["acuracia"])
            cell = shape(slide, MSO_SHAPE.RECTANGLE, lx + 1.05 + j * cw, y, cw - 0.04, ch - 0.04, fill,
                         name=f"Célula C={C} gamma={gamma}")
            if C == best["C"] and gamma == best["gamma"]:
                cell.line.color.rgb = rgb(GOLD)
                cell.line.width = Pt(4)
            frame = cell.text_frame
            frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
            frame.vertical_anchor = MSO_ANCHOR.MIDDLE
            write(frame, [br(value)], size=18, bold=True, color="FFFFFF" if t > 0.45 else INK, align=PP_ALIGN.CENTER)
    grid = slide.shapes[-1]
    alt(grid, "Mapa de calor: acurácia na validação para C (linhas) e gamma (colunas). " + "; ".join(
        f"C {C}: " + ", ".join(br(v) for v in linha) for C, linha in zip(mapa["C"], mapa["acuracia"])) + ".")
    g1 = mapa["gamma1_C1"]
    cards = [
        (f"{br(best['acuracia'], 2)}%", f"melhor: C = {br(best['C'], 0)}, γ = {br(best['gamma'])}; "
                                        f"{mapa['perto_do_melhor']} de {mapa['combinacoes']} a até 0,5 ponto", TINT),
        (f"{br(mapa['acuracia'][0][0])}%", "C e γ pequenos: o modelo vira o chute", RED_TINT),
        (f"{br(g1['treino'])} × {br(g1['validacao'])}", "γ = 1: treino contra validação, o modelo decora", RED_TINT),
    ]
    for index, (number, caption, fill) in enumerate(cards):
        card(slide, 8.65, 2.0 + index * 1.62, 3.45, 1.45, fill, [
            {"text": number, "size": 28, "bold": True, "color": GREEN_DK if index == 0 else RED, "space_after": 0},
            {"text": caption, "size": 18},
        ], name=f"Leitura {index + 1}", anchor=MSO_ANCHOR.MIDDLE, pad=0.2)


def slide_scaling(deck, d):
    pad, b = d["seed0"]["padronizacao"], d["base"]
    slide = deck.slide("Somente Título", "Sem padronização, o RBF perde 4 pontos")
    pairs = [("RBF", pad["RBF sem"], pad["RBF com"], RED), ("SVM linear", pad["LinearSVC sem"], pad["LinearSVC com"],
                                                           GREEN_DK)]
    for row, (name, sem, com, color) in enumerate(pairs):
        y = 2.0 + row * 1.85
        text_box(slide, 0.92, y, 1.9, 1.6, [name], size=24, bold=True, color=GREEN_DK, anchor=MSO_ANCHOR.MIDDLE,
                 name=f"Modelo {name}")
        for col, (label, info, fill, ink) in enumerate([("sem padronização", sem, RED_TINT if row == 0 else GRAY_TINT,
                                                         color), ("com padronização", com, TINT, GREEN_DK)]):
            card(slide, 2.9 + col * 2.55, y, 2.35, 1.6, fill, [
                {"text": f"{br(info['acuracia'])}%", "size": 36, "bold": True, "color": ink, "align": PP_ALIGN.CENTER,
                 "space_after": 0},
                {"text": label, "size": 18, "align": PP_ALIGN.CENTER},
            ], name=f"{name} {label}")
    text_box(slide, 8.4, 2.0, 3.7, 0.45, ["Escalas dos numéricos"], size=24, bold=True, color=GREEN_DK)
    f = b["faixas"]
    rows = [["Atributo", "Faixa"], ["ganho de capital", f"0 a {thousands(f['capital.gain'][1])}"],
            ["perda de capital", f"0 a {thousands(f['capital.loss'][1])}"],
            ["idade", f"{f['age'][0]} a {f['age'][1]}"], ["anos de estudo", f"{f['education.num'][0]} a "
                                                                            f"{f['education.num'][1]}"]]
    table(slide, 8.4, 2.55, [2.1, 1.6], 0.56, rows, "Tabela de escalas",
          "Tabela: faixas dos atributos numéricos. " + "; ".join(f"{r[0]}: {r[1]}" for r in rows[1:]) + ".", size=18)
    card(slide, 0.92, 5.75, 11.18, 1.1, GRAY_TINT, [
        {"runs": [("RBF mede distâncias: ", {"bold": True, "color": GREEN_DK}),
                  ("sem padronizar, o ganho de capital domina", {})]},
        {"runs": [("SVM linear: ", {"bold": True, "color": GREEN_DK}),
                  ("um peso por atributo, e a escala deixa de importar", {})]},
    ], name="Por quê", size=20, pad=0.3)


def slide_cost(deck, d):
    t, m = d["tempo_por_tamanho"], d["modelos"]
    slide = deck.slide("Somente Título", "O custo da SVM com kernel cresce rápido")
    text_box(slide, 0.92, 1.95, 7.2, 0.45, ["Treino (ms) por nº de pessoas, escala log"], size=22, bold=True,
             color=GREEN_DK)
    series = [("SVC RBF", t["SVC RBF"]["n"], t["SVC RBF"]["tempo_s"]),
              ("Random Forest", t["random forest"]["n"], t["random forest"]["tempo_s"]),
              ("LinearSVC", t["LinearSVC"]["n"], t["LinearSVC"]["tempo_s"])]
    loglog_chart(slide, 0.92, 2.45, 7.3, 4.4, series, [RED, GRAY_BAR, GREEN],
                 "Gráfico log-log do tempo de treino (s) contra o número de pessoas no treino. " + "; ".join(
                     f"{name}: " + ", ".join(f"{thousands(n)} pessoas {br(s, 3)} s" for n, s in zip(ns, ts))
                     for name, ns, ts in series) + ".")
    rbf, lin = m["SVM RBF"], m["SVM linear"]
    cards = [
        (f"{br(t['SVC RBF']['inclinacao'])} × {br(t['LinearSVC']['inclinacao'])}",
         "inclinação: dobrar o treino quadruplica o tempo da SVC", RED),
        (f"{seconds(t['SVC RBF']['tempo_s'][-1])} × {seconds(t['LinearSVC']['tempo_s'][-1])}",
         f"treino com {thousands(d['seed0']['treino'])} pessoas: SVC RBF × LinearSVC", GREEN_DK),
        (f"{millis(rbf['previsao_ms'])} × {millis(lin['previsao_ms'])}",
         "previsão do teste: a SVC compara cada pessoa com os vetores de suporte", GREEN_DK),
    ]
    for index, (number, caption, color) in enumerate(cards):
        text_box(slide, 8.6, 2.0 + index * 1.62, 3.5, 1.5, [
            {"text": number, "size": 30, "bold": True, "color": color, "space_after": 0},
            {"text": caption, "size": 18},
        ], name=f"Custo {index + 1}")


def slide_grids(deck, d):
    e, m = d["escolhas"], d["modelos"]
    slide = deck.slide("Somente Título", "O que testamos e o que a busca escolheu")

    def top(name):
        texto, n = next(iter(e[name].items()))
        return json.loads(texto), n

    lin, n_lin = top("SVM linear")
    poly, n_poly = top("SVM polinomial")
    rbf_c = sum(n for texto, n in e["SVM RBF"].items() if json.loads(texto)["C"] == 1)
    gammas = {}
    for texto, n in e["SVM RBF"].items():
        p = json.loads(texto)
        if p["C"] == 1:
            gammas[p["gamma"]] = n
    arv = e["árvore de decisão"]
    rows = [["Modelo", "Valores testados", "Escolha nas 10 seeds"],
            ["Árvore de decisão", "critério × profundidade × folha mínima (30)",
             f"{arv['combinacoes']} escolhas; profundidade ≥ {arv['profundidade_min']}"],
            ["SVM linear", "C ∈ {0,001; 0,01; 0,1; 1; 10}", f"C = {br(lin['C'])} em {n_lin} seeds"],
            ["SVM RBF", "C ∈ {0,1; 1; 10; 100} × γ ∈ {0,01; 0,03; 0,1; 0,3}",
             f"C = 1 em {rbf_c}; γ = " + " ou ".join(f"{br(gm)} ({n})" for gm, n in gammas.items())],
            ["SVM polinomial", "grau ∈ {2; 3} × C ∈ {0,1; 1; 10}", f"grau {poly['degree']}, C = {br(poly['C'], 0)} em "
                                                                     f"{n_poly} seeds"],
            ["Rede neural", "6 arquiteturas × 2 alphas × 2 taxas (24)",
             f"{len(e['rede neural'])} escolhas em 10 seeds"]]
    table(slide, 0.92, 2.0, [2.35, 5.15, 3.68], 0.74, rows, "Tabela de grades",
          "Tabela das grades de busca e das escolhas. " + "; ".join(f"{r[0]}: testou {r[1]}; escolheu {r[2]}"
                                                                    for r in rows[1:]) + ".",
          fills={2: TINT, 3: TINT, 4: TINT}, size=18)
    text_box(slide, 0.92, 6.55, 11.1, 0.4, [
        {"runs": [("A SVM repete a escolha; ", {"bold": True}),
                  ("na árvore e na rede, várias configurações empatam", {})]},
    ], size=18, name="Leitura")


def slide_results(deck, d):
    m, c = d["modelos"], d["comparacoes"]
    order = [("SVM RBF", "SVM RBF"), ("SVM polinomial", "SVM polinomial"), ("árvore de decisão", "Árvore ajustada"),
             ("rede neural", "Rede neural"), ("regressão logística", "Regressão logística"),
             ("SVM linear", "SVM linear"), ("random forest", "Random Forest")]
    values = [m[name]["acuracia"] for name, _ in order]
    colors = [GREEN_DK if name.startswith("SVM") else TEAL_BAR if name == "rede neural" else GRAY_BAR
              for name, _ in order]
    slide = deck.slide("Somente Título", "A SVM RBF tem a melhor acurácia, por pouco")
    text_box(slide, 0.92, 2.0, 7.2, 0.45, ["Acurácia no teste, média de 10 seeds"], size=24, bold=True, color=GREEN_DK)
    hbar_chart(slide, 0.92, 2.5, 7.3, 3.9, [label for _, label in order], values, colors,
               "Gráfico de barras, eixo de 80% a 90%: " + "; ".join(
                   f"{label} {br(value)}%" for (_, label), value in zip(order, values)) + ".", vmin=80, vmax=90)
    text_box(slide, 0.92, 6.45, 7.3, 0.4, ["Eixo a partir de 80%; em verde-escuro, as SVMs"],
             size=18, color=MUTED, name="Nota do eixo")
    for index, (key, label, color) in enumerate([
            ("SVM RBF × SVM linear", "sobre a SVM linear", GREEN_DK),
            ("SVM RBF × random forest", "sobre a Random Forest", GREEN_DK),
            ("SVM RBF × árvore de decisão", "sobre a árvore: empate", "9A7A00")]):
        info = c[key]["acuracia"]
        text_box(slide, 8.6, 2.0 + index * 1.6, 3.5, 1.45, [
            {"text": pts(info["pontos"]), "size": 36, "bold": True, "color": color, "space_after": 0},
            {"text": f"{label}; melhor em {info['seeds']} de 10 seeds", "size": 18},
        ], name=f"Comparação {index + 1}")


def slide_auc(deck, d):
    m, c, g = d["modelos"], d["comparacoes"], d["gamma_rbf"]
    order = [("rede neural", "Rede neural"), ("SVM linear", "SVM linear"), ("SVM polinomial", "SVM polinomial"),
             ("regressão logística", "Regressão logística"), ("árvore de decisão", "Árvore ajustada"),
             ("random forest", "Random Forest"), ("SVM RBF", "SVM RBF")]
    values = [m[name]["auc"] for name, _ in order]
    colors = [RED if name == "SVM RBF" else TEAL_BAR if name == "rede neural" else GREEN_DK if name.startswith("SVM")
              else GRAY_BAR for name, _ in order]
    slide = deck.slide("Somente Título", "Pela AUC, a ordem se inverte")
    text_box(slide, 0.92, 2.0, 7.2, 0.45, ["AUC no teste, média de 10 seeds"], size=24, bold=True, color=GREEN_DK)
    hbar_chart(slide, 0.92, 2.5, 7.3, 3.9, [label for _, label in order], values, colors,
               "Gráfico de barras, eixo de 85% a 95%: " + "; ".join(
                   f"{label} {br(value)}%" for (_, label), value in zip(order, values)) + ".", vmin=85, vmax=95)
    text_box(slide, 0.92, 6.45, 7.3, 0.4, ["Eixo a partir de 85%; média de 10 seeds"],
             size=18, color=MUTED, name="Nota do eixo")
    info = c["SVM RBF × SVM linear"]["auc"]
    text_box(slide, 8.6, 2.0, 3.5, 1.45, [
        {"text": pts(info["pontos"]), "size": 36, "bold": True, "color": RED, "space_after": 0},
        {"text": f"SVM RBF contra a linear; abaixo em {10 - info['seeds']} de 10 seeds", "size": 18},
    ], name="RBF contra linear")
    card(slide, 8.6, 3.6, 3.5, 1.5, GRAY_TINT, [
        {"text": "A busca escolhe pela acurácia e prefere γ alto: acerta o lado, ordena pior", "size": 18},
    ], name="Motivo", pad=0.2)
    rows = [["γ escolhido", "AUC"], [f"0,3 ({g['0.3']['seeds']} seeds)", f"{br(g['0.3']['auc'])}%"],
            [f"0,1 ({g['0.1']['seeds']} seeds)", f"{br(g['0.1']['auc'])}%"]]
    table(slide, 8.6, 5.25, [2.1, 1.4], 0.52, rows, "Tabela de gamma",
          f"Tabela: AUC da SVM RBF por gamma escolhido. 0,3: {rows[1][1]}; 0,1: {rows[2][1]}.", size=18)


def slide_network(deck, d):
    m, c = d["modelos"], d["comparacoes"]
    rbf, rede = m["SVM RBF"], m["rede neural"]
    slide = deck.slide("Somente Título", "A rede alcança a SVM a uma fração do custo")
    rows = [["10 seeds", "SVM RBF", "Rede neural"],
            ["Acurácia", {"text": f"{br(rbf['acuracia'])}%", "bold": True}, f"{br(rede['acuracia'])}%"],
            ["F1 macro", f"{br(rbf['f1'])}%", {"text": f"{br(rede['f1'])}%", "bold": True}],
            ["AUC", f"{br(rbf['auc'])}%", {"text": f"{br(rede['auc'])}%", "bold": True}],
            ["Busca por seed", seconds(rbf["busca_s"]), {"text": seconds(rede["busca_s"]), "bold": True}],
            ["Previsão do teste", millis(rbf["previsao_ms"]), {"text": millis(rede["previsao_ms"]), "bold": True}]]
    table(slide, 0.92, 2.0, [3.0, 2.2, 2.2], 0.68, rows, "Tabela SVM contra rede",
          "Tabela: SVM RBF contra rede neural. " + "; ".join(
              f"{r[0]}: SVM {r[1]['text'] if isinstance(r[1], dict) else r[1]}, rede "
              f"{r[2]['text'] if isinstance(r[2], dict) else r[2]}" for r in rows[1:]) + ".",
          fills={4: TINT, 5: TINT}, size=20)
    cr = c["rede neural × SVM RBF"]
    items = [("Acurácia", f"SVM à frente em {10 - cr['acuracia']['seeds']} de 10", GREEN_DK),
             ("F1 macro", f"rede à frente em {cr['f1']['seeds']} de 10: empate", "9A7A00"),
             ("AUC", f"rede à frente em {cr['auc']['seeds']} de 10", TEAL_BAR)]
    text_box(slide, 8.85, 2.0, 3.25, 0.45, ["Seed a seed"], size=24, bold=True, color=GREEN_DK)
    for index, (head, detail, color) in enumerate(items):
        card(slide, 8.85, 2.6 + index * 1.4, 3.25, 1.25, GRAY_TINT, [
            {"text": head, "size": 22, "bold": True, "color": color, "space_after": 0},
            {"text": detail, "size": 18},
        ], name=f"Seed a seed {head}", anchor=MSO_ANCHOR.MIDDLE, pad=0.2)
    text_box(slide, 0.92, 6.25, 7.6, 0.6, [
        {"runs": [("Mesma rede e mesma grade da parte 3; ", {"bold": True}),
                  ("treinada para estimar probabilidade, ordena melhor", {})]},
    ], size=18, name="Rede")


def slide_conclusion(deck, d):
    m = d["modelos"]
    slide = deck.slide("Somente Título", "Conclusões")
    cards = [
        (f"{br(m['SVM RBF']['acuracia'])}%", "SVM RBF: a melhor acurácia, menos de 1 ponto acima da reta"),
        (f"{br(m['rede neural']['auc'])}%", "rede neural: a melhor AUC, a uma fração do custo"),
        ("n²", "o custo de treino da SVM com kernel"),
    ]
    for index, (number, caption) in enumerate(cards):
        card(slide, 0.92 + index * 3.78, 2.0, 3.55, 2.0, TINT, [
            {"text": number, "size": 40, "bold": True, "color": GREEN_DK, "align": PP_ALIGN.CENTER, "space_after": 4},
            {"text": caption, "size": 18, "align": PP_ALIGN.CENTER},
        ], name=f"Número {index + 1}")
    text_box(slide, 0.92, 4.25, 11.1, 0.45, ["O que aprendemos"], size=24, bold=True, color=GREEN_DK)
    lessons = [("Padronizar", "obrigatório no kernel RBF"),
               ("C e gamma", "uma faixa boa, não um ponto ótimo"),
               ("O critério", "acurácia e AUC escolhem modelos diferentes")]
    for index, (head, detail) in enumerate(lessons):
        card(slide, 0.92 + index * 3.78, 4.8, 3.55, 1.2, "FFFFFF", [
            {"text": head, "size": 22, "bold": True, "color": GREEN_DK, "align": PP_ALIGN.CENTER, "space_after": 0},
            {"text": detail, "size": 18, "align": PP_ALIGN.CENTER},
        ], name=f"Lição {index + 1}").line.color.rgb = rgb(GRAY_BAR)
    text_box(slide, 0.92, 6.4, 11.1, 0.4, [
        {"runs": [("Código e dados: ", {"bold": True}), ("github.com/pumba-dev/machine-learning-practice", {}),
                  ("  ·  Perguntas?", {"bold": True, "color": GREEN})]},
    ], size=20, name="Repositório")


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    deck = Deck(build_notes(data), out=OUT, notes_md=NOTES_MD, speakers=SPEAKERS, blocks=BLOCK_OF_SLIDE,
                block_titles=BLOCK_TITLE, handoff=HANDOFF, title=TITLE,
                author="Bernan R. do Nascimento; Paulo E. R. Araujo; Thiago R. P. de Carvalho",
                notes_title="Roteiro da quarta apresentação (10 min)")
    for build in (slide_title, slide_base, slide_curation, slide_hard, slide_rulers, slide_margin, slide_kernels,
                  slide_map, slide_scaling, slide_cost, slide_grids, slide_results, slide_auc, slide_network,
                  slide_conclusion):
        build(deck, data)
    deck.save()
    print("gravado:", OUT)
    small = audit_fonts(OUT)
    print("texto abaixo de", MIN_FONT, "pt:", small if small else "nenhum")


if __name__ == "__main__":
    main()
