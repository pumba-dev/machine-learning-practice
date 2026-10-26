"""Notebook 03: treino, ajuste e avaliação da árvore de decisão.

A ordem de uso é a do notebook:

1. `prepare`        monta X, y, os ids de grupo e os dois splits de uma vez
2. `feature_summary` descreve as colunas derivadas do SMILES
3. `group_leakage`  mede o vazamento que o split aleatório deixa passar
4. `split_summary`  confere as proporções de classe nos dois splits
5. `tune_all`       busca em grade nas 6 combinações (3 conjuntos × 2 splits)
6. `leakage_gap`    quanto o split aleatório superestima
7. `depth_curve` / `pruning_curve`  profundidade e poda
8. `tree_rules` / `importances` / `evaluation` / `reference_models`
"""
from collections import namedtuple

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import (
    GridSearchCV,
    StratifiedGroupKFold,
    StratifiedKFold,
    train_test_split,
    validation_curve,
)
from sklearn.tree import DecisionTreeClassifier, export_text

from src.config import CLASSES, CV_FOLDS, FEATURE_SETS, FEATURES, RANDOM_STATE, SMILES_FEATURES, TEST_SIZE
from src.eda import complete_rows

#: X, y, ids de grupo e os dois splits, para não repassar quatro objetos em cada chamada.
Dados = namedtuple("Dados", "X y grupos splits")

SPLITS = ["aleatória", "agrupada"]
#: A combinação honesta: features completas e split sem vazamento. Usada das seções 6 a 11.
CHOSEN = ("descritores + SMILES", "agrupada")

PARAM_GRID = {
    "criterion": ["gini", "entropy"],
    "max_depth": [8, 12, 16, None],
    "min_samples_leaf": [1, 5, 20],
    "ccp_alpha": [0.0, 1e-4, 3e-4],
}
DEPTHS = [2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 25]
ALPHAS = [0.0, 1e-5, 3e-5, 1e-4, 3e-4, 1e-3, 3e-3, 1e-2]


def smiles_features(smiles):
    """Conta caracteres do SMILES e devolve 12 colunas numéricas, sem biblioteca de química."""
    # Cl e Br viram um símbolo único antes de contar: senão o "C" de "Cl" entraria na contagem
    # de carbono e o "r" de "Br" em nenhuma.
    flat = smiles.str.replace("Cl", "X", regex=False).str.replace("Br", "X", regex=False)
    return pd.DataFrame({
        "smiles_len": smiles.str.len(),
        # Maiúsculas e minúsculas juntas: a minúscula marca átomo em anel aromático.
        "n_N": flat.str.count("[Nn]"),
        "n_O": flat.str.count("[Oo]"),
        "n_S": flat.str.count("[Ss]"),
        "n_halogen": flat.str.count("[XFI]"),
        # Cada anel abre e fecha com o mesmo dígito. Conta errado na notação %10, rara nesta base.
        "n_rings": smiles.str.count(r"\d") // 2,
        "n_branch": smiles.str.count(r"\("),
        "n_aromatic": flat.str.count("[cnos]"),
        "n_double": smiles.str.count("="),
        "n_triple": smiles.str.count("#"),
        "n_charge": smiles.str.count(r"[+-]"),
        "n_stereo": smiles.str.count("@") + smiles.str.count("/"),
    }, index=smiles.index)


def descriptor_groups(complete):
    """Id de grupo por linha: linhas com a mesma tupla dos 5 descritores recebem o mesmo id."""
    # O ChEMBL já publica no máximo 2 casas decimais, então round(2) não muda nada hoje. Fica como
    # garantia caso um novo download venha com mais precisão. A chave é texto para não comparar float.
    key = complete[FEATURES].round(2).astype(str).agg("|".join, axis=1)
    return pd.factorize(key)[0]


def _random_split(y):
    """Split estratificado comum: ignora que linhas repetidas podem cair dos dois lados."""
    train, test = train_test_split(np.arange(len(y)), test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE)
    return np.sort(train), np.sort(test)


def _grouped_split(y, grupos):
    """Primeiro fold do StratifiedGroupKFold: mantém as proporções de classe e não parte grupos."""
    splitter = StratifiedGroupKFold(n_splits=round(1 / TEST_SIZE), shuffle=True, random_state=RANDOM_STATE)
    return next(iter(splitter.split(np.zeros(len(y)), y, groups=grupos)))


