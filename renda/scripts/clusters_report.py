"""Figuras, tabelas e números da quinta parte do relatório (K-means na base de renda).

Lê report/results/clusters_dados.json (gerado por clusters_data.py) e grava:

    report/figures/clusters_peso.pdf          parte de cada atributo na distância média entre duas pessoas
    report/figures/clusters_curvas.pdf        inércia, silhueta e Davies-Bouldin para k de 2 a 10 (10 seeds)
    report/figures/clusters_estabilidade.pdf  ARI entre as seeds, com 10 inicializações e com uma
    report/figures/clusters_renda.pdf         % acima de 50 mil em cada grupo (k = 6, seed 42)
    report/figures/clusters_pca.pdf           os grupos nas duas primeiras componentes principais
    report/figures/clusters_proporcoes.pdf    estado civil, relacionamento e ocupação dentro de cada grupo
    report/figures/clusters_log.pdf           silhueta e menor grupo por k, com e sem log (seed 42)
    report/figures/clusters_silhueta.pdf      silhueta das pessoas em cada grupo (quartis, média, % negativa)
    report/figures/clusters_tempo.pdf         tempo por ajuste e iterações por k
    report/results/tab_clusters_alternativas.tex  perfis com k = 5 e k = 8
    report/results/tab_clusters_log.tex       grupos com e sem log no capital (k = 4, seed 42)
    report/results/tab_clusters_k.tex         métricas internas e estabilidade por k
    report/results/tab_clusters_grupos.tex    perfil dos seis grupos
    report/results/tab_clusters_sensiveis.tex sexo e raça em cada grupo (só no relatório)
    report/results/numeros_clusters.tex       um \\newcommand por número citado no texto (prefixo cl)

Mesmo formato das figuras de svm_report.py (largura útil do template SBC = 15 cm, fonte 8 pt, fundo
branco, sem título dentro da figura, vírgula decimal). As cores dos grupos são as dos slides.

Uso, a partir da raiz do repositório:

    python renda/scripts/clusters_report.py           # PDF
    python renda/scripts/clusters_report.py --png     # também PNG, para conferir a olho
"""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "report" / "results" / "clusters_dados.json"
FIGURES = ROOT / "report" / "figures"
RESULTS = ROOT / "report" / "results"

FULL = 5.9
BLUE, ORANGE = "#2a78d6", "#eb6834"
GRAY, TEXT2, DARK = "#8a8985", "#52514e", "#0f4334"
GROUP_COLOR = {1: "#2a78d6", 2: "#eb6834", 3: "#1baf7a", 4: "#8e5ac8", 5: "#9a7a00", 6: "#b23a2e"}
RC = {
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7, "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#b9b8b2", "axes.labelcolor": TEXT2,
    "xtick.color": TEXT2, "ytick.color": TEXT2, "axes.grid": True, "grid.color": "#e7e6e1", "grid.linewidth": 0.6,
    "legend.frameon": False, "axes.formatter.use_locale": False,
}
KS = [str(k) for k in range(2, 11)]
OCUPACAO = {"Other-service": "outros serviços", "Adm-clerical": "administrativo", "Craft-repair": "ofícios e reparos",
            "Prof-specialty": "especialista", "Exec-managerial": "gerência"}
RACA = [("White", "Branca"), ("Black", "Negra"), ("Asian-Pac-Islander", "Asiática ou do Pacífico"),
        ("Amer-Indian-Eskimo", "Indígena ou esquimó"), ("Other", "Outra")]


def fmt(value, digits=1):
    return f"{value:.{digits}f}".replace(".", ",")


def thousands(value):
    return f"{int(round(value)):,}".replace(",", ".")


def comma_axis(digits=0, suffix=""):
    return FuncFormatter(lambda v, _: fmt(v, digits) + suffix)


# --- Figuras -----------------------------------------------------------------------------------

