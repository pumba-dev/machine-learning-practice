"""Figuras, tabela e números da terceira parte do relatório (rede neural na base de empréstimos).

Lê report/results/rn_dados.json (gerado por rn_data.py) e grava:

    report/figures/rn_aprovacao_score.pdf   aprovação por faixa de score (o degrau em 550)
    report/figures/rn_neuronios.pdf         acurácia de validação por número de neurônios
    report/figures/rn_epocas.pdf            perda e acurácia por época; onde a paciência para o treino
    report/figures/rn_rampa_degrau.pdf      probabilidade de aprovação por score: rede (rampa) e árvore (degrau)
    report/figures/rn_correlacao.pdf        correlação entre os 11 atributos e a aprovação (triângulo inferior)
    report/figures/rn_confusao.pdf          matriz de confusão da rede e da árvore no teste (seed 42)
    report/results/tab_rn_modelos.tex       os seis modelos nas 10 seeds, com os tempos
    report/results/numeros_rn.tex           um \\newcommand por número citado no texto

Mesmo formato das figuras de export_figures.py (largura útil do template SBC = 15 cm, fonte 8 pt, fundo
branco, sem título dentro da figura) e mesma vírgula decimal de results_tables.py.

Uso, a partir da raiz do projeto:

    python scripts/rn_report.py           # PDF
    python scripts/rn_report.py --png     # também PNG, para conferir a olho
"""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.ticker import PercentFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "report" / "results" / "rn_dados.json"
FIGURES = ROOT / "report" / "figures"
RESULTS = ROOT / "report" / "results"

FULL, HALF = 5.9, 2.85
BLUE, ORANGE, GREEN, RED = "#2a78d6", "#eb6834", "#1baf7a", "#e34948"
GRAY, TEXT2 = "#8a8985", "#52514e"
RC = {
    "font.size": 8, "axes.titlesize": 8.5, "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7, "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#b9b8b2", "axes.labelcolor": TEXT2,
    "xtick.color": TEXT2, "ytick.color": TEXT2, "axes.grid": True, "grid.color": "#e7e6e1", "grid.linewidth": 0.6,
    "legend.frameon": False,
}
#: Nome no CSV -> nome no relatório.
ROTULO = {"classe majoritária": "Classe majoritária", "regra de um corte": "Regra de um corte",
          "regressão logística": "Regressão logística", "árvore de decisão": "Árvore de decisão",
          "random forest": "Random Forest", "rede neural": "Rede neural (MLP)"}


def fmt(value, digits=1):
    return f"{value:.{digits}f}".replace(".", ",")


def signed(value, digits=1):
    return fmt(value, digits) if value >= 0 else "$-$" + fmt(-value, digits)


# --- Figuras -----------------------------------------------------------------------------------

def fig_aprovacao(d):
    faixas = d["base"]["aprovacao_por_faixa"]
    inicio = np.array([int(k) for k in faixas])
    taxa = np.array(list(faixas.values())) / 100
    fig, ax = plt.subplots(figsize=(HALF, 2.0))
    ax.bar(inicio + 12.5, taxa, width=22, color=[GRAY if s < 550 else BLUE for s in inicio])
    ax.axvline(550, color="black", linewidth=0.9, linestyle="--")
    ax.text(544, 0.5, "550", color="black", fontsize=7.5, ha="right")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.set_ylim(0, 1.05)
    ax.set_xlim(295, 905)
    ax.set_xlabel("score de crédito (faixas de 25 pontos)")
    ax.set_ylabel("pedidos aprovados")
    ax.grid(axis="x", visible=False)
    return fig


def fig_neuronios(d):
    curva = d["seed42"]["neuronios"]
    modelos = d["multiseed"]["modelos"]
    fig, ax = plt.subplots(figsize=(HALF, 2.35))
    for chave, cor, nome in [("1_camada", BLUE, "1 camada oculta"), ("2_camada", ORANGE, "2 camadas ocultas")]:
        ax.plot(curva["neuronios"], np.array(curva[chave]) / 100, marker="o", markersize=3, color=cor, label=nome)
    ax.axhline(modelos["árvore de decisão"]["acuracia"] / 100, color="black", linestyle="--", linewidth=0.8,
               label="árvore (teste)")
    ax.axhline(modelos["regra de um corte"]["acuracia"] / 100, color=GRAY, linestyle=":", linewidth=1,
               label="regra de um corte (teste)")
    ax.set_xscale("log", base=2)
    ax.set_xticks(curva["neuronios"], curva["neuronios"])
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.set_ylim(0.92, 0.99)
    ax.set_xlabel("neurônios por camada oculta")
    ax.set_ylabel("acurácia de validação")
    ax.legend(loc="upper center", bbox_to_anchor=(0.45, -0.3), ncol=2, fontsize=6.3, columnspacing=1.0)
    return fig


