"""Figuras, tabelas e números da quarta parte do relatório (SVM na base de renda).

Lê report/results/svm_dados.json (gerado por svm_data.py) e grava:

    report/figures/svm_eda.pdf             renda alta por estado civil e por anos de estudo
    report/figures/svm_mapa.pdf            acurácia de validação no mapa C × gamma (seed 0)
    report/figures/svm_gamma.pdf           treino contra validação por gamma, com C = 1 (sobreajuste)
    report/figures/svm_tempo.pdf           tempo de treino por tamanho do treino, escala log
    report/figures/svm_acc_auc.pdf         acurácia e AUC dos modelos nas 10 seeds
    report/results/tab_svm_modelos.tex     os dez modelos nas 10 seeds, com erros e tempos
    report/results/tab_svm_seed0.tex       kernels com C = 1 e efeito da padronização (seed 0)
    report/results/tab_svm_grades.tex      grades de busca e o que a busca escolheu
    report/results/numeros_svm.tex         um \\newcommand por número citado no texto

Mesmo formato das figuras de emprestimos/scripts/rn_report.py (largura útil do template SBC = 15 cm,
fonte 8 pt, fundo branco, sem título dentro da figura, vírgula decimal).

Uso, a partir da raiz do repositório:

    python renda/scripts/svm_report.py           # PDF
    python renda/scripts/svm_report.py --png     # também PNG, para conferir a olho
"""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import FuncFormatter, PercentFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "report" / "results" / "svm_dados.json"
FIGURES = ROOT / "report" / "figures"
RESULTS = ROOT / "report" / "results"

FULL, HALF = 5.9, 2.85
BLUE, ORANGE, GREEN, RED = "#2a78d6", "#eb6834", "#1baf7a", "#e34948"
GRAY, TEXT2, DARK = "#8a8985", "#52514e", "#0f4334"
RC = {
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7, "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#b9b8b2", "axes.labelcolor": TEXT2,
    "xtick.color": TEXT2, "ytick.color": TEXT2, "axes.grid": True, "grid.color": "#e7e6e1", "grid.linewidth": 0.6,
    "legend.frameon": False, "axes.formatter.use_locale": False,
}
#: Nome no CSV -> nome no relatório, na ordem das tabelas.
ROTULO = {"classe majoritária": "Classe majoritária", "regra de um corte": "Regra de um corte",
          "regressão logística": "Regressão logística", "árvore de decisão": "Árvore de decisão",
          "random forest": "Random Forest", "SVM linear": "SVM linear", "SVM RBF": "SVM RBF",
          "SVM polinomial": "SVM polinomial", "SVM RBF com pesos": "SVM RBF com pesos",
          "rede neural": "Rede neural (MLP)"}
#: Nome no CSV -> pedaço do nome das macros.
CHAVE = {"classe majoritária": "Maj", "regra de um corte": "Regra", "regressão logística": "Log",
         "árvore de decisão": "Arv", "random forest": "RF", "SVM linear": "Lin", "SVM RBF": "RBF",
         "SVM polinomial": "Poli", "SVM RBF com pesos": "Pesos", "rede neural": "Rede"}


def fmt(value, digits=1):
    return f"{value:.{digits}f}".replace(".", ",")


def signed(value, digits=1):
    """Diferença com sinal para o LaTeX: +0,6 ou $-$0,2."""
    return ("+" + fmt(value, digits)) if value >= 0 else "$-$" + fmt(-value, digits)


def thousands(value):
    return f"{int(value):,}".replace(",", ".")


def comma_axis(digits=0, suffix=""):
    return FuncFormatter(lambda v, _: fmt(v, digits) + suffix)


# --- Figuras -----------------------------------------------------------------------------------

