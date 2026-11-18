"""Configuração central do projeto: caminhos, alvos, filtros e constantes.

Qualquer valor usado em mais de uma etapa fica aqui, para que o notebook e os
módulos usem sempre a mesma definição.
"""
from pathlib import Path

# Caminhos
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

KAGGLE_CSV = RAW_DIR / "molecule_classification_dataset.csv"
ACTIVITIES_CSV = RAW_DIR / "chembl_activities.csv"
DOWNLOAD_INFO_JSON = RAW_DIR / "chembl_download_info.json"
PROPERTIES_CSV = RAW_DIR / "chembl_molecule_properties.csv"
FINAL_CSV = PROCESSED_DIR / "chembl_4targets.csv"

# Fontes
KAGGLE_DOWNLOAD_URL = "https://www.kaggle.com/api/v1/datasets/download/xjoannax88/multitarget-bioactivity-chembl"
KAGGLE_CSV_NAME = "molecule_classification_dataset.csv"
CHEMBL_HOST = "https://www.ebi.ac.uk"
CHEMBL_API = f"{CHEMBL_HOST}/chembl/api/data"

# Alvos
# A ordem define a ordem das classes em tabelas e gráficos.
TARGETS = {"EGFR": "CHEMBL203", "BACE1": "CHEMBL4822", "DRD2": "CHEMBL217", "HDAC1": "CHEMBL325"}
CLASSES = list(TARGETS)

# Download das atividades: só ensaios de ligação, valor exato e pChEMBL preenchido
ACTIVITY_FILTERS = {"assay_type": "B", "standard_relation": "=", "pchembl_value__isnull": "false"}
ACTIVITY_FIELDS = [
    "activity_id", "molecule_chembl_id", "canonical_smiles", "target_chembl_id", "assay_chembl_id",
    "assay_type", "standard_type", "standard_relation", "standard_value", "standard_units",
    "pchembl_value", "data_validity_comment", "potential_duplicate",
]

# Propriedades do ChEMBL e o nome que recebem na base final
PROPERTY_COLUMNS = {"full_mwt": "Molecular Weight", "alogp": "LogP", "hba": "HBA", "hbd": "HBD", "psa": "TPSA"}
FEATURES = list(PROPERTY_COLUMNS.values())

# Curadoria
ACTIVE_THRESHOLD = 6.0  # pChEMBL >= 6 equivale a potência de 1 µM ou melhor

# Modelagem
TEST_SIZE = 0.2
CV_FOLDS = 5
# Colunas contadas a partir do texto do SMILES (ver modeling.smiles_features).
SMILES_FEATURES = [
    "smiles_len", "n_N", "n_O", "n_S", "n_halogen", "n_rings",
    "n_branch", "n_aromatic", "n_double", "n_triple", "n_charge", "n_stereo",
]
# Os três conjuntos de features comparados no notebook 03.
FEATURE_SETS = {
    "descritores": FEATURES,
    "descritores + SMILES": FEATURES + SMILES_FEATURES,
    "só SMILES": SMILES_FEATURES,
}

RANDOM_STATE = 42