def fig_epocas(d):
    epocas = d["seed42"]["epocas"]
    lenta, rapida = epocas["curvas"]["0.001"], epocas["curvas"]["0.01"]
    eixo = np.arange(1, len(lenta["perda treino"]) + 1)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(FULL, 2.1))
    ax1.plot(eixo, lenta["perda treino"], color=GRAY, label="treino")
    ax1.plot(eixo, lenta["perda validação"], color=BLUE, label="validação")
    ax1.set_xlabel("época")
    ax1.set_ylabel("perda (entropia cruzada)")
    ax1.set_title("(a) perda, taxa 0,001", loc="left")
    ax1.legend()
    ax2.plot(eixo, np.array(lenta["acurácia validação"]), color=BLUE, linewidth=0.9, label="taxa 0,001")
    ax2.plot(eixo, np.array(rapida["acurácia validação"]), color=ORANGE, linewidth=0.9, label="taxa 0,01")
    for parada in epocas["paradas"]:
        if parada["taxa"] == 0.001:
            ax2.axvline(parada["epoca"], color=BLUE, linewidth=0.9, linestyle=":" if parada["paciencia"] == 10 else "--",
                        label=f"parada com paciência {parada['paciencia']}")
    ax2.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax2.set_ylim(0.85, 1.0)
    ax2.set_xlabel("época")
    ax2.set_ylabel("acurácia de validação")
    ax2.set_title("(b) acurácia de validação", loc="left")
    ax2.legend(loc="lower right", fontsize=6.3)
    fig.tight_layout(w_pad=1.5)
    return fig


def fig_rampa(d):
    disp = d["seed42"]["dispersao"]
    score, real = np.array(disp["score"]), np.array(disp["real"])
    fig, eixos = plt.subplots(1, 2, figsize=(FULL, 2.0), sharey=True)
    for ax, (nome, letra) in zip(eixos, [("rede neural", "a"), ("árvore de decisão", "b")]):
        prob = np.array(disp[nome])
        for classe, cor, rotulo in [(1, GREEN, "aprovado"), (0, RED, "rejeitado")]:
            marca = real == classe
            ax.scatter(score[marca], prob[marca], s=3, alpha=0.5, color=cor, label=rotulo, rasterized=True, linewidths=0)
        ax.axvline(550, color="black", linewidth=0.8, linestyle="--")
        ax.set_title(f"({letra}) {nome}", loc="left")
        ax.set_xlabel("score de crédito")
        ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    eixos[0].set_ylabel("probabilidade de aprovação")
    eixos[0].legend(title="situação real", title_fontsize=7, loc="center right", markerscale=3)
    fig.tight_layout(w_pad=1.0)
    return fig


def fig_correlacao(d):
    corr = np.array(d["base"]["correlacao"]["matriz"])
    rotulos = d["base"]["correlacao"]["rotulos"]
    k = len(rotulos)
    # triângulo inferior sem a diagonal: linhas 1..k-1 contra colunas 0..k-2
    valores = np.ma.masked_array(corr[1:, :-1], mask=np.triu(np.ones((k - 1, k - 1), dtype=bool), 1))
    fig, ax = plt.subplots(figsize=(FULL, 4.3))
    im = ax.imshow(valores, cmap="RdBu_r", vmin=-1, vmax=1)
    for i in range(k - 1):
        for j in range(i + 1):
            v = corr[i + 1, j]
            texto = "0" if abs(v) < 0.005 else fmt(v, 2).replace("-", "−")
            ax.text(j, i, texto, ha="center", va="center", fontsize=6.5,
                    color="white" if abs(v) > 0.6 else "black")
    ax.set_xticks(range(k - 1), rotulos[:-1], rotation=45, ha="right", rotation_mode="anchor")
    ax.set_yticks(range(k - 1), rotulos[1:])
    ax.tick_params(length=0)
    ax.grid(False)
    for lado in ["left", "bottom"]:
        ax.spines[lado].set_visible(False)
    barra = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    barra.set_ticks([-1, -0.5, 0, 0.5, 1])
    barra.ax.tick_params(labelsize=7)
    barra.ax.yaxis.set_major_formatter(lambda v, _: fmt(v, 1).replace("-", "−"))
    barra.outline.set_visible(False)
    fig.tight_layout()
    return fig


