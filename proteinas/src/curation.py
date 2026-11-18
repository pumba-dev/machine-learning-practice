"""Etapas 5 e 7: curadoria das atividades e montagem da base final.

A sequência é:
1. `apply_quality_filters`   remove medições suspeitas, duplicadas ou sem estrutura
2. `aggregate_pairs`         uma linha por par molécula-alvo, com a mediana do pChEMBL
3. `select_active`           mantém só pares com pChEMBL >= limiar
4. `remove_multi_target`     remove moléculas ativas em mais de um alvo
5. `build_final_dataset`     junta os descritores e salva a base final
"""
import pandas as pd

from src.config import ACTIVE_THRESHOLD, CLASSES, FEATURES, FINAL_CSV, PROPERTY_COLUMNS


def apply_quality_filters(activities):
    """Devolve (atividades válidas, relatório de quantas linhas cada filtro removeu)."""
    flagged = activities["data_validity_comment"].notna()
    duplicate = activities["potential_duplicate"] == 1
    no_smiles = activities["canonical_smiles"].isna()
    valid = activities[~(flagged | duplicate | no_smiles)]
    report = pd.Series({
        "atividades brutas": len(activities),
        "removidas: data_validity_comment": flagged.sum(),
        "removidas: potential_duplicate": duplicate.sum(),
        "removidas: sem SMILES": no_smiles.sum(),
        "atividades válidas": len(valid),
    }).to_frame("linhas")
    return valid, report


def aggregate_pairs(valid):
    """Resume as medições de cada par molécula-alvo pela mediana do pChEMBL."""
    return (
        valid.groupby(["molecule_chembl_id", "protein"])
        .agg(
            canonical_smiles=("canonical_smiles", "first"),
            pchembl=("pchembl_value", "median"),
            medicoes=("pchembl_value", "size"),
        )
        .reset_index()
    )


def active_share_by_threshold(pairs, thresholds=(5, 6, 7)):
    """Percentual de pares que seriam considerados ativos em cada limiar, por alvo."""
    return pd.DataFrame({
        f"% com pChEMBL ≥ {threshold}": pairs.groupby("protein")["pchembl"].apply(lambda s: (s >= threshold).mean() * 100).round(1)
        for threshold in thresholds
    }).reindex(CLASSES)


def select_active(pairs, threshold=ACTIVE_THRESHOLD):
    """Pares molécula-alvo com pChEMBL mediano >= limiar."""
    return pairs[pairs["pchembl"] >= threshold]


def multi_target_summary(active):
    """Combinações de alvos das moléculas ativas em mais de um alvo."""
    targets_per_molecule = active.groupby("molecule_chembl_id")["protein"].nunique()
    multi = active[active["molecule_chembl_id"].isin(targets_per_molecule[targets_per_molecule > 1].index)]
    print("moléculas ativas em mais de um alvo:", multi["molecule_chembl_id"].nunique())
    return multi.groupby("molecule_chembl_id")["protein"].apply(lambda s: " + ".join(sorted(s))).value_counts().to_frame("moléculas")


def remove_multi_target(active):
    """Mantém só moléculas ativas em exatamente um alvo (rótulo único)."""
    targets_per_molecule = active.groupby("molecule_chembl_id")["protein"].transform("nunique")
    return active[targets_per_molecule == 1].reset_index(drop=True)


def build_final_dataset(single, properties, path=FINAL_CSV):
    """Junta descritores às moléculas, renomeia colunas para o padrão da base e salva o CSV final."""
    final = (
        single.merge(properties, on="molecule_chembl_id", how="left")
        .rename(columns={"molecule_chembl_id": "ChEMBL ID", "canonical_smiles": "SMILES", "pchembl": "pChEMBL", "protein": "Protein", **PROPERTY_COLUMNS})
        [["ChEMBL ID", "SMILES", *FEATURES, "pChEMBL", "Protein"]]
        .sort_values(by="ChEMBL ID")
        .reset_index(drop=True)
    )
    final["pChEMBL"] = final["pChEMBL"].round(2)
    path.parent.mkdir(parents=True, exist_ok=True)
    final.to_csv(path, index=False)
    return final


def compare_with_kaggle(kaggle, final):
    """Nas moléculas presentes nas duas bases: quantas, se o rótulo coincide e % de descritores iguais."""
    overlap = kaggle.merge(final, on="ChEMBL ID", suffixes=("_kaggle", ""))
    matches = pd.Series({
        feature: ((overlap[f"{feature}_kaggle"] - overlap[feature]).abs() <= 0.011).mean() * 100
        for feature in FEATURES
    }).round(1).to_frame("% igual ao Kaggle").T
    print("moléculas em comum:", len(overlap), "de", len(kaggle))
    print("mesmo rótulo:", f"{(overlap['Protein_kaggle'] == overlap['Protein']).mean():.1%}")
    return matches