def fig_eda(d):
    b = d["base"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(FULL, 2.1), gridspec_kw={"width_ratios": [1, 1.5]})
    ec = b["estado_civil"]
    ax1.barh(list(ec)[::-1], list(ec.values())[::-1], color=[BLUE if k == "casado(a)" else GRAY for k in list(ec)[::-1]])
    for i, v in enumerate(list(ec.values())[::-1]):
        ax1.text(v + 1, i, fmt(v) + "%", va="center", fontsize=7, color=TEXT2)
    ax1.set_xlim(0, 60)
    ax1.xaxis.set_major_formatter(comma_axis(0, "%"))
    ax1.set_xlabel("ganham mais de 50 mil")
    ax1.grid(axis="y", visible=False)
    ax1.set_title("(a) por estado civil", loc="left")
    anos = [int(k) for k in b["por_anos_de_estudo"]]
    taxa = list(b["por_anos_de_estudo"].values())
    ax2.bar(anos, taxa, color=GRAY, width=0.75)
    ax2.axhline(b["positivos"], color="black", linewidth=0.8, linestyle="--")
    ax2.text(1, b["positivos"] + 2, f"média: {fmt(b['positivos'])}%", fontsize=7, color="black")
    ax2.set_xticks(anos)
    ax2.yaxis.set_major_formatter(comma_axis(0, "%"))
    ax2.set_ylim(0, 85)
    ax2.set_xlabel("anos de estudo")
    ax2.grid(axis="x", visible=False)
    ax2.set_title("(b) por anos de estudo", loc="left")
    fig.tight_layout()
    return fig


def fig_mapa(d):
    m = d["mapa"]
    acc = np.array(m["acuracia"])
    fig, ax = plt.subplots(figsize=(HALF + 0.6, 2.3))
    image = ax.imshow(acc, cmap="Greens", vmin=75, vmax=m["melhor"]["acuracia"], aspect="auto")
    for i in range(acc.shape[0]):
        for j in range(acc.shape[1]):
            ax.text(j, i, fmt(acc[i, j]), ha="center", va="center", fontsize=6.5,
                    color="white" if acc[i, j] > 83.5 else "black")
    bi, bj = m["C"].index(m["melhor"]["C"]), m["gamma"].index(m["melhor"]["gamma"])
    ax.add_patch(plt.Rectangle((bj - 0.5, bi - 0.5), 1, 1, fill=False, edgecolor=ORANGE, linewidth=1.6))
    ax.set_xticks(range(len(m["gamma"])), [fmt(g, 3).rstrip("0").rstrip(",") for g in m["gamma"]])
    ax.set_yticks(range(len(m["C"])), [fmt(c, 2).rstrip("0").rstrip(",") for c in m["C"]])
    ax.set_xlabel("gamma")
    ax.set_ylabel("C")
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    bar = fig.colorbar(image, ax=ax, fraction=0.05, pad=0.03)
    bar.ax.yaxis.set_major_formatter(comma_axis(0, "%"))
    bar.ax.tick_params(labelsize=7)
    bar.outline.set_visible(False)
    fig.tight_layout()
    return fig


def fig_gamma(d):
    m = d["mapa"]
    i = m["C"].index(1.0)
    gammas = m["gamma"]
    fig, ax = plt.subplots(figsize=(HALF, 2.0))
    ax.plot(gammas, m["treino"][i], marker="o", markersize=3.5, color=GRAY, label="treino")
    ax.plot(gammas, m["acuracia"][i], marker="o", markersize=3.5, color=BLUE, label="validação")
    ax.set_xscale("log")
    ax.set_xticks(gammas, [fmt(g, 3).rstrip("0").rstrip(",") for g in gammas], rotation=45)
    ax.minorticks_off()
    ax.yaxis.set_major_formatter(comma_axis(0, "%"))
    ax.set_xlabel("gamma (escala log), C = 1")
    ax.set_ylabel("acurácia")
    ax.legend(loc="upper left")
    fig.tight_layout()
    return fig


