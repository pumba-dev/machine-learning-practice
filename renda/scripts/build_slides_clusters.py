"""Monta slides/apresentacao_clusters.pptx: a quinta apresentação, com o K-means na base de renda.

Passos, a partir da raiz do repositório:

    python renda/scripts/clusters_data.py            # números (resultados do notebook 07), alguns segundos
    python renda/scripts/build_slides_clusters.py    # slides/apresentacao_clusters.pptx e slides/notas_clusters.md
    powershell -File comum/export_slides_pdf.ps1 renda/slides/apresentacao_clusters.pptx   # PDF (exige PowerPoint)

Mesmo template, paleta, regras de acessibilidade (texto de no mínimo 18 pt; na prática, 20 pt) e peças das
apresentações anteriores (comum/slides_common.py): gráficos e tabelas nativos do PowerPoint.
Raça e sexo ficam fora dos slides, por decisão do grupo.
"""
import json
import sys
from pathlib import Path

from pptx.chart.data import CategoryChartData, XyChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_MARKER_STYLE, XL_TICK_LABEL_POSITION, XL_TICK_MARK
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "comum"))  # slides_common.py, compartilhado pelas bases

from slides_common import (GRAY_BAR, GRAY_TINT, GREEN, GREEN_DK, INK, MIN_FONT, MUTED, RED, RED_TINT, TINT, Deck,
                           alt, audit_fonts, br, card, column_chart, number_badge, rgb, shape, style_chart, table,
                           text_box, thousands, write)  # noqa: E402
from slides_clusters_notes import build_notes  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "report" / "results" / "clusters_dados.json"
OUT = ROOT / "slides" / "apresentacao_clusters.pptx"
NOTES_MD = ROOT / "slides" / "notas_clusters.md"

TITLE = "K-means na base de renda"
SPEAKERS = {1: "Thiago", 2: "Paulo", 3: "Bernan"}
BLOCK_OF_SLIDE = [1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3]
BLOCK_TITLE = {1: "O problema e o preparo dos dados",
               2: "A escolha do k: métricas internas e estabilidade",
               3: "Os grupos, a renda e as conclusões"}
HANDOFF = {
    4: (2, "Com os dados preparados, quantos grupos pedir ao K-means?"),
    9: (3, "Com k = 6, quem são esses grupos?"),
}
KS = [str(k) for k in range(2, 11)]
#: Uma cor por grupo, a mesma na tabela, nas barras e no gráfico em 2D.
GROUP_COLOR = {1: "2A78D6", 2: "EB6834", 3: "1BAF7A", 4: "8E5AC8", 5: "9A7A00", 6: "B23A2E"}
GOLD_DK = "9A7A00"


def dec(value, digits=2):
    return br(value, digits)


# --- Gráficos próprios desta apresentação ---------------------------------------------------------

def axis_style(axis, fmt, vmin, vmax, unit):
    axis.minimum_scale, axis.maximum_scale, axis.major_unit = vmin, vmax, unit
    axis.has_major_gridlines = True
    axis.major_gridlines.format.line.color.rgb = rgb("DDE5E3")
    axis.format.line.fill.background()
    axis.tick_labels.number_format = fmt
    axis.tick_labels.number_format_is_linked = False
    axis.tick_labels.font.size = Pt(MIN_FONT)
    axis.tick_labels.font.color.rgb = rgb(MUTED)


