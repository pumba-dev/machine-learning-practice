"""Peças comuns dos dois decks (primeira apresentação e comparação de modelos): paleta, texto,
formas, gráficos nativos, número do slide, notas do apresentador e a classe `Deck`, que parte do
template da SBC.

Os decks ficam em build_slides.py (primeira apresentação) e build_slides_rt.py (segunda).
"""
import io
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.dml import MSO_LINE
from pptx.enum.lang import MSO_LANGUAGE_ID
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "slides" / "template" / "Template Apresentações SBC.pptx"

# Paleta: verdes do fundo da SBC, ouro de apoio e as cores de classe dos gráficos do relatório.
# Acessibilidade (projetor, sala iluminada, plateia com baixa visão): texto de no mínimo 18 pt, cores
# escuras sobre fundo claro e barras com contraste de pelo menos 3:1 contra o branco.
MIN_FONT = 18
INK = "1F2A2E"
GREEN = "09846C"
GREEN_DK = "0F4334"
TINT = "E3F0EC"
MUTED = "3C4649"
GRAY_BAR = "8A9795"
TEAL_BAR = "4E9C8A"
GOLD = "E3B505"
RED = "B23A2E"
RED_TINT = "F6E4E0"
CLASS_COLOR = {"EGFR": "2A78D6", "BACE1": "EB6834", "DRD2": "1BAF7A", "HDAC1": "EDA100"}
CLASS_TINT = {"EGFR": "D9E7F8", "BACE1": "FBE1D5", "DRD2": "D2F0E4", "HDAC1": "FBEFC9"}


def br(value, digits=1):
    """Número com vírgula decimal."""
    return f"{value:.{digits}f}".replace(".", ",")


def thousands(value):
    return f"{value:,}".replace(",", ".")


def rgb(hex_color):
    return RGBColor.from_string(hex_color)


# --- Texto e formas -----------------------------------------------------------------------------

def write(frame, lines, size=20, color=INK, bold=False, align=PP_ALIGN.LEFT, font=None):
    """Escreve `lines` num text frame. Cada linha é str ou dict(text|runs, size, bold, color, align,
    space_after, bullet, font). Um run é str ou (str, dict(size, bold, color, font))."""
    first = True
    for line in lines:
        item = {"text": line} if isinstance(line, str) else line
        paragraph = frame.paragraphs[0] if first else frame.add_paragraph()
        first = False
        paragraph.alignment = item.get("align", align)
        if "space_after" in item:
            paragraph.space_after = Pt(item["space_after"])
        runs = item.get("runs") or [item.get("text", "")]
        for run_spec in runs:
            text, style = (run_spec, {}) if isinstance(run_spec, str) else run_spec
            run = paragraph.add_run()
            run.text = text
            run.font.size = Pt(max(MIN_FONT, style.get("size", item.get("size", size))))
            run.font.language_id = MSO_LANGUAGE_ID.BRAZILIAN_PORTUGUESE
            run.font.bold = style.get("bold", item.get("bold", bold))
            run.font.color.rgb = rgb(style.get("color", item.get("color", color)))
            name = style.get("font", item.get("font", font))
            if name:
                run.font.name = name
        if item.get("bullet"):
            bullet(paragraph)


def bullet(paragraph, indent=0.25):
    """Marcador de lista de verdade (propriedade do parágrafo), não um caractere no texto."""
    properties = paragraph._p.get_or_add_pPr()
    properties.set("marL", str(int(Inches(indent))))
    properties.set("indent", str(-int(Inches(indent))))
    marker = etree.SubElement(properties, qn("a:buChar"))
    marker.set("char", "•")


def text_box(slide, x, y, w, h, lines, anchor=MSO_ANCHOR.TOP, name=None, **style):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.word_wrap = True
    frame.vertical_anchor = anchor
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(frame, side, 0)
    write(frame, lines, **style)
    if name:
        box.name = name
    return box


def shape(slide, kind, x, y, w, h, fill, line=None, radius=None, name=None):
    item = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    item.shadow.inherit = False
    if fill is None:
        item.fill.background()
    else:
        item.fill.solid()
        item.fill.fore_color.rgb = rgb(fill)
    if line is None:
        item.line.fill.background()
    else:
        item.line.color.rgb = rgb(line)
        item.line.width = Pt(1.25)
    if radius is not None and kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        item.adjustments[0] = radius
    if name:
        item.name = name
    return item