def fig_peso(d):
    peso = d["base"]["peso"]
    nomes = list(peso)[::-1]
    valores = [peso[n]["parte"] for n in nomes]
    cores = [BLUE if peso[n]["tipo"] == "numérico" else GRAY for n in nomes]
    fig, ax = plt.subplots(figsize=(FULL * 0.62, 2.3))
    ax.barh(nomes, valores, color=cores, height=0.65)
    for i, v in enumerate(valores):
        ax.text(v + 0.3, i, fmt(v) + "%", va="center", fontsize=7, color=TEXT2)
    ax.set_xlim(0, 15.5)
    ax.set_xticks([0, 3, 6, 9, 12, 15])
    ax.xaxis.set_major_formatter(comma_axis(0, "%"))
    ax.set_xlabel("parte da distância média ao quadrado entre duas pessoas")
    ax.grid(axis="y", visible=False)
    ax.text(15.4, 0, "azul: numéricos · cinza: de texto", ha="right", va="center", fontsize=7, color=TEXT2)
    fig.tight_layout()
    return fig


def fig_curvas(d):
    pk = d["por_k"]
    ks = [int(k) for k in KS]
    fig, eixos = plt.subplots(1, 3, figsize=(FULL, 1.9))
    specs = [("inercia", "(a) inércia (mil): cotovelo", 1000, 0), ("silhueta", "(b) silhueta: maior é melhor", 1, 2),
             ("db", "(c) Davies-Bouldin: menor é melhor", 1, 1)]
    for ax, (chave, titulo, div, casas) in zip(eixos, specs):
        media = [pk[k][chave] / div for k in KS]
        desvio = [pk[k][f"{chave}_desvio"] / div for k in KS]
        ax.fill_between(ks, [m - s for m, s in zip(media, desvio)], [m + s for m, s in zip(media, desvio)],
                        color=BLUE, alpha=0.18, linewidth=0)
        ax.plot(ks, media, marker="o", markersize=3, color=BLUE, linewidth=1.3)
        ax.plot([6], [pk["6"][chave] / div], marker="o", markersize=6, markerfacecolor="none",
                markeredgecolor="black", markeredgewidth=0.9)
        ax.set_xticks(ks)
        ax.yaxis.set_major_formatter(comma_axis(casas))
        ax.set_xlabel("k")
        ax.set_title(titulo, loc="left")
    fig.tight_layout()
    return fig


def fig_estabilidade(d):
    pk = d["por_k"]
    ks = [int(k) for k in KS]
    fig, ax = plt.subplots(figsize=(FULL * 0.62, 2.1))
    dez, uma = [pk[k]["ari"] for k in KS], [pk[k]["ari_1"] for k in KS]
    ax.plot(ks, dez, marker="o", markersize=3.5, color=BLUE, linewidth=1.4)
    ax.plot(ks, uma, marker="o", markersize=3.5, color=GRAY, linewidth=1.4)
    ax.text(10.2, dez[-1], "10 inicializações", va="center", fontsize=7, color=BLUE)
    ax.text(10.2, uma[-1], "1 inicialização", va="center", fontsize=7, color=TEXT2)
    ax.axvline(6, color="black", linewidth=0.7, linestyle="--")
    ax.set_xticks(ks)
    ax.set_xlim(1.7, 10.3)
    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_formatter(comma_axis(1))
    ax.set_xlabel("k")
    ax.set_ylabel("ARI médio entre as 10 seeds")
    fig.tight_layout()
    return fig


def fig_renda(d):
    gr, b = d["grupos"], d["base"]
    fig, ax = plt.subplots(figsize=(FULL * 0.75, 2.1))
    rotulos = [f"{g['grupo']}. {g['nome']}" for g in gr][::-1]
    valores = [g["positivos"] for g in gr][::-1]
    ax.barh(rotulos, valores, color=[GROUP_COLOR[g["grupo"]] for g in gr][::-1], height=0.65)
    for i, v in enumerate(valores):
        ax.text(v + 1, i, fmt(v) + "%", va="center", fontsize=7, color="black")
    ax.axvline(b["positivos"], color="black", linewidth=0.8, linestyle="--")
    ax.text(b["positivos"] + 1, len(gr) - 0.45, f"base inteira: {fmt(b['positivos'])}%", fontsize=7)
    ax.set_xlim(0, 75)
    ax.set_ylim(-0.6, len(gr) - 0.1)
    ax.xaxis.set_major_formatter(comma_axis(0, "%"))
    ax.set_xlabel("ganham mais de 50 mil")
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return fig