def lines(slide, x, y, w, h, series, colors, description, decimals, vmin, vmax, unit, legend=False, highlight=None):
    """Linhas com marcadores sobre k = 2 a 10; `highlight` destaca o marcador de um k.

    Vírgula decimal sem depender do idioma de quem abre o arquivo: os valores (e a escala do eixo) são
    multiplicados por 10^decimals, e o formato põe uma vírgula literal antes dos últimos dígitos."""
    factor = 10 ** decimals
    fmt = '0' if decimals == 0 else '0","' + '0' * decimals
    vmin, vmax, unit = vmin * factor, vmax * factor, unit * factor
    data = CategoryChartData(number_format=fmt)
    data.categories = KS
    for name, values in series:
        data.add_series(name, [round(v * factor, 6) for v in values])
    frame = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(x), Inches(y), Inches(w), Inches(h), data)
    alt(frame, description)
    chart = frame.chart
    style_chart(chart)
    chart.has_legend = legend
    if legend:
        chart.legend.position = XL_LEGEND_POSITION.BOTTOM
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(MIN_FONT)
    for item, color in zip(chart.plots[0].series, colors):
        item.smooth = False
        item.format.line.color.rgb = rgb(color)
        item.format.line.width = Pt(3)
        item.marker.style = XL_MARKER_STYLE.CIRCLE
        item.marker.size = 9
        item.marker.format.fill.solid()
        item.marker.format.fill.fore_color.rgb = rgb(color)
        item.marker.format.line.color.rgb = rgb(color)
        if highlight is not None:
            point = item.points[KS.index(str(highlight))]
            point.marker.size = 15
            point.marker.format.fill.solid()
            point.marker.format.fill.fore_color.rgb = rgb(color)
            point.marker.format.line.color.rgb = rgb("F2C200")
            point.marker.format.line.width = Pt(3)
    axis_style(chart.value_axis, fmt, vmin, vmax, unit)
    chart.category_axis.tick_labels.font.size = Pt(MIN_FONT)
    chart.category_axis.format.line.color.rgb = rgb(GRAY_BAR)
    return chart


def scatter(slide, x, y, w, h, pca, description):
    """Pessoas projetadas nas duas primeiras componentes, uma série por grupo, e os centros em destaque."""
    data = XyChartData()
    for g in range(1, 7):
        series = data.add_series(f"Grupo {g}")
        for px, py in pca["pontos"][str(g)]:
            series.add_data_point(px, py)
    centers = data.add_series("Centros")
    for g in range(1, 7):
        centers.add_data_point(*pca["centros"][str(g)])
    frame = slide.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, Inches(x), Inches(y), Inches(w), Inches(h), data)
    alt(frame, description)
    chart = frame.chart
    style_chart(chart)
    chart.has_legend = False
    plot = chart.plots[0]
    for index, item in enumerate(plot.series):
        item.format.line.fill.background()
        if index < 6:
            color = GROUP_COLOR[index + 1]
            item.marker.style = XL_MARKER_STYLE.CIRCLE
            item.marker.size = 4
            item.marker.format.fill.solid()
            item.marker.format.fill.fore_color.rgb = rgb(color)
            item.marker.format.line.fill.background()
        else:
            item.marker.style = XL_MARKER_STYLE.DIAMOND
            item.marker.size = 16
            for g in range(6):
                point = item.points[g]
                point.marker.format.fill.solid()
                point.marker.format.fill.fore_color.rgb = rgb(GROUP_COLOR[g + 1])
                point.marker.format.line.color.rgb = rgb(INK)
                point.marker.format.line.width = Pt(2)
    for axis, (vmin, vmax) in ((chart.value_axis, (-3, 5)), (chart.category_axis, (-4, 5))):
        axis.minimum_scale, axis.maximum_scale = vmin, vmax
        axis.has_major_gridlines = False
        axis.tick_label_position = XL_TICK_LABEL_POSITION.NONE
        axis.major_tick_mark = XL_TICK_MARK.NONE
        axis.format.line.fill.background()
    return chart


# --- Slides ------------------------------------------------------------------------------------

def slide_title(deck, d):
    slide = deck.slide("Slide de Título", TITLE, title_size=44)
    slide.shapes.title.text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM
    frame = slide.placeholders[1].text_frame
    frame.text = ""
    write(frame, [
        {"text": f"Quinta parte: agrupar {thousands(d['base']['linhas'])} pessoas sem olhar a renda", "size": 24,
         "bold": True, "color": GREEN, "space_after": 8},
        {"text": "Bernan R. do Nascimento · Paulo E. R. Araujo · Thiago R. P. de Carvalho", "size": 22, "bold": True,
         "space_after": 6},
        {"text": "Universidade Federal do Piauí (UFPI)", "size": 20},
        {"text": "PPGCC010 – Aprendizagem de Máquina (2026.2) · Prof. Vinicius Ponte Machado", "size": 20},
    ], align=PP_ALIGN.CENTER)