def card(slide, x, y, w, h, fill, lines=None, name=None, anchor=MSO_ANCHOR.MIDDLE, pad=0.18, **style):
    """Retângulo arredondado, com texto opcional dentro."""
    item = shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill, radius=0.08, name=name)
    if lines:
        frame = item.text_frame
        frame.word_wrap = True
        frame.vertical_anchor = anchor
        frame.margin_left = frame.margin_right = Inches(pad)
        frame.margin_top = frame.margin_bottom = Inches(0.06)
        write(frame, lines, **style)
    return item


def line_between(slide, x1, y1, x2, y2, color, width=1.5, dash=False, name=None):
    connector = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    connector.line.color.rgb = rgb(color)
    connector.line.width = Pt(width)
    if dash:
        connector.line.dash_style = MSO_LINE.DASH
    if name:
        connector.name = name
    return connector


def number_badge(slide, x, y, diameter, label, fill=GREEN):
    badge = shape(slide, MSO_SHAPE.OVAL, x, y, diameter, diameter, fill, name=f"Número {label}")
    frame = badge.text_frame
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = 0
    frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    write(frame, [label], size=26, bold=True, color="FFFFFF", align=PP_ALIGN.CENTER)


def alt(item, text):
    """Texto alternativo (leitor de tela) do primeiro objeto de desenho de `item`."""
    item._element.xpath(".//p:cNvPr")[0].set("descr", text)


# --- Gráficos ----------------------------------------------------------------------------------

def style_chart(chart, size=18):
    chart.has_title = False
    chart.font.size = Pt(size)
    chart.font.color.rgb = rgb(INK)


def label_points(series, values, size=20):
    """Rótulo de cada ponto como texto, com vírgula decimal e o mesmo arredondamento do restante do
    texto. O formato numérico do gráfico segue o idioma de quem abre o arquivo e mostraria ponto."""
    for index, value in enumerate(values):
        label = series.points[index].data_label
        frame = label.text_frame
        frame.text = f"{br(value)}%"
        run = frame.paragraphs[0].runs[0]
        run.font.size = Pt(size)
        run.font.bold = True
        run.font.color.rgb = rgb(INK)
        label.position = XL_LABEL_POSITION.OUTSIDE_END


def column_chart(slide, x, y, w, h, categories, series, colors, description, vmax=100):
    """Colunas agrupadas, valores em %; rótulo de dado em cada coluna."""
    data = CategoryChartData(number_format='0.0"%"')
    data.categories = categories
    for name, values in series:
        data.add_series(name, values)
    frame = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), data)
    alt(frame, description)
    chart = frame.chart
    style_chart(chart)
    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.BOTTOM
    chart.legend.include_in_layout = False
    plot = chart.plots[0]
    plot.gap_width = 25
    plot.overlap = -5
    plot.has_data_labels = True
    labels = plot.data_labels
    labels.number_format = '0.0"%"'
    labels.number_format_is_linked = False
    labels.position = XL_LABEL_POSITION.OUTSIDE_END
    labels.font.size = Pt(20)
    labels.font.bold = True
    for item, color, (_, values) in zip(plot.series, colors, series):
        item.format.fill.solid()
        item.format.fill.fore_color.rgb = rgb(color)
        label_points(item, values, 18)
    axis = chart.value_axis
    axis.minimum_scale, axis.maximum_scale, axis.major_unit = 0, vmax, 20
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


def bar_chart(slide, x, y, w, h, categories, values, colors, description, vmax=118):
    """Barras horizontais de uma série, primeira categoria no topo; sem eixo de valores (há rótulos).
    O máximo do eixo passa de 100 para sobrar espaço ao rótulo das barras mais longas."""
    data = CategoryChartData(number_format='0.0"%"')
    data.categories = categories
    data.add_series("Acurácia", values)
    frame = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), data)
    alt(frame, description)
    chart = frame.chart
    style_chart(chart)
    chart.has_legend = False
    plot = chart.plots[0]
    plot.gap_width = 45
    plot.vary_by_categories = False
    plot.has_data_labels = True
    labels = plot.data_labels
    labels.number_format = '0.0"%"'
    labels.number_format_is_linked = False
    labels.position = XL_LABEL_POSITION.OUTSIDE_END
    labels.font.size = Pt(20)
    labels.font.bold = True
    series = plot.series[0]
    for index, color in enumerate(colors):
        point = series.points[index]
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = rgb(color)
    label_points(series, values)
    chart.category_axis.reverse_order = True
    chart.category_axis.tick_labels.font.size = Pt(MIN_FONT)
    chart.category_axis.format.line.color.rgb = rgb(GRAY_BAR)
    axis = chart.value_axis
    axis.minimum_scale, axis.maximum_scale = 0, vmax
    axis.has_major_gridlines = False
    axis.visible = False
    return chart


