"""Configuração central da base de renda (atividade 4, SVM): caminhos, colunas e constantes."""
from pathlib import Path

# Caminhos
ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT / "data" / "raw" / "adult.csv"
PROCESSED_CSV = ROOT / "data" / "processed" / "renda.csv"
RESULTS_DIR = ROOT / "resultados"

# Impressão digital do CSV baixado do Kaggle (uciml/adult-census-income, versão 3, de 07/10/2016)
RAW_SHA256 = "250E154ED75714AE57A564926D66C6319CD6AAC1BCD32774CC76841A88D74E53"

# Colunas
TARGET = "income"
#: Marca de valor ausente no CSV original.
AUSENTE = "?"
NUMERICOS = ["age", "education.num", "capital.gain", "capital.loss", "hours.per.week"]
CATEGORICOS = ["workclass", "marital.status", "occupation", "relationship", "race", "sex", "native.country"]
FEATURES = NUMERICOS + CATEGORICOS
#: Colunas que ficam na base processada, mas não entram nos modelos (motivo no notebook 01).
FORA = {
    "fnlwgt": "peso amostral do censo: quantas pessoas da população o registro representa",
    "education": "a mesma informação de education.num, em texto",
}

# Nomes em português para gráficos, tabelas e relatório. Os dados e o código mantêm os
# nomes originais, para que tudo possa ser rastreado até o CSV.
NOMES = {
    "age": "idade",
    "workclass": "tipo de vínculo",
    "fnlwgt": "peso amostral",
    "education": "escolaridade (texto)",
    "education.num": "nível de escolaridade",
    "marital.status": "estado civil",
    "occupation": "ocupação",
    "relationship": "papel na família",
    "race": "raça",
    "sex": "sexo",
    "capital.gain": "ganho de capital",
    "capital.loss": "perda de capital",
    "hours.per.week": "horas por semana",
    "native.country": "país de origem",
    "income": "renda acima de 50 mil",
}

# Modelagem
TEST_SIZE = 0.2
CV_FOLDS = 5
RANDOM_STATE = 42
SEEDS = list(range(10))