def fig_confusao(d):
    erros = d["seed42"]["erros"]
    fig, eixos = plt.subplots(1, 2, figsize=(4.6, 1.85))
    for ax, (nome, letra) in zip(eixos, [("rede neural", "a"), ("árvore de decisão", "b")]):
        m = erros[nome]["matriz"]
        contagem = np.array([[m["vn"], m["fp"]], [m["fn"], m["vp"]]])
        proporcao = contagem / contagem.sum(axis=1, keepdims=True)
        ax.imshow(proporcao, cmap="Blues", vmin=0, vmax=1)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(contagem[i, j]), ha="center", va="center", fontsize=8,
                        color="white" if proporcao[i, j] > 0.5 else "black")
        ax.set_xticks([0, 1], ["rejeitado", "aprovado"])
        ax.set_yticks([0, 1], ["rejeitado", "aprovado"] if letra == "a" else ["", ""])
        ax.set_xlabel("previsto")
        if letra == "a":
            ax.set_ylabel("real")
        ax.set_title(f"({letra}) {nome}", loc="left")
        ax.grid(False)
        for lado in ["left", "bottom"]:
            ax.spines[lado].set_visible(False)
        ax.tick_params(length=0)
    fig.tight_layout(w_pad=0.8)
    return fig


# --- Tabela e números --------------------------------------------------------------------------

def tabela_modelos(d):
    linhas = [r"\setlength{\tabcolsep}{4pt}", r"\begin{tabular}{lccccccc}", r"\toprule",
              r"Modelo & Acurácia (\%) & \shortstack{F1 macro\\(\%)} & AUC (\%) & Erros &\shortstack{Treino\\(ms)} & "
              r"\shortstack{Busca\\(s)} & \shortstack{Previsão\\(ms)} \\", r"\midrule"]
    for nome, m in d["multiseed"]["modelos"].items():
        treino = fmt(m["treino_ms"], 0) if m["treino_ms"] >= 100 else fmt(m["treino_ms"], 1)
        busca = "--" if m["busca_s"] is None else fmt(m["busca_s"], 2 if m["busca_s"] < 1 else 1)
        linhas.append(f"{ROTULO[nome]} & {fmt(m['acuracia'])} $\\pm$ {fmt(m['desvio'])} & {fmt(m['f1'])} & "
                      f"{fmt(m['auc'])} & {fmt(m['erros'])} & {treino} & {busca} & {fmt(m['previsao_ms'], 2 if m['previsao_ms'] < 0.1 else 1)} \\\\")
    linhas += [r"\bottomrule", r"\end{tabular}"]
    return "\n".join(linhas) + "\n"