# --- Estrutura comum ---------------------------------------------------------------------------

SLIDE_NUMBER_XML = (
    '<p:sp xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">'
    '<p:nvSpPr><p:cNvPr id="{shape_id}" name="Número do slide"/>'
    '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
    '<p:nvPr><p:ph type="sldNum" sz="quarter" idx="12"/></p:nvPr></p:nvSpPr>'
    '<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm></p:spPr>'
    '<p:txBody><a:bodyPr lIns="0" rIns="0" anchor="ctr"/><a:lstStyle/>'
    '<a:p><a:pPr algn="r"/>'
    '<a:fld id="{{B6F15528-21DE-4FAA-801E-634DDDAF4B2B}}" type="slidenum">'
    '<a:rPr lang="pt-BR" sz="1800" b="1"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill></a:rPr>'
    '<a:t>‹#›</a:t></a:fld>'
    '<a:endParaRPr lang="pt-BR" sz="1800"/></a:p></p:txBody></p:sp>'
)


def add_slide_number(slide):
    """Número do slide como campo do PowerPoint (acompanha a ordem dos slides). Fica à esquerda do
    logo da SBC (x > 12,3) e acima da linha dourada do fundo (y ≈ 7,17)."""
    xml = SLIDE_NUMBER_XML.format(shape_id=slide.shapes._next_shape_id, x=int(Inches(10.9)), y=int(Inches(6.75)),
                                  w=int(Inches(1.2)), h=int(Inches(0.4)), color=MUTED)
    slide.shapes._spTree.append(parse_xml(xml))


def compose_notes(entry, speaker, handoff, closing, markdown=False):
    """Texto das notas de um slide: roteiro (fala), material de estudo e perguntas prováveis.

    O PowerPoint mostra as notas como texto simples, então o formato do .pptx usa rótulos em maiúsculas;
    o notas.md usa títulos e marcadores de Markdown."""
    spoken = f"[{speaker} · {entry['tempo']}] {entry['fala']}"
    extras = []
    if handoff:
        extras.append(f"Passagem para {handoff[0]}: “{handoff[1]}”")
    if closing:
        extras.append(closing)
    if markdown:
        parts = [f"**Roteiro (o que falar)** · {speaker} · {entry['tempo']}\n\n{entry['fala']}"]
        parts += [f"> {line}" for line in extras]
        parts.append("**Para estudar** (apoio; não faz parte da fala)\n\n" + "\n".join(f"- {line}" for line in entry["estudo"]))
        parts.append("**Perguntas prováveis**\n\n" + "\n\n".join(f"- **P:** {q}  \n  **R:** {a}" for q, a in entry["perguntas"]))
        return "\n\n".join(parts)
    parts = ["ROTEIRO (o que falar)\n" + spoken]
    parts += extras
    parts.append("────────────────────\nPARA ESTUDAR (apoio; não faz parte da fala)\n" + "\n".join(f"• {line}" for line in entry["estudo"]))
    parts.append("PERGUNTAS PROVÁVEIS\n" + "\n".join(f"P: {q}\nR: {a}\n" for q, a in entry["perguntas"]).rstrip())
    return "\n\n".join(parts)

