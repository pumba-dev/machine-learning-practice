"""Etapa 6: comparação das fontes de descritores (RDKit local × ChEMBL)."""
import pandas as pd
from rdkit import Chem, rdBase
from rdkit.Chem import Descriptors, rdMolDescriptors

from src import chembl_api
from src.config import FEATURES, RANDOM_STATE

rdBase.DisableLog("rdApp.*")

TOLERANCE = 0.011  # os valores vêm arredondados em 2 casas


# Funções de rdMolDescriptors são as mesmas usadas por Crippen.MolLogP e Lipinski.NumHAcceptors/NumHDonors,
# mas declaradas nos stubs do RDKit (o Pylance não enxerga as versões definidas como lambda).
def rdkit_descriptors(smiles):
    """Os 5 descritores do projeto calculados localmente com RDKit a partir do SMILES."""
    mol = Chem.MolFromSmiles(smiles)
    return pd.Series({
        "Molecular Weight": Descriptors.MolWt(mol),  # pyright: ignore[reportAttributeAccessIssue]
        "LogP": rdMolDescriptors.CalcCrippenDescriptors(mol)[0],
        "HBA": rdMolDescriptors.CalcNumHBA(mol),
        "HBD": rdMolDescriptors.CalcNumHBD(mol),
        "TPSA": rdMolDescriptors.CalcTPSA(mol),
    })


def rdkit_match_rate(reference):
    """Devolve (descritores RDKit, % de linhas iguais ao `reference` por descritor)."""
    rdkit_values = reference["SMILES"].apply(rdkit_descriptors)
    match = ((rdkit_values - reference[FEATURES]).abs() <= TOLERANCE).mean().mul(100).round(1)
    return rdkit_values, match.to_frame("% igual ao Kaggle (RDKit)").T


def compare_sources_sample(reference, rdkit_values, n=4):
    """Amostra de moléculas em que o RDKit diverge, lado a lado com os valores publicados pelo ChEMBL."""
    mismatch = (rdkit_values["HBA"] != reference["HBA"]) | ((rdkit_values["LogP"] - reference["LogP"]).abs() > TOLERANCE)
    sample = reference[mismatch].sample(n, random_state=RANDOM_STATE)
    chembl_values = pd.DataFrame(
        [chembl_api.get_molecule_properties(molecule_id) for molecule_id in sample["ChEMBL ID"]],
        index=sample.index,
    )
    return pd.DataFrame({
        "ChEMBL ID": sample["ChEMBL ID"],
        "LogP Kaggle": sample["LogP"],
        "LogP RDKit": rdkit_values.loc[sample.index, "LogP"].round(2),
        "LogP ChEMBL": chembl_values["alogp"].astype(float),
        "HBA Kaggle": sample["HBA"],
        "HBA RDKit": rdkit_values.loc[sample.index, "HBA"],
        "HBA ChEMBL": chembl_values["hba"],
    })