def fig_pca(d):
    pca, gr = d["pca"], d["grupos"]
    fig, ax = plt.subplots(figsize=(FULL * 0.8, 2.9))
    for g in gr:
        pontos = pca["pontos"][str(g["grupo"])]
        ax.scatter([p[0] for p in pontos], [p[1] for p in pontos], s=3, alpha=0.55, color=GROUP_COLOR[g["grupo"]],
                   linewidths=0, label=f"{g['grupo']}. {g['nome']}")
    for g in gr:
        cx, cy = pca["centros"][str(g["grupo"])]
        ax.scatter([cx], [cy], s=55, marker="D", color=GROUP_COLOR[g["grupo"]], edgecolors="black", linewidths=0.8)
    v1, v2 = pca["variancia"]
    ax.set_xlabel(f"componente 1 ({fmt(v1)}% da variância)")
    ax.set_ylabel(f"componente 2 ({fmt(v2)}% da variância)")
    ax.xaxis.set_major_formatter(comma_axis(0))
    ax.yaxis.set_major_formatter(comma_axis(0))
    ax.legend(markerscale=3.5, loc="center left", bbox_to_anchor=(1.0, 0.5), handletextpad=0.3)
    fig.tight_layout()
    return fig


CATEGORIA = {
    "Married-civ-spouse": "casado(a)", "Never-married": "nunca casou", "Divorced": "divorciado(a)",
    "Widowed": "viúvo(a)", "Separated": "separado(a)",
    "Husband": "marido", "Wife": "esposa", "Not-in-family": "mora sem a família", "Own-child": "filho(a) na casa",
    "Unmarried": "chefe sem cônjuge", "Other-relative": "outro parente",
    "Adm-clerical": "administrativo", "Craft-repair": "ofícios e reparos", "Exec-managerial": "gerência",
    "Machine-op-inspct": "operação de máquinas", "Other-service": "outros serviços", "Prof-specialty": "especialista",
    "Sales": "vendas", "Transport-moving": "transporte", "Handlers-cleaners": "carga e limpeza",
    "outras": "outras",
}


def fig_proporcoes(d):
    """Três mapas de calor: % de cada categoria dentro de cada grupo."""
    blocos = [("marital.status", "(a) estado civil"), ("relationship", "(b) relacionamento"),
              ("occupation", "(c) ocupação")]
    alturas = [len(d["proporcoes"][a]) for a, _ in blocos]
    fig, eixos = plt.subplots(len(blocos), 1, figsize=(FULL * 0.78, 0.2 * sum(alturas) + 1.3),
                              gridspec_kw={"height_ratios": alturas})
    for ax, (atributo, titulo) in zip(eixos, blocos):
        bloco = d["proporcoes"][atributo]
        nomes = list(bloco)
        valores = [bloco[n] for n in nomes]
        ax.imshow(valores, cmap="Greens", vmin=0, vmax=100, aspect="auto")
        for i, linha in enumerate(valores):
            for j, v in enumerate(linha):
                ax.text(j, i, fmt(v, 0), ha="center", va="center", fontsize=6.5, color="white" if v > 55 else "black")
        ax.set_yticks(range(len(nomes)))
        ax.set_yticklabels([CATEGORIA.get(n, n) for n in nomes], fontsize=7)
        ax.set_xticks(range(6))
        ax.set_xticklabels([f"grupo {g}" for g in range(1, 7)] if atributo == "occupation" else [""] * 6, fontsize=7)
        ax.tick_params(length=0)
        ax.grid(False)
        for lado in ax.spines.values():
            lado.set_visible(False)
        ax.set_title(titulo, loc="left")
    fig.tight_layout()
    return fig


def fig_log(d):
    lc = d["log_curvas"]
    ks = [int(k) for k in KS]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(FULL, 1.9))
    for chave, cor, rotulo in [("sem", ORANGE, "sem log"), ("com", BLUE, "com log")]:
        ax1.plot(ks, [lc[chave][k]["silhueta"] for k in KS], marker="o", markersize=3, color=cor, label=rotulo)
        ax2.plot(ks, [lc[chave][k]["menor"] for k in KS], marker="o", markersize=3, color=cor, label=rotulo)
    ax1.set_title("(a) silhueta", loc="left")
    ax1.yaxis.set_major_formatter(comma_axis(2))
    ax2.set_title("(b) tamanho do menor grupo (pessoas)", loc="left")
    ax2.set_yscale("log")
    ax2.set_yticks([100, 300, 1000, 3000])
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda v, _: thousands(v)))
    ax2.yaxis.set_minor_formatter(FuncFormatter(lambda v, _: ""))
    for ax in (ax1, ax2):
        ax.set_xticks(ks)
        ax.set_xlabel("k")
    ax1.legend()
    fig.tight_layout()
    return fig