def prepare(final):
    """Monta X (descritores + SMILES), y, os ids de grupo e os dois splits de uma vez."""
    complete = complete_rows(final).reset_index(drop=True)
    X = pd.concat([complete[FEATURES], smiles_features(complete["SMILES"])], axis=1)
    # `pChEMBL` é resultado do ensaio contra o alvo e não pode entrar como feature.
    assert list(X.columns) == FEATURES + SMILES_FEATURES, "colunas inesperadas em X"
    grupos = descriptor_groups(complete)
    y = complete["Protein"]
    splits = {"aleatória": _random_split(y), "agrupada": _grouped_split(y, grupos)}
    return Dados(X, y, grupos, splits)


def _subset(dados, features=None, split=None):
    """Recorta (X_treino, X_teste, y_treino, y_teste) de um conjunto de features e um split."""
    features, split = features or CHOSEN[0], split or CHOSEN[1]
    train, test = dados.splits[split]
    X = dados.X[FEATURE_SETS[features]]
    return X.iloc[train], X.iloc[test], dados.y.iloc[train], dados.y.iloc[test]


def feature_summary(dados):
    """Estatísticas descritivas das colunas derivadas do SMILES."""
    return dados.X[SMILES_FEATURES].describe().round(1).T[["mean", "std", "min", "50%", "max"]]


def group_leakage(dados):
    """Tabela do vazamento: grupos, linhas repetidas e quanto do teste teria um gêmeo no treino."""
    sizes = pd.Series(dados.grupos).value_counts()
    train, test = dados.splits["aleatória"]
    twins = np.isin(dados.grupos[test], dados.grupos[train]).sum()
    classes_por_grupo = pd.DataFrame({"g": dados.grupos, "y": dados.y}).groupby("g")["y"].nunique()
    return pd.Series({
        "linhas completas": len(dados.X),
        "tuplas de descritores distintas": len(sizes),
        "linhas que repetem outra": len(dados.X) - len(sizes),
        "maior grupo": sizes.max(),
        "grupos com mais de uma classe": int((classes_por_grupo > 1).sum()),
        "teste com gêmeo no treino (split aleatório)": twins,
        "% do teste com gêmeo": round(100 * twins / len(test), 1),
    }).to_frame("valor")


def split_summary(dados):
    """Linhas e proporção de cada classe no treino e no teste dos dois splits."""
    columns = {}
    for split in SPLITS:
        for name, idx in zip(["treino", "teste"], dados.splits[split]):
            share = dados.y.iloc[idx].value_counts(normalize=True).reindex(CLASSES)
            columns[(split, f"{name} (n={len(idx)})")] = (share * 100).round(1)
    return pd.DataFrame(columns)


def _search(split, grid=PARAM_GRID):
    """GridSearchCV cuja validação cruzada respeita o mesmo agrupamento do split externo."""
    # Usar StratifiedKFold dentro de um treino agrupado dá uma CV ~5 pontos otimista: o splitter
    # interno precisa seguir a mesma disciplina do externo.
    cv = (StratifiedGroupKFold(CV_FOLDS, shuffle=True, random_state=RANDOM_STATE) if split == "agrupada"
          else StratifiedKFold(CV_FOLDS, shuffle=True, random_state=RANDOM_STATE))
    return GridSearchCV(DecisionTreeClassifier(random_state=RANDOM_STATE), grid, scoring="accuracy", cv=cv, n_jobs=-1)


def tune_all(dados, grid=PARAM_GRID):
    """Busca em grade nas 6 combinações; devolve a tabela comparativa e os modelos ajustados."""
    rows, models = [], {}
    for features in FEATURE_SETS:
        for split in SPLITS:
            X_tr, X_te, y_tr, y_te = _subset(dados, features, split)
            groups = dados.grupos[dados.splits[split][0]] if split == "agrupada" else None
            search = _search(split, grid).fit(X_tr, y_tr, groups=groups)
            tree = search.best_estimator_
            models[(features, split)] = tree
            rows.append({
                "features": features,
                "split": split,
                "acurácia CV": round(search.best_score_, 3),
                "acurácia teste": round(accuracy_score(y_te, tree.predict(X_te)), 3),
                "F1 macro teste": round(f1_score(y_te, tree.predict(X_te), average="macro"), 3),
                "folhas": tree.get_n_leaves(),
                "profundidade": tree.get_depth(),
                "ccp_alpha": search.best_params_["ccp_alpha"],
            })
    return pd.DataFrame(rows), models


def best_params_table(models):
    """Hiperparâmetros escolhidos em cada combinação."""
    return pd.DataFrame(
        [{"features": f, "split": s, **{k: v for k, v in m.get_params().items() if k in PARAM_GRID}}
         for (f, s), m in models.items()]
    )