def fig_tempo(d):
    t = d["tempo_por_tamanho"]
    estilo = {"SVC RBF": (RED, "SVC RBF"), "SVC linear": (ORANGE, "SVC linear"), "LinearSVC": (GREEN, "LinearSVC"),
              "random forest": (GRAY, "Random Forest"), "árvore de decisão": ("#b9b8b2", "Árvore"),
              "regressão logística": (BLUE, "Regressão logística")}
    fig, ax = plt.subplots(figsize=(FULL * 0.78, 2.3))
    for nome, (cor, rotulo) in estilo.items():
        info = t[nome]
        ax.plot(info["n"], info["tempo_s"], marker="o", markersize=3, color=cor,
                label=f"{rotulo} ({fmt(info['inclinacao'], 2)})")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: thousands(v)))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: fmt(v, 3).rstrip("0").rstrip(",")))
    ax.set_xlabel("pessoas no treino (escala log)")
    ax.set_ylabel("tempo de treino (s, escala log)")
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=6.8, title="modelo (inclinação)",
              title_fontsize=6.8, alignment="left")
    fig.tight_layout()
    return fig


def fig_acc_auc(d):
    m = d["modelos"]
    nomes = ["regressão logística", "árvore de decisão", "random forest", "SVM linear", "SVM RBF", "SVM polinomial",
             "SVM RBF com pesos", "rede neural"]
    rotulos = [ROTULO[n] for n in nomes]
    cores = [DARK if n.startswith("SVM") else BLUE if n == "rede neural" else GRAY for n in nomes]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(FULL, 2.4), sharey=True)
    y = np.arange(len(nomes))[::-1]
    for ax, chave, desvio, lim, titulo in [(ax1, "acuracia", "desvio", (80, 87), "(a) acurácia"),
                                           (ax2, "auc", "desvio_auc", (85, 92), "(b) AUC")]:
        valores = [m[n][chave] for n in nomes]
        erros = [m[n][desvio] for n in nomes]
        ax.barh(y, valores, xerr=erros, color=cores, height=0.65, error_kw={"elinewidth": 0.8, "capsize": 2})
        for yi, v, e in zip(y, valores, erros):
            ax.text(v + e + 0.15, yi, fmt(v), va="center", fontsize=6.8, color=TEXT2)
        ax.set_xlim(*lim)
        ax.xaxis.set_major_formatter(comma_axis(0, "%"))
        ax.grid(axis="y", visible=False)
        ax.set_title(titulo, loc="left")
    ax1.set_yticks(y, rotulos)
    fig.tight_layout()
    return fig


# --- Tabelas -----------------------------------------------------------------------------------

def tabela_modelos(d):
    m = d["modelos"]
    linhas = [r"\setlength{\tabcolsep}{3.5pt}", r"\begin{tabular}{lcccccccc}", r"\toprule",
              r"Modelo & Acurácia (\%) & \shortstack{F1 macro\\(\%)} & \shortstack{F1 $>$50K\\(\%)} & AUC (\%) & FP & FN "
              r"& \shortstack{Treino\\(s)} & \shortstack{Previsão\\(ms)} \\", r"\midrule"]
    for nome, rotulo in ROTULO.items():
        info = m[nome]
        treino = fmt(info["treino_s"], 2 if info["treino_s"] < 1 else 1)
        prev = fmt(info["previsao_ms"], 0 if info["previsao_ms"] >= 100 else 1)
        linha = (f"{rotulo} & {fmt(info['acuracia'])} $\\pm$ {fmt(info['desvio'])} & {fmt(info['f1'])} & "
                 f"{fmt(info['f1_pos'])} & {fmt(info['auc'])} & {thousands(round(info['fp']))} & "
                 f"{thousands(round(info['fn']))} & {treino} & {prev} \\\\")
        if nome == "SVM linear":
            linhas.append(r"\midrule")
        linhas.append(linha)
    linhas += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(linhas) + "\n"