def slide_unsupervised(deck, d):
    b = d["base"]
    slide = deck.slide("Somente Título", "Agora o modelo não vê a resposta")
    columns = [
        ("Antes: supervisionado", "SVM, rede neural, árvores", ["atributos + renda", "o modelo aprende a prever",
                                                               "acerta ou erra no teste"], GRAY_TINT, INK),
        ("Agora: não supervisionado", "K-means", ["só os atributos", "grupos de pessoas parecidas",
                                                 "a renda entra só no fim, para conferir"], TINT, GREEN_DK),
    ]
    for index, (head, sub, steps, fill, color) in enumerate(columns):
        x = 0.92 + index * 5.75
        card(slide, x, 2.0, 5.4, 3.3, fill, [
            {"text": head, "size": 26, "bold": True, "color": color, "space_after": 2},
            {"text": sub, "size": 20, "color": MUTED, "space_after": 10},
            *[{"text": step, "size": 22, "bullet": True, "space_after": 4} for step in steps],
        ], name=head, anchor=MSO_ANCHOR.TOP, pad=0.3)
    card(slide, 0.92, 5.6, 11.15, 1.15, GREEN_DK, [
        f"Mesmas {thousands(b['linhas'])} pessoas e 10 atributos da SVM · sem treino e teste: os grupos são formados "
        "na base inteira"], name="Base", size=22, bold=True, color="FFFFFF", align=PP_ALIGN.CENTER, pad=0.3)


def slide_algorithm(deck, d):
    slide = deck.slide("Somente Título", "Como o K-means funciona")
    steps = ["Sorteia k centros", "Cada pessoa vai para o centro mais próximo", "Cada centro vira a média do seu grupo",
             "Repete 2 e 3 até os grupos pararem de mudar"]
    for index, text in enumerate(steps):
        x = 0.92 + index * 2.85
        card(slide, x, 2.35, 2.55, 2.25, TINT if index < 3 else GREEN_DK, [
            {"text": text, "size": 22, "bold": index == 3, "color": INK if index < 3 else "FFFFFF",
             "align": PP_ALIGN.CENTER}], name=f"Passo {index + 1}", pad=0.15)
        number_badge(slide, x + 1.0, 1.95, 0.55, str(index + 1), fill=GREEN if index < 3 else GREEN_DK)
        if index < 3:
            arrow = shape(slide, MSO_SHAPE.RIGHT_ARROW, x + 2.58, 3.3, 0.25, 0.4, GREEN, name=f"Seta {index + 1}")
            alt(arrow, "seta para o próximo passo")
    cards = [("Objetivo", "grupos compactos: a menor soma das distâncias de cada pessoa ao seu centro (inércia)"),
             ("Cuidado com o sorteio", "o resultado depende dos centros iniciais: 10 inicializações, fica a melhor")]
    for index, (head, detail) in enumerate(cards):
        card(slide, 0.92 + index * 5.65, 4.95, 5.45, 1.8, GRAY_TINT, [
            {"text": head, "size": 22, "bold": True, "color": GREEN_DK, "space_after": 2},
            {"text": detail, "size": 20},
        ], name=head, pad=0.25)