def fig_silhueta(d):
    sg, gr = d["silhueta_grupos"], d["grupos"]
    fig, ax = plt.subplots(figsize=(FULL * 0.75, 2.1))
    for i, g in enumerate(gr):
        s = sg[str(g["grupo"])]
        cor = GROUP_COLOR[g["grupo"]]
        ax.add_patch(plt.Rectangle((i - 0.28, s["q1"]), 0.56, s["q3"] - s["q1"], color=cor, alpha=0.35, linewidth=0))
        ax.plot([i - 0.28, i + 0.28], [s["mediana"]] * 2, color=cor, linewidth=1.6)
        ax.plot([i], [s["media"]], marker="D", markersize=4, color="black")
        ax.text(i, s["q3"] + 0.03, f"{fmt(s['negativa'], 0)}% < 0", ha="center", fontsize=6.5, color=TEXT2)
    ax.axhline(0, color="black", linewidth=0.7)
    ax.set_xticks(range(len(gr)))
    ax.set_xticklabels([f"{g['grupo']}" for g in gr])
    ax.set_xlim(-0.6, len(gr) - 0.4)
    ax.set_ylim(-0.1, 0.56)
    ax.yaxis.set_major_formatter(comma_axis(1))
    ax.set_xlabel("grupo")
    ax.set_ylabel("silhueta das pessoas")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    return fig


def fig_tempo(d):
    pk = d["por_k"]
    ks = [int(k) for k in KS]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(FULL, 1.8))
    ax1.plot(ks, [pk[k]["tempo_s"] for k in KS], marker="o", markersize=3, color=BLUE, label="10 inicializações")
    ax1.plot(ks, [pk[k]["tempo_1_s"] for k in KS], marker="o", markersize=3, color=GRAY, label="1 inicialização")
    ax1.set_title("(a) tempo por ajuste (s, mediana das seeds)", loc="left")
    ax1.yaxis.set_major_formatter(comma_axis(1))
    ax1.legend()
    ax2.plot(ks, [pk[k]["iteracoes"] for k in KS], marker="o", markersize=3, color=BLUE)
    ax2.set_title("(b) iterações até parar (média, 10 inicializações)", loc="left")
    for ax in (ax1, ax2):
        ax.set_xticks(ks)
        ax.set_xlabel("k")
    fig.tight_layout()
    return fig


# --- Tabelas -----------------------------------------------------------------------------------

def tabela_alternativas(d):
    linhas = [r"\setlength{\tabcolsep}{3pt}", r"\begin{tabular}{clrrrrrlr}", r"\toprule",
              r"k & Grupo & Pessoas & Idade & \shortstack{Anos de\\estudo} & \shortstack{Horas por\\semana} & "
              r"\shortstack{Casados\\(\%)} & Ocupação mais comum & \shortstack{$>$50K\\(\%)} \\", r"\midrule"]
    for k in ("5", "8"):
        for i, g in enumerate(d["alternativas"][k]):
            capital = (" (todos com ganho)" if g["com_ganho"] > 99 else " (todos com perda)" if g["com_perda"] > 99 else "")
            linhas.append(f"{k if i == 0 else ''} & {g['grupo']}{capital} & {thousands(g['pessoas'])} & {fmt(g['idade'])} & "
                          f"{fmt(g['estudo'])} & {fmt(g['horas'])} & {fmt(g['casados'], 0)} & "
                          f"{CATEGORIA.get(g['ocupacao'], g['ocupacao'])} & {fmt(g['positivos'])} \\\\")
        if k == "5":
            linhas.append(r"\midrule")
    linhas += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(linhas) + "\n"


def tabela_log(d):
    lg = d["log"]
    linhas = [r"\begin{tabular}{lrrrr}", r"\toprule",
              r"Grupo (k = 4, seed 42) & Pessoas & Com ganho (\%) & Com perda (\%) & $>$50K (\%) \\", r"\midrule"]
    for chave, titulo in [("sem", "Sem log"), ("com", "Com log")]:
        linhas.append(f"\\multicolumn{{5}}{{l}}{{\\emph{{{titulo}}}}} \\\\")
        for i, g in enumerate(lg[chave]["grupos"], 1):
            linhas.append(f"{i}º maior & {thousands(g['pessoas'])} & {fmt(g['com_ganho'])} & {fmt(g['com_perda'])} & "
                          f"{fmt(g['positivos'])} \\\\")
        if chave == "sem":
            linhas.append(r"\midrule")
    linhas += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(linhas) + "\n"