def tabela_seed0(d):
    k, pad = d["seed0"]["kernels"], d["seed0"]["padronizacao"]
    linhas = [r"\begin{tabular}{lccc}", r"\toprule", r"Modelo (seed 0) & Acurácia (\%) & AUC (\%) & Treino (s) \\",
              r"\midrule", r"\multicolumn{4}{l}{\emph{Kernels, com C = 1}} \\"]
    for nome, rotulo in [("LinearSVC", "SVM linear (LinearSVC)"), ("SVC linear", "SVC, kernel linear"),
                         ("SVC polinomial grau 2", "SVC polinomial, grau 2"),
                         ("SVC polinomial grau 3", "SVC polinomial, grau 3"), ("SVC RBF", "SVC RBF")]:
        info = k[nome]
        linhas.append(f"{rotulo} & {fmt(info['acuracia'])} & {fmt(info['auc'])} & {fmt(info['treino_s'], 2)} \\\\")
    melhor = d["mapa"]["melhor"]
    linhas.append(r"\midrule")
    linhas.append(f"\\multicolumn{{4}}{{l}}{{\\emph{{Padronização (RBF com C = {fmt(melhor['C'], 0)} e "
                  f"$\\gamma$ = {fmt(melhor['gamma'])}; LinearSVC com C = 1)}}}} \\\\")
    for nome, rotulo in [("RBF com", "RBF, com padronização"), ("RBF sem", "RBF, sem padronização"),
                         ("LinearSVC com", "LinearSVC, com padronização"),
                         ("LinearSVC sem", "LinearSVC, sem padronização")]:
        info = pad[nome]
        linhas.append(f"{rotulo} & {fmt(info['acuracia'])} & {fmt(info['auc'])} & {fmt(info['treino_s'], 2)} \\\\")
    linhas += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(linhas) + "\n"


def escolhas(d):
    e = d["escolhas"]
    top = {nome: (json.loads(t), n) for nome in ["SVM linear", "SVM polinomial"] for t, n in [next(iter(e[nome].items()))]}
    rbf = [(json.loads(t), n) for t, n in e["SVM RBF"].items()]
    return top, rbf


def tabela_grades(d):
    e = d["escolhas"]
    top, rbf = escolhas(d)
    lin, n_lin = top["SVM linear"]
    poly, n_poly = top["SVM polinomial"]
    c1 = sum(n for p, n in rbf if p["C"] == 1)
    gammas = " ou ".join(f"{fmt(p['gamma'])} ({n})" for p, n in rbf if p["C"] == 1)
    arv = e["árvore de decisão"]
    linhas = [r"\begin{tabular}{l>{\raggedright\arraybackslash}p{5.6cm}>{\raggedright\arraybackslash}p{4.2cm}}", r"\toprule", r"Modelo & Valores testados & Escolha nas 10 seeds \\",
              r"\midrule",
              f"Árvore de decisão & critério (Gini, entropia) $\\times$ profundidade (3, 5, 8, 12, sem limite) $\\times$ "
              f"mínimo por folha (1, 5, 20): 30 & {arv['combinacoes']} combinações diferentes; profundidade de "
              f"{arv['profundidade_min']} para cima ou sem limite \\\\",
              f"SVM linear & C $\\in$ \\{{0,001; 0,01; 0,1; 1; 10\\}}: 5 & C = {fmt(lin['C'])} em {n_lin} \\\\",
              f"SVM RBF & C $\\in$ \\{{0,1; 1; 10; 100\\}} $\\times$ $\\gamma$ $\\in$ \\{{0,01; 0,03; 0,1; 0,3\\}}: 16 & "
              f"C = 1 em {c1}, com $\\gamma$ = {gammas}; C = 10 e $\\gamma$ = 0,03 em 1 \\\\",
              f"SVM polinomial & grau $\\in$ \\{{2; 3\\}} $\\times$ C $\\in$ \\{{0,1; 1; 10\\}}, coef0 = 1: 6 & "
              f"grau {poly['degree']} e C = {fmt(poly['C'], 0)} em {n_poly} \\\\",
              f"Rede neural & 6 arquiteturas $\\times$ $\\alpha$ (10$^{{-4}}$, 10$^{{-2}}$) $\\times$ taxa (10$^{{-3}}$, "
              f"10$^{{-2}}$): 24 & {len(e['rede neural'])} combinações diferentes \\\\",
              r"\bottomrule", r"\end{tabular}"]
    return "\n".join(linhas) + "\n"