def slide_distance(deck, d):
    b = d["base"]
    slide = deck.slide("Somente Título", "A distância decide tudo")
    items = [("5 numéricos", "padronização (z-score): média 0 e desvio 1"),
             ("5 de texto", "one-hot: uma coluna 0/1 por categoria, 75 colunas")]
    text_box(slide, 0.92, 2.0, 5.6, 0.45, [f"{b['colunas']} colunas, como na SVM"], size=24, bold=True, color=GREEN_DK)
    for index, (head, detail) in enumerate(items):
        card(slide, 0.92, 2.6 + index * 1.55, 5.6, 1.35, TINT, [
            {"text": head, "size": 24, "bold": True, "color": GREEN_DK, "space_after": 2},
            {"text": detail, "size": 20},
        ], name=head, pad=0.25)
    card(slide, 0.92, 5.8, 5.6, 0.95, GRAY_TINT, [
        {"runs": [(f"{br(b['parte_categoricos'], 0)}%", {"bold": True, "color": GREEN_DK}),
                  (" da distância média vem do texto; o país, só ", {}),
                  (f"{br(b['peso']['país de origem']['parte'], 0)}%", {"bold": True, "color": GREEN_DK})]}],
        name="Peso do texto", size=20, pad=0.25)
    card(slide, 6.95, 2.0, 5.12, 4.75, GREEN_DK, [
        {"text": "Trocar de ocupação", "size": 26, "bold": True, "color": "FFFFFF", "align": PP_ALIGN.CENTER},
        {"text": "afasta duas pessoas tanto quanto", "size": 22, "color": "FFFFFF", "align": PP_ALIGN.CENTER,
         "space_after": 6},
        {"text": f"{br(b['troca_em_anos'], 0)} anos", "size": 60, "bold": True, "color": "F2C200",
         "align": PP_ALIGN.CENTER},
        {"text": "de diferença de idade", "size": 22, "color": "FFFFFF", "align": PP_ALIGN.CENTER, "space_after": 12},
        {"text": "uma coluna apaga e outra acende: a diferença é sempre 2, seja qual for a categoria", "size": 20,
         "color": "FFFFFF", "align": PP_ALIGN.CENTER},
    ], name="Troca de categoria", pad=0.3)


def slide_capital(deck, d):
    b, lg = d["base"], d["log"]
    sem, com = lg["sem"]["grupos"], lg["com"]["grupos"]
    slide = deck.slide("Somente Título", "O capital pede log e ainda forma grupos")
    text_box(slide, 0.92, 2.0, 11.15, 0.45, ["Capital: zero para quase todos, enorme para poucos (k = 4)"],
             size=22, bold=True, color=GREEN_DK)
    columns = [
        ("Sem log", RED_TINT, RED, [(str(sem[3]["pessoas"]), "com ganho de 99.999, o teto do censo, num grupo só delas"),
                                    (thousands(sem[2]["pessoas"]), "com perda de capital, em outro")]),
        ("Com log", TINT, GREEN_DK, [(thousands(com[2]["pessoas"]), f"todos com ganho: {br(com[2]['positivos'], 0)}% "
                                                                    "acima de 50 mil"),
                                     (thousands(com[3]["pessoas"]), f"todos com perda: {br(com[3]['positivos'], 0)}% "
                                                                    "acima de 50 mil")]),
    ]
    for index, (head, fill, color, rows) in enumerate(columns):
        x = 0.92 + index * 5.75
        lines_ = [{"text": head, "size": 26, "bold": True, "color": color, "space_after": 8}]
        for number, caption in rows:
            lines_.append({"runs": [(number + " ", {"bold": True, "color": color, "size": 30}), (caption, {})],
                           "size": 20, "space_after": 8})
        card(slide, x, 2.55, 5.4, 3.0, fill, lines_, name=head, anchor=MSO_ANCHOR.TOP, pad=0.3)
    card(slide, 0.92, 5.75, 11.15, 1.05, GREEN_DK, [
        f"Ter ou não ter capital vira o maior salto da base: 2 dos k grupos ficam com os "
        f"{br(b['com_capital'], 0)}% que têm capital"], name="Conclusão do capital", size=22, bold=True, color="FFFFFF",
         align=PP_ALIGN.CENTER, pad=0.3)


