"""Configuração central da atividade 3: caminhos, colunas e constantes."""
from pathlib import Path

# Caminhos
ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT / "data" / "raw" / "loan_approval_dataset.csv"
PROCESSED_CSV = ROOT / "data" / "processed" / "emprestimos.csv"

# Impressão digital do CSV baixado do Kaggle (versão 1, de 16/07/2023)
RAW_SHA256 = "4B5CD093D178378F4CFA8C107ADB6E599B88BE9D8A3B51F3B99C0D5914154E54"

# Colunas
ID = "loan_id"
TARGET = "loan_status"
FEATURES = [
    "no_of_dependents", "education", "self_employed", "income_annum", "loan_amount",
    "loan_term", "cibil_score", "residential_assets_value", "commercial_assets_value",
    "luxury_assets_value", "bank_asset_value",
]

# Modelagem
TEST_SIZE = 0.2
CV_FOLDS = 5
RANDOM_STATE = 42
SEEDS = list(range(10))