def leakage_gap(comparacao):
    """Quanto o split aleatório superestima a acurácia, por conjunto de features."""
    wide = comparacao.pivot(index="features", columns="split", values="acurácia teste")
    wide["diferença (pontos)"] = ((wide["aleatória"] - wide["agrupada"]) * 100).round(1)
    return wide.reindex(FEATURE_SETS)


def _sweep(dados, param, values, features, split):
    """Varre um hiperparâmetro em uma única chamada paralela; um laço com cross_val_score por
    valor gastaria mais tempo criando processos no Windows do que ajustando árvores."""
    X_tr, _, y_tr, _ = _subset(dados, features, split)
    train, test = validation_curve(
        DecisionTreeClassifier(random_state=RANDOM_STATE), X_tr, y_tr,
        param_name=param, param_range=values,
        groups=dados.grupos[dados.splits[split or CHOSEN[1]][0]],
        cv=StratifiedGroupKFold(CV_FOLDS, shuffle=True, random_state=RANDOM_STATE),
        n_jobs=-1,
    )
    return pd.DataFrame({"treino": train.mean(axis=1).round(3), "validação": test.mean(axis=1).round(3)})


def depth_curve(dados, depths=DEPTHS, features=None, split=None):
    """Acurácia de treino e de validação cruzada por profundidade máxima."""
    curve = _sweep(dados, "max_depth", depths, features, split)
    return curve.set_index(pd.Index(depths, name="profundidade"))


def pruning_curve(dados, alphas=ALPHAS, features=None, split=None):
    """Acurácia de treino e validação, número de folhas e profundidade por `ccp_alpha`."""
    curve = _sweep(dados, "ccp_alpha", alphas, features, split)
    X_tr, _, y_tr, _ = _subset(dados, features, split)
    shapes = [DecisionTreeClassifier(ccp_alpha=a, random_state=RANDOM_STATE).fit(X_tr, y_tr) for a in alphas]
    curve["folhas"] = [tree.get_n_leaves() for tree in shapes]
    curve["profundidade"] = [tree.get_depth() for tree in shapes]
    return curve.set_index(pd.Index(alphas, name="ccp_alpha"))


def tree_rules(model, dados, features=None, max_depth=2):
    """Regras das primeiras camadas da árvore em texto; os ramos cortados saem marcados."""
    return export_text(model, feature_names=FEATURE_SETS[features or CHOSEN[0]], max_depth=max_depth)


def importances(model, dados, features=None, split=None, n_repeats=10):
    """Importância por impureza e por permutação (média e desvio), medidas no conjunto de teste."""
    _, X_te, _, y_te = _subset(dados, features, split)
    perm = permutation_importance(model, X_te, y_te, n_repeats=n_repeats, random_state=RANDOM_STATE, n_jobs=-1)
    return pd.DataFrame({
        "impureza": model.feature_importances_,
        "permutação": perm.importances_mean,
        "desvio": perm.importances_std,
    }, index=list(X_te.columns)).sort_values("permutação")


def evaluation(model, dados, features=None, split=None):
    """Devolve (relatório por classe com precisão, recall e F1; matriz de confusão em contagem)."""
    _, X_te, _, y_te = _subset(dados, features, split)
    predicted = model.predict(X_te)
    report = pd.DataFrame(classification_report(y_te, predicted, output_dict=True, zero_division=0)).T
    report = report.rename(columns={"precision": "precisão", "recall": "revocação", "f1-score": "F1", "support": "linhas"})
    matrix = pd.DataFrame(
        confusion_matrix(y_te, predicted, labels=CLASSES),
        index=pd.Index(CLASSES, name="classe real"),
        columns=pd.Index(CLASSES, name="classe prevista"),
    )
    return report.loc[CLASSES + ["accuracy", "macro avg"]].round(3), matrix


def reference_models(dados, features=None, split=None):
    """Piso (`DummyClassifier`) e teto (Random Forest, HistGradientBoosting) no mesmo split da árvore."""
    X_tr, X_te, y_tr, y_te = _subset(dados, features, split)
    candidates = {
        "Dummy (classe majoritária)": DummyClassifier(strategy="most_frequent"),
        "Random Forest (300 árvores)": RandomForestClassifier(n_estimators=300, random_state=RANDOM_STATE, n_jobs=-1),
        "HistGradientBoosting": HistGradientBoostingClassifier(random_state=RANDOM_STATE),
    }
    rows = []
    for name, model in candidates.items():
        predicted = model.fit(X_tr, y_tr).predict(X_te)
        rows.append({
            "modelo": name,
            "acurácia teste": round(accuracy_score(y_te, predicted), 3),
            "F1 macro teste": round(f1_score(y_te, predicted, average="macro"), 3),
        })
    return pd.DataFrame(rows).set_index("modelo")