def slide_metrics(deck, d):
    slide = deck.slide("Somente Título", "Três métricas para escolher o k")
    text_box(slide, 0.92, 2.0, 11.15, 0.45, ["Testamos k de 2 a 10, cada um com 10 seeds; nenhuma métrica olha a renda"],
             size=22, bold=True, color=GREEN_DK)
    cards = [("Inércia", "compacidade dos grupos", "sempre cai com k: procurar o cotovelo"),
             ("Silhueta", "cada pessoa está mais perto do próprio grupo que do vizinho?", "de −1 a 1: maior é melhor"),
             ("Davies-Bouldin", "quanto os grupos se sobrepõem", "a partir de 0: menor é melhor")]
    for index, (head, what, best) in enumerate(cards):
        x = 0.92 + index * 3.8
        card(slide, x, 2.65, 3.55, 2.75, TINT, [
            {"text": head, "size": 28, "bold": True, "color": GREEN_DK, "space_after": 6},
            {"text": what, "size": 22},
        ], name=head, anchor=MSO_ANCHOR.TOP, pad=0.25)
        card(slide, x, 5.55, 3.55, 1.2, GREEN_DK, [best], name=f"{head}: leitura", size=20, bold=True,
             color="FFFFFF", align=PP_ALIGN.CENTER, pad=0.2)


def slide_curves(deck, d):
    pk = d["por_k"]
    slide = deck.slide("Somente Título", "As métricas internas não apontam um k claro")
    specs = [("Inércia (mil)", [pk[k]["inercia"] / 1000 for k in KS], 0, 100, 220, 40),
             ("Silhueta (maior, melhor)", [pk[k]["silhueta"] for k in KS], 2, 0.1, 0.35, 0.05),
             ("Davies-Bouldin (menor)", [pk[k]["db"] for k in KS], 1, 1.0, 2.0, 0.2)]
    for index, (head, values, fmt, vmin, vmax, unit) in enumerate(specs):
        x = 0.92 + index * 3.8
        text_box(slide, x, 2.0, 3.6, 0.45, [head], size=20, bold=True, color=GREEN_DK, name=f"Título {index + 1}")
        lines(slide, x - 0.1, 2.45, 3.75, 2.95, [(head, values)], [GREEN_DK],
              f"Gráfico de linha, {head}, para k de 2 a 10: " + "; ".join(
                  f"k {k}: {br(v, 2)}" for k, v in zip(KS, values)) + ".", fmt, vmin, vmax, unit)
    text_box(slide, 0.92, 5.45, 11.15, 0.35, ["k (número de grupos) no eixo horizontal; média das 10 seeds"],
             size=20, color=MUTED, name="Nota")
    card(slide, 0.92, 5.9, 11.15, 0.9, GRAY_TINT, [
        {"runs": [("k = 2 vence, mas só separa quem tem ganho de capital. ", {"bold": True, "color": GREEN_DK}),
                  (f"De 4 em diante, tudo plano: silhueta de {dec(pk['6']['silhueta'])}, grupos pouco separados", {})]}],
        name="Leitura das curvas", size=20, pad=0.25)


def slide_stability(deck, d):
    pk = d["por_k"]
    slide = deck.slide("Somente Título", "As 10 seeds acham os mesmos grupos?")
    text_box(slide, 0.92, 2.0, 7.3, 0.45, ["ARI médio entre as 10 seeds (1 = idênticas)"], size=22, bold=True,
             color=GREEN_DK)
    values = [pk[k]["ari"] for k in KS]
    lines(slide, 0.82, 2.5, 7.5, 3.9, [("ARI", values)], [GREEN_DK],
          "Gráfico de linha: ARI médio entre seeds para k de 2 a 10: " + "; ".join(
              f"k {k}: {br(v, 3)}" for k, v in zip(KS, values)) + ".", 1, 0, 1, 0.2, highlight=6)
    text_box(slide, 0.92, 6.4, 7.3, 0.4, ["k (número de grupos); em destaque, k = 6"], size=20, color=MUTED,
             name="Nota do eixo")
    cards = [(f"{dec(min(pk['5']['ari'], pk['6']['ari'], pk['8']['ari']))} ou mais", "k = 5, 6 e 8: as 10 seeds chegam "
                                                                                    "aos mesmos grupos", TINT, GREEN_DK),
             (f"{dec(pk['3']['ari'])} e {dec(pk['9']['ari'])}", "k = 3 e 9: cada seed divide de um jeito", RED_TINT, RED)]
    for index, (number, caption, fill, color) in enumerate(cards):
        card(slide, 8.6, 2.0 + index * 2.4, 3.47, 2.15, fill, [
            {"text": number, "size": 32, "bold": True, "color": color, "space_after": 4},
            {"text": caption, "size": 20},
        ], name=f"Estabilidade {index + 1}", pad=0.2)


