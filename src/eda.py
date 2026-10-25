"""Etapa 8: tabelas da análise exploratória da base final."""
import pandas as pd
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.tree import DecisionTreeClassifier

from src.config import CLASSES, FEATURES, RANDOM_STATE


def class_distribution(df, label="Protein"):
    """Linhas e percentual por classe."""
    counts = df[label].value_counts()
    return pd.DataFrame({"linhas": counts, "%": (counts / counts.sum() * 100).round(1)})


def complete_rows(final):
    """Linhas com os 5 descritores preenchidos (as que entram na modelagem, decisão D7)."""
    return final.dropna(subset=FEATURES)


def missing_summary(final):
    """Devolve (faltantes por coluna, linhas com faltante por classe, massa molecular dessas linhas)."""
    missing = final[final[FEATURES].isna().any(axis=1)]
    print("linhas com descritor faltante:", len(missing), f"({len(missing) / len(final):.2%})")
    return (
        final[FEATURES].isna().sum().to_frame("faltantes").T,
        missing["Protein"].value_counts().reindex(CLASSES).to_frame("linhas com faltante"),
        missing["Molecular Weight"].describe().round(1).to_frame("Molecular Weight das linhas com faltante").T,
    )


def describe_features(final):
    """Estatísticas descritivas das features e do pChEMBL."""
    return final[FEATURES + ["pChEMBL"]].describe().round(2).T


def medians_by_class(final):
    """Mediana de cada feature por classe."""
    return final.groupby("Protein")[FEATURES + ["pChEMBL"]].median().reindex(CLASSES).round(2)


def single_feature_accuracy(final, max_depth=3, folds=5):
    """Acurácia em validação cruzada de uma árvore rasa treinada com uma única feature.

    Diagnóstico do sinal de cada feature sozinha, não é o modelo final.
    Devolve (acurácia por feature, acurácia de sempre chutar a classe majoritária).
    """
    complete = complete_rows(final)
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=RANDOM_STATE)
    accuracy = pd.Series({
        feature: cross_val_score(DecisionTreeClassifier(max_depth=max_depth, random_state=RANDOM_STATE), complete[[feature]], complete["Protein"], cv=cv).mean()
        for feature in FEATURES
    }, dtype=float).sort_values()
    baseline = complete["Protein"].value_counts(normalize=True).max()
    return accuracy, baseline


def duplicates_and_outliers(final):
    """Contagem de duplicatas e valores extremos."""
    complete = complete_rows(final)
    duplicated = complete[complete[FEATURES].duplicated(keep=False)]
    conflicting = duplicated.groupby(FEATURES)["Protein"].nunique()
    return pd.Series({
        "ChEMBL ID duplicado": final["ChEMBL ID"].duplicated().sum(),
        "SMILES duplicado": final["SMILES"].duplicated().sum(),
        "linhas que repetem os 5 descritores de outra": complete[FEATURES].duplicated().sum(),
        "grupos de descritores idênticos com classes diferentes": (conflicting > 1).sum(),
        "Molecular Weight > 1.000 Da": (final["Molecular Weight"] > 1000).sum(),
        "LogP > 8": (final["LogP"] > 8).sum(),
    }).to_frame("linhas")


def duplicated_smiles(final):
    """Linhas cujo SMILES aparece mais de uma vez."""
    return final[final["SMILES"].duplicated(keep=False)]