# --- Números -----------------------------------------------------------------------------------

def numeros(d):
    b, m, c, mapa, s0 = d["base"], d["modelos"], d["comparacoes"], d["mapa"], d["seed0"]
    k, pad, t, g = s0["kernels"], s0["padronizacao"], d["tempo_por_tamanho"], d["gamma_rbf"]
    top, rbf = escolhas(d)
    n = {
        "svLinhasBrutas": thousands(b["brutas"]), "svPositivosBrutos": fmt(b["positivos_brutos"]),
        "svDuplicadas": b["duplicadas"], "svAusentes": thousands(b["com_ausente"]),
        "svPositivosAusentes": fmt(b["positivos_com_ausente"]), "svLinhas": thousands(b["linhas"]),
        "svLinhasEn": f"{b['linhas']:,}", "svPositivos": fmt(b["positivos"]), "svNPositivos": thousands(b["n_positivos"]),
        "svPiso": fmt(b["piso"]), "svPisoEn": f"{b['piso']:.1f}", "svRazaoClasses": fmt((100 - b["positivos"]) / b["positivos"]),
        "svColunas": b["colunas_modelo"], "svCorrFnlwgt": signed(b["correlacao_fnlwgt"], 3).lstrip("+"),
        "svPerfisConflito": b["perfis_conflito"], "svLinhasConflito": thousands(b["linhas_conflito"]),
        "svPctConflito": fmt(100 * b["linhas_conflito"] / b["linhas"], 0), "svErrosIrred": b["erros_irredutiveis"],
        "svIrredPct": fmt(100 - b["teto"]), "svTeto": fmt(b["teto"]), "svTetoEn": f"{b['teto']:.1f}",
        "svRepetemPerfil": thousands(b["repetem_perfil"]),
        "svCasados": fmt(b["estado_civil"]["casado(a)"]), "svNuncaCasou": fmt(b["estado_civil"]["nunca casou"]),
        "svEstudoNove": fmt(b["por_anos_de_estudo"]["9"]), "svEstudoTreze": fmt(b["por_anos_de_estudo"]["13"]),
        "svEstudoQuinze": fmt(b["por_anos_de_estudo"]["15"]),
        "svCorrEstudo": fmt(b["correlacao_alvo"]["education.num"], 2), "svCorrIdade": fmt(b["correlacao_alvo"]["age"], 2),
        "svCorrHoras": fmt(b["correlacao_alvo"]["hours.per.week"], 2),
        "svCorrGanho": fmt(b["correlacao_alvo"]["capital.gain"], 2),
        "svCorrPerda": fmt(b["correlacao_alvo"]["capital.loss"], 2),
        "svGanhoMax": thousands(b["faixas"]["capital.gain"][1]),
        "svTreino": thousands(s0["treino"]), "svTeste": thousands(s0["teste"]),
        "svPositivosTeste": thousands(s0["positivos_teste"]),
        "svMargem": fmt(s0["margem"]["dentro_da_margem"]), "svVetNeg": thousands(s0["margem"]["vetores_por_classe"][0]),
        "svVetPos": thousands(s0["margem"]["vetores_por_classe"][1]),
        "svKLinSVC": fmt(k["LinearSVC"]["acuracia"]), "svKSVCLin": fmt(k["SVC linear"]["acuracia"]),
        "svKPoliDois": fmt(k["SVC polinomial grau 2"]["acuracia"]), "svKPoliTres": fmt(k["SVC polinomial grau 3"]["acuracia"]),
        "svKRBF": fmt(k["SVC RBF"]["acuracia"]), "svKAucLinSVC": fmt(k["LinearSVC"]["auc"]), "svKAucRBF": fmt(k["SVC RBF"]["auc"]),
        "svRazaoLinear": fmt(k["SVC linear"]["treino_s"] / k["LinearSVC"]["treino_s"], 0),
        "svPadCom": fmt(pad["RBF com"]["acuracia"]), "svPadSem": fmt(pad["RBF sem"]["acuracia"]),
        "svPadFCom": fmt(pad["RBF com"]["f1_pos"]), "svPadFSem": fmt(pad["RBF sem"]["f1_pos"]),
        "svPadVetSem": thousands(pad["RBF sem"]["vetores"]),
        "svPadVetSemPct": fmt(100 * pad["RBF sem"]["vetores"] / s0["treino"], 0),
        "svPadTempoSem": fmt(pad["RBF sem"]["treino_s"], 0), "svPadTempoCom": fmt(pad["RBF com"]["treino_s"], 1),
        "svLinPadCom": fmt(pad["LinearSVC com"]["acuracia"]), "svLinPadSem": fmt(pad["LinearSVC sem"]["acuracia"]),
        "svMapaMelhor": fmt(mapa["melhor"]["acuracia"], 2), "svMapaMelhorC": fmt(mapa["melhor"]["C"], 0),
        "svMapaMelhorG": fmt(mapa["melhor"]["gamma"]), "svMapaPerto": mapa["perto_do_melhor"],
        "svMapaComb": mapa["combinacoes"], "svMapaCanto": fmt(mapa["acuracia"][0][0]),
        "svGammaUmTreino": fmt(mapa["gamma1_C1"]["treino"]), "svGammaUmVal": fmt(mapa["gamma1_C1"]["validacao"]),
        "svMapaTempoMax": fmt(max(max(r) for r in mapa["tempo_s"])),
        "svInclSVC": fmt(t["SVC RBF"]["inclinacao"], 2), "svInclSVCLin": fmt(t["SVC linear"]["inclinacao"], 2),
        "svInclLinSVC": fmt(t["LinearSVC"]["inclinacao"], 2),
        "svTempoSVC": fmt(t["SVC RBF"]["tempo_s"][-1]), "svTempoLinSVC": fmt(t["LinearSVC"]["tempo_s"][-1], 2),
        "svGTresAuc": fmt(g["0.3"]["auc"]), "svGUmAuc": fmt(g["0.1"]["auc"]), "svGTresAcc": fmt(g["0.3"]["acuracia"]),
        "svGUmAcc": fmt(g["0.1"]["acuracia"]), "svGTresSeeds": g["0.3"]["seeds"], "svGUmSeeds": g["0.1"]["seeds"],
        "svGTresVet": thousands(g["0.3"]["vetores"]), "svGUmVet": thousands(g["0.1"]["vetores"]),
        "svLinC": fmt(top["SVM linear"][0]["C"]), "svLinCSeeds": top["SVM linear"][1],
        "svRBFCUmSeeds": sum(n for p, n in rbf if p["C"] == 1),
        "svPoliSeeds": top["SVM polinomial"][1], "svArvComb": d["escolhas"]["árvore de decisão"]["combinacoes"],
        "svRedeComb": len(d["escolhas"]["rede neural"]),
        "svRedeEpMin": m["rede neural"]["epocas"][0], "svRedeEpMax": m["rede neural"]["epocas"][1],
        "svBuscaTotalRBF": fmt(m["SVM RBF"]["busca_total_min"], 0),
        "svBuscaTotalSVM": fmt(sum(m[x]["busca_total_min"] for x in ["SVM linear", "SVM RBF", "SVM polinomial"]), 0),
        "svBuscaTotalRede": fmt(m["rede neural"]["busca_total_min"], 0),
        "svRecallRBF": fmt(100 * (1 - m["SVM RBF"]["fn"] / s0["positivos_teste"]), 0),
        "svRecallPesos": fmt(100 * (1 - m["SVM RBF com pesos"]["fn"] / s0["positivos_teste"]), 0),
        "svRBFPrevS": fmt(m["SVM RBF"]["previsao_ms"] / 1000),
        "svRazaoPrevRBFLin": fmt(m["SVM RBF"]["previsao_ms"] / m["SVM linear"]["previsao_ms"], 0),
        "svRazaoPrevRBFRede": fmt(m["SVM RBF"]["previsao_ms"] / m["rede neural"]["previsao_ms"], 0),
    }
    for nome, chave in CHAVE.items():
        info = m[nome]
        n[f"sv{chave}Acc"] = fmt(info["acuracia"])
        n[f"sv{chave}AccEn"] = f"{info['acuracia']:.1f}"
        n[f"sv{chave}Sd"] = fmt(info["desvio"])
        n[f"sv{chave}Fum"] = fmt(info["f1"])
        n[f"sv{chave}Fpos"] = fmt(info["f1_pos"])
        n[f"sv{chave}Auc"] = fmt(info["auc"])
        n[f"sv{chave}AucEn"] = f"{info['auc']:.1f}"
        n[f"sv{chave}FP"] = thousands(round(info["fp"]))
        n[f"sv{chave}FN"] = thousands(round(info["fn"]))
        n[f"sv{chave}Treino"] = fmt(info["treino_s"], 2 if info["treino_s"] < 1 else 1)
        n[f"sv{chave}Prev"] = fmt(info["previsao_ms"], 0 if info["previsao_ms"] >= 100 else 1)
        if info["busca_s"] is not None:
            n[f"sv{chave}Busca"] = fmt(info["busca_s"], 1) if info["busca_s"] < 60 else fmt(info["busca_s"] / 60, 1)
        if "vetores" in info:
            n[f"sv{chave}Vet"] = thousands(info["vetores"])
    for par, info in c.items():
        a, b2 = par.split(" × ")
        nome = CHAVE[a] + CHAVE[b2]
        for metrica, rotulo in [("acuracia", "Acc"), ("f1", "Fum"), ("auc", "Auc")]:
            n[f"svDif{nome}{rotulo}"] = signed(info[metrica]["pontos"], 2)
            n[f"svSeeds{nome}{rotulo}"] = info[metrica]["seeds"]
    linhas = ["% Gerado por scripts/svm_report.py a partir de report/results/svm_dados.json; não editar."]
    linhas += [f"\\newcommand{{\\{chave}}}{{{valor}}}" for chave, valor in n.items()]
    return "\n".join(linhas) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--png", action="store_true", help="grava também PNG, para conferir")
    args = parser.parse_args()
    d = json.loads(DATA.read_text(encoding="utf-8"))
    plt.rcParams.update(RC)
    FIGURES.mkdir(parents=True, exist_ok=True)
    for nome, fazer in [("svm_eda", fig_eda), ("svm_mapa", fig_mapa), ("svm_gamma", fig_gamma),
                        ("svm_tempo", fig_tempo), ("svm_acc_auc", fig_acc_auc)]:
        fig = fazer(d)
        fig.savefig(FIGURES / f"{nome}.pdf", bbox_inches="tight")
        if args.png:
            fig.savefig(FIGURES / f"{nome}.png", dpi=200, bbox_inches="tight")
        plt.close(fig)
    (RESULTS / "tab_svm_modelos.tex").write_text(tabela_modelos(d), encoding="utf-8")
    (RESULTS / "tab_svm_seed0.tex").write_text(tabela_seed0(d), encoding="utf-8")
    (RESULTS / "tab_svm_grades.tex").write_text(tabela_grades(d), encoding="utf-8")
    (RESULTS / "numeros_svm.tex").write_text(numeros(d), encoding="utf-8")
    print("gravado:", FIGURES, RESULTS)


if __name__ == "__main__":
    main()