def slide_inits(deck, d):
    pk = d["por_k"]
    k6 = pk["6"]
    slide = deck.slide("Somente Título", "10 inicializações compram estabilidade")
    text_box(slide, 0.92, 2.0, 7.3, 0.45, ["ARI médio entre as 10 seeds"], size=22, bold=True, color=GREEN_DK)
    lines(slide, 0.82, 2.5, 7.5, 4.2, [("10 inicializações", [pk[k]["ari"] for k in KS]),
                                       ("1 inicialização", [pk[k]["ari_1"] for k in KS])], [GREEN_DK, "EB6834"],
          "Gráfico de linha: ARI médio entre seeds com 10 inicializações e com 1, para k de 2 a 10. Com 10: " + "; ".join(
              f"k {k}: {br(pk[k]['ari'], 2)}" for k in KS) + ". Com 1: " + "; ".join(
              f"k {k}: {br(pk[k]['ari_1'], 2)}" for k in KS) + ".", 1, 0, 1, 0.2, legend=True)
    text_box(slide, 8.6, 2.0, 3.47, 0.45, ["Com k = 6"], size=24, bold=True, color=GREEN_DK)
    cards = [(f"{dec(k6['ari_1'])} → {dec(k6['ari'], 3)}", "ARI com 1 e com 10 inicializações", TINT, GREEN_DK),
             (f"+{br(k6['inercia_piora_1'], 0)}%", "inércia com uma só: cada sorteio para num lugar", RED_TINT, RED),
             (f"{br(k6['tempo_s'], 1)} s", "por ajuste com 10, nas 30 mil pessoas", GRAY_TINT, GREEN_DK)]
    for index, (number, caption, fill, color) in enumerate(cards):
        card(slide, 8.6, 2.6 + index * 1.42, 3.47, 1.3, fill, [
            {"text": number, "size": 28, "bold": True, "color": color, "space_after": 0},
            {"text": caption, "size": 20},
        ], name=f"Inicializações {index + 1}", pad=0.2)


def slide_choice(deck, d):
    pk = d["por_k"]
    slide = deck.slide("Somente Título", "Escolhemos k = 6")
    rows = [["Evidência", "O que diz"],
            ["Cotovelo da inércia", "entre 5 e 6"],
            ["Silhueta e Davies-Bouldin", "planas de 4 em diante: não desempatam"],
            ["Estabilidade (ARI)", f"{dec(pk['6']['ari'], 3)} em k = 6, quase perfeita"],
            ["Leitura dos grupos", "4 perfis para quem não tem capital, mais os 2 do capital"]]
    table(slide, 0.92, 2.0, [3.6, 7.55], 0.78, rows, "Tabela da escolha do k",
          "Tabela das evidências para a escolha do k. " + "; ".join(f"{r[0]}: {r[1]}" for r in rows[1:]) + ".",
          fills={4: TINT}, size=20)
    alternatives = [("k = 5", "só 3 grupos sem capital; junta perfis diferentes"),
                    ("k = 8", "6 grupos sem capital; alguns difíceis de distinguir")]
    for index, (head, detail) in enumerate(alternatives):
        card(slide, 0.92 + index * 5.65, 6.05, 5.45, 0.8, GRAY_TINT, [
            {"runs": [(head + ": ", {"bold": True, "color": GREEN_DK}), (detail, {})]}],
            name=f"Alternativa {head}", size=20, pad=0.2)


