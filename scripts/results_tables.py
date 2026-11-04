"""Gera as tabelas LaTeX e os números do relatório a partir de report/results/multiseed.csv.

Uso, a partir da raiz do projeto (depois de scripts/multiseed.py):

    python scripts/results_tables.py

Saídas em report/results/:
    tab_features.tex    resultados da árvore por conjunto de atributos
    tab_referencia.tex  árvore contra os modelos de referência (usada pela primeira apresentação)
    tab_modelos.tex     todos os modelos no cenário escolhido (árvore, Random Tree, RF, GB)
    tab_rt.tex          Random Tree ajustada contra a árvore nos 6 cenários
    numeros.tex         um \\newcommand por número citado no texto (acurácias, ganhos, superestimativas)

Tudo sai do CSV, então o texto do relatório, as tabelas e o resumo não divergem de uma execução para outra.
Acurácias e F1 aparecem em %. Ganho e superestimativa são relativos: (B - A) / A, calculado por seed
(mesmas divisões de dados nas duas pontas) e depois com a média sobre as seeds.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "report" / "results"
TREE = "Árvore de decisão"
FEATURES = ["descritores", "só SMILES", "descritores + SMILES"]
LABELS = {"descritores": "Descritores (5)", "só SMILES": "SMILES (12)", "descritores + SMILES": "Ambos (17)"}
#: Sufixo dos nomes de macro por conjunto de atributos (macros só aceitam letras).
SUFFIX = {"descritores": "Desc", "só SMILES": "Smiles", "descritores + SMILES": "Ambos"}
CLASSES = ["EGFR", "BACE1", "DRD2", "HDAC1"]
#: Nomes de macro não aceitam dígitos, então o 1 e o 2 das classes viram palavra.
MACRO_CLASS = {"EGFR": "EGFR", "BACE1": "BACEone", "DRD2": "DRDtwo", "HDAC1": "HDACone"}
MODELS = {
    "Dummy (classe majoritária)": ("Classe majoritária (EGFR)", "Maj"),
    TREE: (TREE, "Arvore"),
    "Random Forest (300 árvores)": ("Random Forest (300 árvores)", "RF"),
    "HistGradientBoosting": ("Gradient boosting (histogramas)", "HGB"),
}
#: Modelos da comparação no relatório, na ordem da tabela: nome no CSV -> (rótulo, sufixo de macro).
#: O bagging do multiseed fica de fora (só aparece no notebook 07). `MODELS` acima fica como está
#: porque os slides da primeira apresentação dependem dele.
ALL_MODELS = {
    "Dummy (classe majoritária)": ("Classe majoritária (EGFR)", "Maj"),
    TREE: (TREE, "Arvore"),
    "Random Tree (padrão Weka)": ("Random Tree (padrão do Weka)", "RTweka"),
    "Random Tree": ("Random Tree (ajustada)", "RT"),
    "Random Forest (300 árvores)": ("Random Forest (padrão)", "RF"),
    "Random Forest (ajustada)": ("Random Forest (ajustada)", "RFaj"),
    "HistGradientBoosting": ("Gradient boosting (padrão)", "HGB"),
    "Gradient boosting (ajustado)": ("Gradient boosting (ajustado)", "GBaj"),
}
SPLIT_LABEL = {"aleatória": "Aleatória", "agrupada": "Agrupada"}


def fmt(value, digits=1):
    """Número com vírgula decimal."""
    return f"{value:.{digits}f}".replace(".", ",")


def pm(series, digits=1):
    """'média $\\pm$ desvio' em %, com vírgula decimal; o desvio é o amostral (ddof=1)."""
    return f"{fmt(series.mean() * 100, digits)} $\\pm$ {fmt(series.std() * 100, digits)}"


def paired(results, features, model=TREE):
    """Acurácia por seed (índice = seed) nos dois splits de um conjunto de atributos."""
    part = results[(results["modelo"] == model) & (results["features"] == features)]
    return (part[part["split"] == "aleatória"].set_index("seed"),
            part[part["split"] == "agrupada"].set_index("seed"))


def features_table(results):
    """Árvore em cada conjunto de atributos: as duas divisões, F1 macro agrupado e a superestimativa relativa."""
    rows = []
    for features in FEATURES:
        random, grouped = paired(results, features)
        over = (random["acurácia"] / grouped["acurácia"] - 1)
        rows.append(f"{LABELS[features]} & {pm(random['acurácia'])} & {pm(grouped['acurácia'])} & "
                    f"{pm(grouped['F1 macro'])} & {pm(over)} \\\\")
    return rows


def reference_table(results):
    """Piso, árvore escolhida e modelos de referência, todos na divisão agrupada com os 17 atributos."""
    chosen = results[(results["features"] == "descritores + SMILES") & (results["split"] == "agrupada")]
    return [f"{label} & {pm(chosen[chosen['modelo'] == model]['acurácia'])} & "
            f"{pm(chosen[chosen['modelo'] == model]['F1 macro'])} \\\\"
            for model, (label, _) in MODELS.items()]


def signed(value, digits=1):
    """Número com sinal de menos tipográfico do LaTeX quando negativo."""
    return f"$-${fmt(-value, digits)}" if value < 0 else fmt(value, digits)


def chosen_by_seed(results, model, column="acurácia"):
    """Valor por seed (índice = seed) de um modelo no cenário escolhido."""
    chosen = results[(results["features"] == "descritores + SMILES") & (results["split"] == "agrupada")]
    return chosen[chosen["modelo"] == model].set_index("seed")[column]


def models_table(results):
    """Todos os modelos no cenário escolhido: acurácia, F1 macro e diferença relativa para a árvore."""
    tree = chosen_by_seed(results, TREE)
    rows = []
    for model, (label, _) in ALL_MODELS.items():
        acc = chosen_by_seed(results, model)
        f1 = chosen_by_seed(results, model, "F1 macro")
        gain = "--" if model in {TREE, "Dummy (classe majoritária)"} else signed((acc / tree - 1).mean() * 100)
        rows.append(f"{label} & {pm(acc)} & {pm(f1)} & {gain} \\\\")
    return rows


def rt_table(results):
    """Random Tree ajustada contra a árvore de decisão nos 6 cenários (média das seeds)."""
    rows = []
    for features in FEATURES:
        for split in ["aleatória", "agrupada"]:
            part = results[(results["features"] == features) & (results["split"] == split)]
            tree = part[part["modelo"] == TREE].set_index("seed")["acurácia"]
            rt = part[part["modelo"] == "Random Tree"].set_index("seed")["acurácia"]
            rel = (rt / tree - 1) * 100
            rows.append(f"{LABELS[features]} & {SPLIT_LABEL[split]} & {pm(tree)} & {pm(rt)} & "
                        f"{signed(rel.mean())} & {int((rt > tree).sum())} \\\\")
    return rows


def ensemble_macros(results):
    """Números da comparação entre todos os modelos (Random Tree, RF e GB ajustados).

    Só acrescenta nomes novos; os que `macros` já define ficam com o mesmo valor."""
    out = {}
    tree = chosen_by_seed(results, TREE)
    for model, (_, suf) in ALL_MODELS.items():
        acc = chosen_by_seed(results, model)
        if suf not in {"Maj", "Arvore", "RF", "HGB"}:
            out[f"acc{suf}"] = fmt(acc.mean() * 100)
            out[f"sd{suf}"] = fmt(acc.std() * 100)
        out[f"fone{suf}"] = fmt(chosen_by_seed(results, model, "F1 macro").mean() * 100)
        out[f"fscoreHDACone{suf}"] = fmt(chosen_by_seed(results, model, "F1 HDAC1").mean() * 100)
        if model != TREE and suf != "Maj":
            rel = (acc / tree - 1) * 100
            # Ganho (positivo) ou queda (valor absoluto) relativo à árvore, para o texto escolher o verbo.
            out[f"rel{suf}"] = fmt(abs(rel.mean()))
            out[f"pontos{suf}"] = fmt(abs((acc - tree).mean() * 100))
            out[f"seedsAcima{suf}"] = str(int((acc > tree).sum()))
    # Random Tree ajustada contra a árvore nos 6 cenários.
    losses, worst = 0, (0.0, "")
    for features in FEATURES:
        for split in ["aleatória", "agrupada"]:
            part = results[(results["features"] == features) & (results["split"] == split)]
            t = part[part["modelo"] == TREE].set_index("seed")["acurácia"]
            r = part[part["modelo"] == "Random Tree"].set_index("seed")["acurácia"]
            rel = ((r / t - 1) * 100).mean()
            losses += rel < 0
            worst = min(worst, (rel, features))
    # Quanto o boosting ajustado acerta a mais que a Random Forest padrão, em pontos.
    out["difGBRF"] = fmt((chosen_by_seed(results, "Gradient boosting (ajustado)")
                          - chosen_by_seed(results, "Random Forest (300 árvores)")).mean() * 100)
    out["cenariosRTabaixo"] = str(losses)
    out["piorRT"] = fmt(abs(worst[0]))
    return out


def macros(results):
    """Dicionário nome -> texto de todos os números que o relatório cita."""
    out = {}
    grouped_acc, over_mean = {}, {}
    for features in FEATURES:
        random, grouped = paired(results, features)
        suf = SUFFIX[features]
        grouped_acc[features] = grouped["acurácia"]
        over = random["acurácia"] / grouped["acurácia"] - 1
        over_mean[features] = over.mean() * 100
        out[f"accGrup{suf}"] = fmt(grouped["acurácia"].mean() * 100)
        out[f"sdGrup{suf}"] = fmt(grouped["acurácia"].std() * 100)
        out[f"accAleat{suf}"] = fmt(random["acurácia"].mean() * 100)
        out[f"gap{suf}"] = fmt(over.mean() * 100)
        out[f"sdGap{suf}"] = fmt(over.std() * 100)
    out["gapMin"], out["gapMax"] = fmt(min(over_mean.values())), fmt(max(over_mean.values()))

    ambos = grouped_acc["descritores + SMILES"]
    out["ganhoAmbos"] = fmt((ambos / grouped_acc["descritores"] - 1).mean() * 100, 0)
    out["ganhoSmiles"] = fmt((grouped_acc["só SMILES"] / grouped_acc["descritores"] - 1).mean() * 100, 0)
    out["faixaMin"], out["faixaMax"] = fmt(ambos.min() * 100), fmt(ambos.max() * 100)
    out["fscoreGrupAmbos"] = fmt(paired(results, "descritores + SMILES")[1]["F1 macro"].mean() * 100)
    for c in CLASSES:
        out[f"fscore{MACRO_CLASS[c]}"] = fmt(paired(results, "descritores + SMILES")[1][f"F1 {c}"].mean() * 100)

    chosen = results[(results["features"] == "descritores + SMILES") & (results["split"] == "agrupada")]
    tree_acc = chosen[chosen["modelo"] == TREE].set_index("seed")["acurácia"]
    for model, (_, suf) in MODELS.items():
        acc = chosen[chosen["modelo"] == model].set_index("seed")["acurácia"]
        out[f"acc{suf}"] = fmt(acc.mean() * 100)
        out[f"sd{suf}"] = fmt(acc.std() * 100)
    rf = chosen[chosen["modelo"] == "Random Forest (300 árvores)"].set_index("seed")["acurácia"]
    out["ganhoRF"] = fmt((rf / tree_acc - 1).mean() * 100)
    out["gemeas"] = fmt(results["% teste com gêmeo"].mean())
    out["sdGemeas"] = fmt(results["% teste com gêmeo"].std())
    out["nSeeds"] = str(results["seed"].nunique())
    return out


def main():
    results = pd.read_csv(RESULTS / "multiseed.csv")

    header = "\\begin{tabular}{lcccc}\n\\toprule\n" \
             "Atributos & \\shortstack{Acurácia\\\\aleatória (\\%)} & \\shortstack{Acurácia\\\\agrupada (\\%)} & " \
             "\\shortstack{F1 macro\\\\agrupado (\\%)} & \\shortstack{Superestimativa\\\\(\\%)} \\\\\n\\midrule\n"
    body = "\n".join(features_table(results))
    (RESULTS / "tab_features.tex").write_text(f"{header}{body}\n\\bottomrule\n\\end{{tabular}}\n", encoding="utf-8")

    header = "\\begin{tabular}{lcc}\n\\toprule\nModelo & Acurácia (\\%) & F1 macro (\\%) \\\\\n\\midrule\n"
    (RESULTS / "tab_referencia.tex").write_text(
        f"{header}{chr(10).join(reference_table(results))}\n\\bottomrule\n\\end{{tabular}}\n", encoding="utf-8")

    header = "\\begin{tabular}{lccc}\n\\toprule\n" \
             "Modelo & Acurácia (\\%) & F1 macro (\\%) & \\shortstack{Diferença para\\\\a árvore (\\%)} \\\\\n\\midrule\n"
    (RESULTS / "tab_modelos.tex").write_text(
        f"{header}{chr(10).join(models_table(results))}\n\\bottomrule\n\\end{{tabular}}\n", encoding="utf-8")

    header = "\\begin{tabular}{llcccc}\n\\toprule\n" \
             "Atributos & Divisão & \\shortstack{Árvore de\\\\decisão (\\%)} & \\shortstack{Random\\\\Tree (\\%)} & " \
             "\\shortstack{Diferença\\\\(\\%)} & \\shortstack{Seeds com\\\\RT melhor} \\\\\n\\midrule\n"
    (RESULTS / "tab_rt.tex").write_text(
        f"{header}{chr(10).join(rt_table(results))}\n\\bottomrule\n\\end{{tabular}}\n", encoding="utf-8")

    values = macros(results)
    values.update(ensemble_macros(results))
    # Variante com ponto decimal para o abstract em inglês: "accGrupDesc" -> "accGrupDescEn".
    values.update({f"{name}En": text.replace(",", ".") for name, text in list(values.items())})
    lines = [f"\\newcommand{{\\{name}}}{{{text}}}" for name, text in values.items()]
    (RESULTS / "numeros.tex").write_text("% Gerado por scripts/results_tables.py; não editar.\n" + "\n".join(lines) + "\n",
                                         encoding="utf-8")
    print(f"{values['nSeeds']} seeds")
    for name, text in values.items():
        print(f"  {name} = {text}")


if __name__ == "__main__":
    main()
