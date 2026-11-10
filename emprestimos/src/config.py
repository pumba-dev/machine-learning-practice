"""Configuração central da atividade 3: caminhos, colunas e constantes."""
from pathlib import Path

# Caminhos
ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT / "data" / "raw" / "loan_approval_dataset.csv"
PROCESSED_CSV = ROOT / "data" / "processed" / "emprestimos.csv"
RESULTS_DIR = ROOT / "resultados"

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

# Nomes em português para gráficos, tabelas e relatório. Os dados e o código mantêm os
# nomes originais do Kaggle, para que tudo possa ser rastreado até o CSV.
NOMES = {
    "no_of_dependents": "dependentes",
    "education": "graduado",
    "self_employed": "autônomo",
    "income_annum": "renda anual",
    "loan_amount": "valor do empréstimo",
    "loan_term": "prazo (anos)",
    "cibil_score": "score de crédito",
    "residential_assets_value": "patrimônio residencial",
    "commercial_assets_value": "patrimônio comercial",
    "luxury_assets_value": "bens de luxo",
    "bank_asset_value": "saldo bancário",
    "loan_status": "aprovado",
}
# Colunas em dinheiro (provavelmente rúpias; a página do Kaggle não informa a moeda).
DINHEIRO = [
    "income_annum", "loan_amount", "residential_assets_value", "commercial_assets_value",
    "luxury_assets_value", "bank_asset_value",
]

# Modelagem
TEST_SIZE = 0.2
CV_FOLDS = 5
RANDOM_STATE = 42
SEEDS = list(range(10))