def tabela_k(d):
    pk = d["por_k"]
    linhas = [r"\begin{tabular}{crrrrr}", r"\toprule",
              r"k & Inércia & Silhueta & Davies-Bouldin & ARI (10 inic.) & ARI (1 inic.) \\", r"\midrule"]
    for k in KS:
        info = pk[k]
        linha = (f"{k} & {thousands(info['inercia'])} & {fmt(info['silhueta'], 3)} & {fmt(info['db'], 2)} & "
                 f"{fmt(info['ari'], 3)} & {fmt(info['ari_1'], 3)} \\\\")
        linhas.append(r"\textbf{6} & " + linha.split(" & ", 1)[1] if k == "6" else linha)
    linhas += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(linhas) + "\n"


def tabela_grupos(d):
    comp = d["composicao"]
    linhas = [r"\setlength{\tabcolsep}{3pt}", r"\begin{tabular}{lrrrrrlr}", r"\toprule",
              r"Grupo & Pessoas & Idade & \shortstack{Anos de\\estudo} & \shortstack{Horas por\\semana} & "
              r"\shortstack{Casados\\(\%)} & Ocupação mais comum & \shortstack{$>$50K\\(\%)} \\", r"\midrule"]
    for g in d["grupos"]:
        c = comp[str(g["grupo"])]
        ocupacao = f"{OCUPACAO.get(c['ocupacao'], c['ocupacao'])} ({fmt(c['ocupacao_parte'], 0)}\\%)"
        linhas.append(f"{g['grupo']}. {g['nome']} & {thousands(g['pessoas'])} & {fmt(g['idade'])} & {fmt(g['estudo'])} & "
                      f"{fmt(g['horas'])} & {fmt(c['casados'], 0)} & {ocupacao} & {fmt(g['positivos'])} \\\\")
    c = comp["base"]
    b = d["base"]
    media = c
    linhas += [r"\midrule",
               f"Base inteira & {thousands(b['linhas'])} & {fmt(media['idade'])} & {fmt(media['estudo'])} & "
               f"{fmt(media['horas'])} & {fmt(c['casados'], 0)} & {OCUPACAO[c['ocupacao']]} "
               f"({fmt(c['ocupacao_parte'], 0)}\\%) & {fmt(b['positivos'])} \\\\",
               r"\bottomrule", r"\end{tabular}"]
    return "\n".join(linhas) + "\n"


def tabela_sensiveis(d):
    comp = d["composicao"]
    cols = [str(g) for g in range(1, 7)] + ["base"]
    linhas = [r"\begin{tabular}{lrrrrrrr}", r"\toprule",
              r"(\%) & Grupo 1 & Grupo 2 & Grupo 3 & Grupo 4 & Grupo 5 & Grupo 6 & Base \\", r"\midrule",
              "Mulheres & " + " & ".join(fmt(comp[c]["mulheres"]) for c in cols) + r" \\", r"\midrule",
              r"\multicolumn{8}{l}{\emph{Raça}} \\"]
    for chave, rotulo in RACA:
        linhas.append(f"{rotulo} & " + " & ".join(fmt(comp[c]["raca"].get(chave, 0)) for c in cols) + r" \\")
    linhas += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(linhas) + "\n"


# --- Números citados no texto ------------------------------------------------------------------

