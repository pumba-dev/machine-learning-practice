"""Configuração central da atividade 4: caminhos, colunas e constantes."""
from pathlib import Path

# Caminhos
ROOT = Path(__file__).resolve().parent.parent
RAW_CSV = ROOT / "data" / "raw" / "adult.csv"
PROCESSED_CSV = ROOT / "data" / "processed" / "renda.csv"
RESULTS_DIR = ROOT / "resultados"

# Impressão digital do CSV baixado do Kaggle (uciml/adult-census-income, arquivo de 2019).
# O conteúdo é o mesmo do adult.data da UCI, com cabeçalho e as linhas em outra ordem.
RAW_SHA256 = "250E154ED75714AE57A564926D66C6319CD6AAC1BCD32774CC76841A88D74E53"

# Alvo: 1 para quem ganha mais de 50 mil dólares por ano (">50K"), 0 para "<=50K"
TARGET = "income"
POSITIVO = ">50K"

# Atributos usados pelos modelos
NUMERICAS = ["age", "education.num", "capital.gain", "capital.loss", "hours.per.week"]
CATEGORICAS = ["workclass", "marital.status", "occupation", "relationship", "native.country"]
FEATURES = NUMERICAS + CATEGORICAS

# Atributos sensíveis: ficam na base para a análise exploratória e para conferir os erros
# por grupo depois da previsão, mas não entram nos modelos.
SENSIVEIS = ["race", "sex"]

# Removidas na curadoria: fnlwgt é o peso amostral do censo (não descreve a pessoa) e
# education repete education.num em texto.
REMOVIDAS = ["fnlwgt", "education"]

# Nomes em português para gráficos, tabelas e relatório. Os dados e o código mantêm os
# nomes originais, para que tudo possa ser rastreado até o CSV.
NOMES = {
    "age": "idade",
    "workclass": "classe de trabalho",
    "fnlwgt": "peso amostral",
    "education": "escolaridade",
    "education.num": "anos de estudo",
    "marital.status": "estado civil",
    "occupation": "ocupação",
    "relationship": "relacionamento",
    "race": "raça",
    "sex": "sexo",
    "capital.gain": "ganho de capital",
    "capital.loss": "perda de capital",
    "hours.per.week": "horas por semana",
    "native.country": "país de origem",
    "income": "renda >50K",
}

# Modelagem (mesmo protocolo da atividade 3)
TEST_SIZE = 0.2
CV_FOLDS = 5
RANDOM_STATE = 42
SEEDS = list(range(10))