def numeros(d):
    base, ms, s42 = d["base"], d["multiseed"], d["seed42"]
    m, c, r = ms["modelos"], ms["comparacoes"], ms["rede"]
    sufixo = {"classe majoritária": "Maj", "regra de um corte": "Regra", "regressão logística": "Log",
              "árvore de decisão": "Arv", "random forest": "RF", "rede neural": "Rede"}
    n = {
        "rnLinhas": f"{base['linhas']:,}".replace(",", "."),
        "rnAprovados": fmt(base["aprovados"]),
        "rnNegativos": str(base["negativos_residencial"]),
        "rnRegraBase": fmt(base["regra_550_base"]),
        "rnAprovAbaixo": fmt(base["aprovacao_abaixo_550"], 0),
        "rnAprovAcima": fmt(base["aprovacao_acima_550"]),
        "rnAprovPrazoDois": fmt(base["aprovacao_abaixo_550_por_prazo"]["2"], 0),
        "rnAprovPrazoQuatro": fmt(base["aprovacao_abaixo_550_por_prazo"]["4"], 0),
        "rnCorrScore": fmt(base["corr_score_alvo"], 2),
        "rnCorrPrazo": signed(base["corr_prazo_alvo"], 2),
        "rnCorrRendaValor": fmt(base["corr_renda_valor"], 2),
        "rnCorrRendaLuxo": fmt(base["corr_renda_luxo"], 2),
        "rnTreino": f"{s42['treino']:,}".replace(",", "."),
        "rnTeste": str(s42["teste"]),
        "rnPrimeiraAcc": fmt(s42["primeira_rede"]["acuracia"]),
        "rnPrimeiraEpocas": str(s42["primeira_rede"]["epocas"]),
        "rnSemPadAcc": fmt(d["padronizacao"]["sem"]["acuracia"]),
        "rnSemPadSd": fmt(d["padronizacao"]["sem"]["desvio"]),
        "rnSemPadAuc": fmt(d["padronizacao"]["sem"]["auc"]),
        "rnComPadAcc": fmt(d["padronizacao"]["com"]["acuracia"]),
        "rnComPadSd": fmt(d["padronizacao"]["com"]["desvio"]),
        "rnCombinacoes": str(r["combinacoes"]),
        "rnCombinacoesArv": str(r["combinacoes_arvore"]),
        "rnSeedsTaxa": str(r["taxa_001"]),
        "rnSeedsDuas": str(r["duas_camadas"]),
        "rnSeedsTrintaDezesseis": str(r["arquiteturas"].get("32-16", 0)),
        "rnEpocasMin": str(r["epocas"][0]),
        "rnEpocasMed": fmt(r["epocas"][1], 1 if r["epocas"][1] % 1 else 0),
        "rnEpocasMax": str(r["epocas"][2]),
    }
    for nome, suf in sufixo.items():
        n[f"rnAcc{suf}"] = fmt(m[nome]["acuracia"])
        n[f"rnSd{suf}"] = fmt(m[nome]["desvio"])
        n[f"rnAuc{suf}"] = fmt(m[nome]["auc"])
        n[f"rnErros{suf}"] = fmt(m[nome]["erros"])
    for nome, suf in [("regra de um corte", "Regra"), ("regressão logística", "Log"), ("árvore de decisão", "Arv"),
                      ("rede neural", "Rede")]:
        n[f"rnAcc{suf}En"] = f"{m[nome]['acuracia']:.1f}"  # abstract em inglês: ponto decimal
    n["rnLinhasEn"] = f"{base['linhas']:,}"
    n["rnTreinoArvMs"] = fmt(m["árvore de decisão"]["treino_ms"])
    n["rnTreinoRedeMs"] = fmt(m["rede neural"]["treino_ms"], 0)
    n["rnTreinoRFMs"] = fmt(m["random forest"]["treino_ms"], 0)
    n["rnBuscaRede"] = fmt(m["rede neural"]["busca_s"])
    n["rnBuscaArv"] = fmt(m["árvore de decisão"]["busca_s"], 2)
    n["rnPrevRFMs"] = fmt(m["random forest"]["previsao_ms"], 0)
    n["rnPrevRedeMs"] = fmt(m["rede neural"]["previsao_ms"])
    n["rnRazaoTreino"] = fmt(m["rede neural"]["treino_ms"] / m["árvore de decisão"]["treino_ms"], 0)
    n["rnRazaoBusca"] = fmt(m["rede neural"]["busca_s"] / m["árvore de decisão"]["busca_s"], 0)
    pares = {"rede neural × regra de um corte": "RedeRegra", "rede neural × regressão logística": "RedeLog",
             "rede neural × árvore de decisão": "RedeArv", "rede neural × random forest": "RedeRF",
             "regra de um corte × regressão logística": "RegraLog", "árvore de decisão × regra de um corte": "ArvRegra",
             "random forest × árvore de decisão": "RFArv"}
    for chave, suf in pares.items():
        n[f"rnDif{suf}"] = signed(c[chave]["pontos"])
        n[f"rnSeeds{suf}"] = str(c[chave]["seeds"])
    paradas = {(p["taxa"], p["paciencia"]): p for p in s42["epocas"]["paradas"]}
    for (taxa, paciencia), suf in [((0.001, 10), "LentaDez"), ((0.001, 30), "LentaTrinta"),
                                   ((0.01, 10), "RapidaDez"), ((0.01, 30), "RapidaTrinta")]:
        n[f"rnParada{suf}"] = str(paradas[(taxa, paciencia)]["epoca"])
        n[f"rnParadaAcc{suf}"] = fmt(paradas[(taxa, paciencia)]["acuracia"])
    n["rnMelhorLenta"] = fmt(paradas[(0.001, 10)]["melhor"])
    n["rnMelhorRapida"] = fmt(paradas[(0.01, 10)]["melhor"])
    neur = s42["neuronios"]
    n["rnNeurUm"] = fmt(neur["1_camada"][0])
    n["rnNeurQuatro"] = fmt(neur["1_camada"][2])
    n["rnNeurSessentaQuatro"] = fmt(neur["1_camada"][-1])
    n["rnNeurOitoDuas"] = fmt(neur["2_camada"][3])
    e = s42["erros"]
    rede_f, arv_f = e["rede neural"]["por_faixa"], e["árvore de decisão"]["por_faixa"]
    n.update({"rnErrosRedeSeed": str(e["rede neural"]["total"]), "rnErrosArvSeed": str(e["árvore de decisão"]["total"]),
              "rnPedidosFaixa": str(e["pedidos"][2]), "rnErrosRedeFaixa": str(rede_f[2]),
              "rnErrosArvFaixa": str(arv_f[2]), "rnExcecao": str(e["excecao_pedidos"]),
              "rnErrosRedeExc": str(e["rede neural"]["na_excecao"]), "rnErrosArvExc": str(e["árvore de decisão"]["na_excecao"]),
              "rnInterRede": fmt(e["rede_intermediarias_500_600"], 0),
              "rnInterArv": fmt(e["arvore_intermediarias_500_600"], 0)})
    cf = d["confusao"]
    for nome, suf in [("rede neural", "Rede"), ("árvore de decisão", "Arv")]:
        m42, media = e[nome]["matriz"], cf[nome]["media"]
        n[f"rnFP{suf}Seed"], n[f"rnFN{suf}Seed"] = str(m42["fp"]), str(m42["fn"])
        n[f"rnFP{suf}Med"], n[f"rnFN{suf}Med"] = fmt(media["fp"]), fmt(media["fn"])
        n[f"rnTaxaFP{suf}"] = fmt(100 * media["fp"] / (media["fp"] + media["vn"]))
        n[f"rnTaxaFN{suf}"] = fmt(100 * media["fn"] / (media["fn"] + media["vp"]))
        n[f"rnSeedsFN{suf}"] = str(cf[nome]["seeds_mais_fn"])
    m42 = e["rede neural"]["matriz"]
    n["rnTesteRej"], n["rnTesteAprov"] = str(m42["vn"] + m42["fp"]), str(m42["fn"] + m42["vp"])
    rejeitados = round(base["linhas"] * (1 - base["aprovados"] / 100))
    n["rnRejeitadosBase"] = f"{rejeitados:,}".replace(",", ".")
    n["rnRazaoClasses"] = fmt(base["aprovados"] / (100 - base["aprovados"]))
    linhas = ["% Gerado por scripts/rn_report.py a partir de report/results/rn_dados.json; não editar."]
    linhas += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in n.items()]
    return "\n".join(linhas) + "\n", n


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--png", action="store_true", help="grava também PNG para conferir")
    args = parser.parse_args()
    d = json.loads(DATA.read_text(encoding="utf-8"))
    plt.rcParams.update(RC)
    for nome, funcao in [("rn_aprovacao_score", fig_aprovacao), ("rn_neuronios", fig_neuronios),
                         ("rn_epocas", fig_epocas), ("rn_rampa_degrau", fig_rampa),
                         ("rn_correlacao", fig_correlacao), ("rn_confusao", fig_confusao)]:
        fig = funcao(d)
        fig.savefig(FIGURES / f"{nome}.pdf", bbox_inches="tight", pad_inches=0.02, dpi=300)
        if args.png:
            fig.savefig(FIGURES / f"{nome}.png", bbox_inches="tight", pad_inches=0.02, dpi=200)
        plt.close(fig)
        print("figura:", nome)
    (RESULTS / "tab_rn_modelos.tex").write_text(tabela_modelos(d), encoding="utf-8")
    texto, n = numeros(d)
    (RESULTS / "numeros_rn.tex").write_text(texto, encoding="utf-8")
    print("tabela e", len(n), "números gravados")


if __name__ == "__main__":
    main()