def slide_groups(deck, d):
    slide = deck.slide("Somente Título", "Seis perfis de pessoas")
    profiles = {1: "26 anos, nunca casados, moram com os pais",
                2: "53 anos, divorciados e viúvos, pouco estudo",
                3: "38 anos, casados, ofícios manuais, 48 h",
                4: "13 anos de estudo, especialistas e gerentes",
                5: "todos com perda de capital",
                6: "todos com ganho de capital"}
    rows = [["Grupo", "Pessoas", "Perfil"]]
    for g in d["grupos"]:
        rows.append([{"text": f"{g['grupo']}. {g['nome']}", "color": GROUP_COLOR[g["grupo"]], "bold": True},
                     thousands(g["pessoas"]), profiles[g["grupo"]]])
    table(slide, 0.92, 2.0, [4.05, 1.2, 5.9], 0.6, rows, "Tabela dos grupos",
          "Tabela dos seis grupos: " + "; ".join(f"{r[0]['text']}, {r[1]} pessoas: {r[2]}" for r in rows[1:]) + ".",
          size=20)
    text_box(slide, 0.92, 6.5, 11.15, 0.35, ["Numerados do menor para o maior % de renda alta; os nomes são nossos"],
             size=20, color=MUTED, name="Nota")


def slide_income(deck, d):
    b = d["base"]
    gr = d["grupos"]
    slide = deck.slide("Somente Título", "Os grupos seguem a renda sem tê-la visto")
    text_box(slide, 0.92, 2.0, 7.6, 0.45, ["Ganham mais de 50 mil, por grupo"], size=24, bold=True, color=GREEN_DK)
    values = [g["positivos"] for g in gr]
    chart = column_chart(slide, 0.92, 2.5, 7.6, 4.3, [str(g["grupo"]) for g in gr], [("% acima de 50 mil", values)],
                         [GREEN_DK], "Gráfico de colunas: % acima de 50 mil por grupo. " + "; ".join(
                             f"grupo {g['grupo']} ({g['nome']}): {br(g['positivos'])}%" for g in gr) + ".", vmax=80)
    chart.has_legend = False
    series = chart.plots[0].series[0]
    for index, g in enumerate(gr):
        point = series.points[index]
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = rgb(GROUP_COLOR[g["grupo"]])
    text_box(slide, 8.85, 2.0, 3.22, 1.9, [
        {"text": f"{br(b['positivos'])}%", "size": 48, "bold": True, "color": GREEN_DK, "space_after": 0},
        {"text": "na base inteira", "size": 20},
    ], name="Base inteira")
    card(slide, 8.85, 4.1, 3.22, 2.7, TINT, [
        {"text": "Idade, estudo, estado civil e capital formam os grupos e também explicam a renda", "size": 20}],
        name="Por quê", pad=0.2)


def slide_describe(deck, d):
    e, ref, gr = d["escolha"], d["referencia"], {g["grupo"]: g for g in d["grupos"]}
    slide = deck.slide("Somente Título", "Os grupos descrevem, não preveem")
    cards = [(f"{br(e['chute'])}%", "chute: ‘até 50 mil’ para todos", GRAY_TINT, INK),
             (f"{br(e['pureza'])}%", "cada grupo chuta a renda da sua maioria (pureza)", TINT, GREEN_DK),
             (f"{br(ref['svm_rbf_acuracia'])}%", "SVM RBF, treinada com a renda", GREEN_DK, "FFFFFF")]
    for index, (number, caption, fill, color) in enumerate(cards):
        card(slide, 0.92 + index * 3.8, 2.0, 3.55, 2.2, fill, [
            {"text": number, "size": 44, "bold": True, "color": color, "align": PP_ALIGN.CENTER, "space_after": 2},
            {"text": caption, "size": 20, "color": "FFFFFF" if index == 2 else INK, "align": PP_ALIGN.CENTER},
        ], name=f"Acerto {index + 1}", pad=0.2)
    items = [("Nenhum grupo é puro", f"nos profissionais, {br(gr[4]['positivos'], 0)}% de renda alta: quase cara ou "
                                     "coroa"),
             ("ARI contra a renda", f"{dec(e['ari_renda'])}: perto do acaso"),
             ("Por quê", "o K-means junta pessoas parecidas em tudo; o classificador aprende o que importa para a renda")]
    for index, (head, detail) in enumerate(items):
        card(slide, 0.92, 4.45 + index * 0.8, 11.15, 0.7, "FFFFFF", [
            {"runs": [(head + ": ", {"bold": True, "color": GREEN_DK}), (detail, {})]}],
            name=head, size=20, pad=0.25).line.color.rgb = rgb(GRAY_BAR)