def numeros(d):
    b, lg, pk, e, ref, comp = d["base"], d["log"], d["por_k"], d["escolha"], d["referencia"], d["composicao"]
    g = {item["grupo"]: item for item in d["grupos"]}
    sem, com = lg["sem"]["grupos"], lg["com"]["grupos"]
    q = d["quedas_inercia"]
    n = {
        "clLinhas": thousands(b["linhas"]), "clColunas": b["colunas"], "clPositivos": fmt(b["positivos"]),
        "clComGanho": fmt(b["com_ganho"]), "clComPerda": fmt(b["com_perda"]), "clComCapital": fmt(b["com_capital"], 0),
        "clTeto": b["ganho_teto"], "clTrocaAnos": fmt(b["troca_em_anos"]), "clDesvioIdade": fmt(b["desvio_idade"]),
        "clParteTexto": fmt(b["parte_categoricos"]), "clParteNum": fmt(100 - b["parte_categoricos"]),
        "clPartePais": fmt(b["peso"]["país de origem"]["parte"]), "clParteOcup": fmt(b["peso"]["ocupação"]["parte"]),
        "clParteUmNum": fmt(b["peso"]["idade"]["parte"]),
        "clSemLogMax": fmt(lg["sem"]["ganho_max_desvios"]), "clComLogMax": fmt(lg["com"]["ganho_max_desvios"]),
        "clComLogZero": fmt(lg["com"]["ganho_zero_desvios"], 2).replace("-", "$-$"),
        "clSemLogTetoGrupo": sem[3]["pessoas"], "clSemLogPerda": thousands(sem[2]["pessoas"]),
        "clComLogGanho": thousands(com[2]["pessoas"]), "clComLogPerda": thousands(com[3]["pessoas"]),
        "clComLogGanhoPos": fmt(com[2]["positivos"]), "clComLogPerdaPos": fmt(com[3]["positivos"]),
        "clQuedaDoisTres": thousands(q["2-3"]), "clQuedaQuatroCinco": thousands(q["4-5"]),
        "clQuedaCincoSeis": thousands(q["5-6"]), "clQuedaSeisSete": thousands(q["6-7"]),
        "clSilDois": fmt(pk["2"]["silhueta"], 2), "clSilSeis": fmt(pk["6"]["silhueta"], 2),
        "clDbDois": fmt(pk["2"]["db"], 2), "clDbSeis": fmt(pk["6"]["db"], 2),
        "clAriDoisMin": fmt(pk["2"]["ari_min"], 2).replace("-", "$-$"),
        "clAriTres": fmt(pk["3"]["ari"], 2), "clAriCinco": fmt(pk["5"]["ari"], 3), "clAriSeis": fmt(pk["6"]["ari"], 3),
        "clAriOito": fmt(pk["8"]["ari"], 3), "clAriNove": fmt(pk["9"]["ari"], 2),
        "clAriSeisUm": fmt(pk["6"]["ari_1"], 2), "clPioraSeisUm": fmt(pk["6"]["inercia_piora_1"], 0),
        "clPioraMin": fmt(min(v["inercia_piora_1"] for v in pk.values()), 0),
        "clPioraMax": fmt(max(v["inercia_piora_1"] for v in pk.values()), 0),
        "clTempoSeis": fmt(pk["6"]["tempo_s"], 2), "clTempoSeisUm": fmt(pk["6"]["tempo_1_s"], 2),
        "clTempoDois": fmt(pk["2"]["tempo_s"], 2), "clAjustes": d["estudo_total_ajustes"],
        "clPureza": fmt(e["pureza"]), "clChute": fmt(e["chute"]), "clPurezaGanho": fmt(e["pureza"] - e["chute"]),
        "clAriRenda": fmt(e["ari_renda"], 2), "clSvmAcc": fmt(ref["svm_rbf_acuracia"]),
        "clVarUm": fmt(d["pca"]["variancia"][0]), "clVarDois": fmt(d["pca"]["variancia"][1]),
        "clVarTotal": fmt(sum(d["pca"]["variancia"]), 0),
        "clMulheresBase": fmt(comp["base"]["mulheres"]), "clMulheresTres": fmt(comp["3"]["mulheres"]),
        "clMulheresUm": fmt(comp["1"]["mulheres"]), "clMulheresDois": fmt(comp["2"]["mulheres"]),
        "clNegrosBase": fmt(comp["base"]["raca"]["Black"]), "clNegrosUm": fmt(comp["1"]["raca"]["Black"]),
        "clNegrosDois": fmt(comp["2"]["raca"]["Black"]),
        "clLinhasEn": f"{b['linhas']:,}", "clPurezaEn": f"{e['pureza']:.1f}", "clChuteEn": f"{e['chute']:.1f}",
        "clSvmAccEn": f"{ref['svm_rbf_acuracia']:.1f}", "clAriSeisEn": f"{pk['6']['ari']:.3f}",
        "clSilSeisEn": f"{pk['6']['silhueta']:.2f}",
    }
    lc, sg, pr = d["log_curvas"], d["silhueta_grupos"], d["proporcoes"]
    n.update({
        "clSemLogSilDois": fmt(lc["sem"]["2"]["silhueta"], 2), "clSemLogSilSeis": fmt(lc["sem"]["6"]["silhueta"], 3),
        "clComLogSilSeis": fmt(lc["com"]["6"]["silhueta"], 3), "clSemLogMenorDois": thousands(lc["sem"]["2"]["menor"]),
        "clSemLogMenor": lc["sem"]["6"]["menor"], "clComLogMenor": thousands(lc["com"]["6"]["menor"]),
        "clComLogMenorDois": thousands(lc["com"]["2"]["menor"]),
        "clTempoMax": fmt(max(v["tempo_s"] for v in pk.values()), 1),
        "clIterDois": fmt(pk["2"]["iteracoes"], 0), "clIterDez": fmt(pk["10"]["iteracoes"], 0),
        "clIterSeis": fmt(pk["6"]["iteracoes"], 0),
        "clCasadosTres": fmt(pr["marital.status"]["Married-civ-spouse"][2], 0),
        "clMaridoTres": fmt(pr["relationship"]["Husband"][2], 0),
        "clNuncaUm": fmt(pr["marital.status"]["Never-married"][0], 0),
        "clFilhoUm": fmt(pr["relationship"]["Own-child"][0], 0),
        "clDivorcDois": fmt(pr["marital.status"]["Divorced"][1], 0),
        "clViuvoDois": fmt(pr["marital.status"]["Widowed"][1], 0),
        "clChefeDois": fmt(pr["relationship"]["Unmarried"][1], 0),
        "clEspecQuatro": fmt(pr["occupation"]["Prof-specialty"][3], 0),
        "clGerenQuatro": fmt(pr["occupation"]["Exec-managerial"][3], 0),
    })
    for i, palavra in enumerate(["Um", "Dois", "Tres", "Quatro", "Cinco", "Seis"], 1):
        n[f"clSilG{palavra}"] = fmt(sg[str(i)]["media"], 2)  # silhueta média do grupo i (k = 6)
        n[f"clSilNegG{palavra}"] = fmt(sg[str(i)]["negativa"], 0)
    for i, palavra in enumerate(["Um", "Dois", "Tres", "Quatro", "Cinco", "Seis"], 1):
        n[f"clPos{palavra}"] = fmt(g[i]["positivos"])
        n[f"clPessoas{palavra}"] = thousands(g[i]["pessoas"])
        n[f"clPos{palavra}En"] = f"{g[i]['positivos']:.1f}"
    linhas = ["% Gerado por scripts/clusters_report.py a partir de report/results/clusters_dados.json; não editar."]
    linhas += [f"\\newcommand{{\\{chave}}}{{{valor}}}" for chave, valor in n.items()]
    return "\n".join(linhas) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--png", action="store_true", help="grava também PNG, para conferir")
    args = parser.parse_args()
    d = json.loads(DATA.read_text(encoding="utf-8"))
    plt.rcParams.update(RC)
    FIGURES.mkdir(parents=True, exist_ok=True)
    for nome, fazer in [("clusters_peso", fig_peso), ("clusters_curvas", fig_curvas),
                        ("clusters_estabilidade", fig_estabilidade), ("clusters_renda", fig_renda),
                        ("clusters_pca", fig_pca), ("clusters_proporcoes", fig_proporcoes), ("clusters_log", fig_log),
                        ("clusters_silhueta", fig_silhueta), ("clusters_tempo", fig_tempo)]:
        fig = fazer(d)
        fig.savefig(FIGURES / f"{nome}.pdf", bbox_inches="tight")
        if args.png:
            fig.savefig(FIGURES / f"{nome}.png", dpi=200, bbox_inches="tight")
        plt.close(fig)
    (RESULTS / "tab_clusters_log.tex").write_text(tabela_log(d), encoding="utf-8")
    (RESULTS / "tab_clusters_k.tex").write_text(tabela_k(d), encoding="utf-8")
    (RESULTS / "tab_clusters_grupos.tex").write_text(tabela_grupos(d), encoding="utf-8")
    (RESULTS / "tab_clusters_sensiveis.tex").write_text(tabela_sensiveis(d), encoding="utf-8")
    (RESULTS / "tab_clusters_alternativas.tex").write_text(tabela_alternativas(d), encoding="utf-8")
    (RESULTS / "numeros_clusters.tex").write_text(numeros(d), encoding="utf-8")
    print("gravado:", FIGURES, RESULTS)


if __name__ == "__main__":
    main()