class Deck:
    """Deck vazio a partir do template da SBC, com notas do apresentador e roteiro em Markdown.

    `script` é a lista de entradas de notas (uma por slide, na ordem); `blocks` diz o bloco de fala
    de cada slide; `handoff` mapeia a posição do último slide de um bloco para (próximo bloco, frase).
    """

    def __init__(self, script, *, out, notes_md, speakers, blocks, block_titles, handoff, title, author,
                 notes_title):
        self.script = script
        self.out, self.notes_md = out, notes_md
        self.speakers, self.blocks, self.block_titles, self.handoff = speakers, blocks, block_titles, handoff
        self.title, self.author, self.notes_title = title, author, notes_title
        self.prs = Presentation(str(TEMPLATE))
        # O fundo da SBC vem como figura dos slides de exemplo; guarda o de conteúdo e esvazia o deck.
        self.art = self.prs.slides[1].shapes[0].image.blob
        slides = self.prs.slides._sldIdLst
        for slide_id in list(slides):
            self.prs.part.drop_rel(slide_id.rId)
            slides.remove(slide_id)
        self.layouts = {layout.name: layout for layout in self.prs.slide_layouts}
        self.notes = []

    def slide(self, layout, title, title_size=40):
        slide = self.prs.slides.add_slide(self.layouts[layout])
        background = slide.shapes.add_picture(io.BytesIO(self.art), 0, 0, self.prs.slide_width, self.prs.slide_height)
        background.name = "Fundo SBC"
        background._element.nvPicPr.cNvPr.set("descr", "Fundo decorativo do template da SBC")
        tree = slide.shapes._spTree
        tree.remove(background._element)
        tree.insert(2, background._element)  # atrás de tudo
        frame = slide.shapes.title.text_frame
        frame.text = title
        frame.vertical_anchor = MSO_ANCHOR.TOP
        frame.margin_left = 0  # alinha o título com o conteúdo, que começa em x = 0,92
        for run in frame.paragraphs[0].runs:
            run.font.size = Pt(title_size)
            run.font.bold = True  # a fonte leve do tema some no projetor; negrito pesa mais
            run.font.name = "Calibri"
            run.font.language_id = MSO_LANGUAGE_ID.BRAZILIAN_PORTUGUESE
            run.font.color.rgb = rgb(GREEN_DK)
        index = len(self.notes)
        block = self.blocks[index]
        entry = self.script[index]
        handoff = None
        if index in self.handoff:
            to_block, phrase = self.handoff[index]
            handoff = (self.speakers[to_block], phrase)
        closing = f"{self.speakers[block]} conduz as perguntas." if index == len(self.blocks) - 1 else None
        slide.notes_slide.notes_text_frame.text = compose_notes(entry, self.speakers[block], handoff, closing)
        self.notes.append((title, compose_notes(entry, self.speakers[block], handoff, closing, markdown=True)))
        if index > 0:  # o slide de título fica sem número
            add_slide_number(slide)
        return slide

    def save(self):
        self.out.parent.mkdir(parents=True, exist_ok=True)
        properties = self.prs.core_properties
        properties.title = self.title
        properties.author = self.author
        properties.language = "pt-BR"
        self.prs.save(str(self.out))
        lines = [f"# {self.notes_title}\n",
                 "Cada slide traz o roteiro (o que falar), um material de estudo e perguntas prováveis. O estudo e as "
                 "perguntas servem para dominar o assunto e não fazem parte da fala. As mesmas notas estão no .pptx.\n"]
        current = None
        for number, (title, notes) in enumerate(self.notes, 1):
            block = self.blocks[number - 1]
            if block != current:
                current = block
                slides = [n for n, b in enumerate(self.blocks, 1) if b == block]
                lines.append(f"# Bloco {block} · {self.speakers[block]} · slides {slides[0]} a {slides[-1]}: "
                             f"{self.block_titles[block]}\n")
            lines.append(f"## Slide {number}: {title}\n\n{notes}\n")
        self.notes_md.write_text("\n".join(lines), encoding="utf-8")


def audit_fonts(path, minimum=MIN_FONT):
    """Confere que nenhum texto, tabela ou gráfico do arquivo gravado fica abaixo do tamanho mínimo."""
    prs = Presentation(str(path))
    found = []
    for number, slide in enumerate(prs.slides, 1):
        for item in slide.shapes:
            frames = []
            if item.has_text_frame:
                frames.append(item.text_frame)
            if getattr(item, "has_table", False) and item.has_table:
                frames += [cell.text_frame for row in item.table.rows for cell in row.cells]
            for frame in frames:
                for paragraph in frame.paragraphs:
                    for run in paragraph.runs:
                        if run.font.size is not None and run.font.size.pt < minimum:
                            found.append((number, item.name, run.font.size.pt, run.text[:30]))
            if getattr(item, "has_chart", False) and item.has_chart:
                for size in item.chart._chartSpace.xpath(".//@sz"):
                    if int(size) < minimum * 100:
                        found.append((number, item.name, int(size) / 100, "gráfico"))
    return found