def slide_pca(deck, d):
    pca, gr = d["pca"], d["grupos"]
    slide = deck.slide("Somente Título", "Grupos são regiões de uma nuvem contínua")
    scatter(slide, 0.82, 2.0, 7.5, 4.35, pca,
            "Gráfico de dispersão: 1.500 pessoas nas duas primeiras componentes principais, coloridas pelo grupo. "
            "Os grupos 5 (perda de capital, em cima) e 6 (ganho de capital, embaixo) ficam isolados; os grupos 1 a 4 "
            "se sobrepõem numa nuvem, do 1 à esquerda ao 4 à direita. Losangos: os centros dos grupos.")
    text_box(slide, 0.92, 6.45, 7.4, 0.4, [f"PCA: só {br(sum(pca['variancia']), 0)}% da variação; losangos = centros"], size=20, color=MUTED, name="Ressalva")
    for index, g in enumerate(gr):
        y = 2.0 + index * 0.8
        dot = shape(slide, MSO_SHAPE.OVAL, 8.65, y + 0.2, 0.3, 0.3, GROUP_COLOR[g["grupo"]], name=f"Cor {g['grupo']}")
        alt(dot, f"cor do grupo {g['grupo']}")
        text_box(slide, 9.1, y, 3.0, 0.72, [f"{g['grupo']}. {g['nome']}"], size=20, name=f"Legenda {g['grupo']}",
                 anchor=MSO_ANCHOR.MIDDLE)


def slide_conclusion(deck, d):
    pk, e = d["por_k"], d["escolha"]
    slide = deck.slide("Somente Título", "Conclusões")
    cards = [("6 perfis", f"estáveis entre seeds (ARI {dec(pk['6']['ari'], 3)}), ordenados pela renda"),
             (dec(e["silhueta"]), "de silhueta: a base não tem grupos nítidos"),
             (f"{br(e['tempo_s'], 1)} s", "por ajuste; o custo cresce linearmente com as pessoas")]
    for index, (number, caption) in enumerate(cards):
        card(slide, 0.92 + index * 3.78, 2.0, 3.55, 2.0, TINT, [
            {"text": number, "size": 40, "bold": True, "color": GREEN_DK, "align": PP_ALIGN.CENTER, "space_after": 4},
            {"text": caption, "size": 20, "align": PP_ALIGN.CENTER},
        ], name=f"Número {index + 1}")
    text_box(slide, 0.92, 4.25, 11.1, 0.45, ["O que aprendemos"], size=24, bold=True, color=GREEN_DK)
    lessons = [("A distância", "escala, one-hot e log mudam os grupos"),
               ("O k", "métricas, estabilidade e leitura juntas"),
               ("O uso", "descrever a população, não prever a renda")]
    for index, (head, detail) in enumerate(lessons):
        card(slide, 0.92 + index * 3.78, 4.8, 3.55, 1.2, "FFFFFF", [
            {"text": head, "size": 22, "bold": True, "color": GREEN_DK, "align": PP_ALIGN.CENTER, "space_after": 0},
            {"text": detail, "size": 20, "align": PP_ALIGN.CENTER},
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
                notes_title="Roteiro da quinta apresentação (10 min)")
    for build in (slide_title, slide_unsupervised, slide_algorithm, slide_distance, slide_capital, slide_metrics,
                  slide_curves, slide_stability, slide_inits, slide_choice, slide_groups, slide_income, slide_describe,
                  slide_pca, slide_conclusion):
        build(deck, data)
    deck.save()
    print("gravado:", OUT)
    small = audit_fonts(OUT)
    print("texto abaixo de", MIN_FONT, "pt:", small if small else "nenhum")


if __name__ == "__main__":
    main()
