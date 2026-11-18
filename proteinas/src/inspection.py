"""Etapa 4: tabelas de inspeção das atividades brutas, antes de qualquer filtro."""
import pandas as pd

from src import chembl_api
from src.config import ACTIVITY_FILTERS, CLASSES, TARGETS


def activity_funnel(targets=TARGETS):
    """Quantas atividades cada filtro do download mantém, por alvo (consulta a API ao vivo)."""
    steps = {
        "todas as atividades": {},
        "+ ensaio de ligação (B)": {"assay_type": "B"},
        "+ relação '='": {"assay_type": "B", "standard_relation": "="},
        "+ pChEMBL preenchido": ACTIVITY_FILTERS,
    }
    return pd.DataFrame({
        protein: {step: chembl_api.count_activities(target_id, **filters) for step, filters in steps.items()}
        for protein, target_id in targets.items()
    })


def activity_overview(activities):
    """Atividades, moléculas e ensaios distintos por alvo."""
    return activities.groupby("protein").agg(
        atividades=("activity_id", "size"),
        moleculas=("molecule_chembl_id", "nunique"),
        ensaios=("assay_chembl_id", "nunique"),
        pchembl_mediano=("pchembl_value", "median"),
    ).reindex(CLASSES)


def standard_type_table(activities, top=8):
    """Tipos de medição (IC50, Ki etc.) por alvo, ordenados pelo total."""
    types = pd.crosstab(activities["standard_type"], activities["protein"])[CLASSES]
    return types.assign(total=types.sum(axis=1)).sort_values("total", ascending=False).head(top)


def quality_flags_table(activities):
    """Sinalizações de qualidade do ChEMBL por alvo."""
    by_protein = activities.groupby("protein")
    return pd.DataFrame({
        "data_validity_comment preenchido": by_protein["data_validity_comment"].count(),
        "potential_duplicate = 1": by_protein["potential_duplicate"].sum(),
        "sem SMILES": by_protein["canonical_smiles"].size() - by_protein["canonical_smiles"].count(),
    }).reindex(CLASSES)


def repeated_measurements_summary(activities):
    """Quantos pares molécula-alvo têm mais de uma medição e quanto essas medições divergem."""
    repeats = activities.groupby(["molecule_chembl_id", "protein"])["pchembl_value"].agg(["size", "min", "max"])
    spread = repeats["max"] - repeats["min"]
    return pd.Series({
        "pares molécula-alvo": len(repeats),
        "pares com mais de 1 medição": (repeats["size"] > 1).sum(),
        "máximo de medições num par": repeats["size"].max(),
        "pares com amplitude > 1 unidade de pChEMBL": (spread > 1).sum(),
    }).to_frame("valor")
