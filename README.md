# Machine Learning Practice: classificação de alvos moleculares com árvores

Projeto de prática de Machine Learning. O objetivo é prever **em qual proteína-alvo uma molécula é ativa** a partir de 5 propriedades físico-químicas, usando Decision Tree, e comparar com Random Tree, Random Forest e Gradient Boosting.

## Base de dados

27.714 moléculas extraídas do [ChEMBL](https://www.ebi.ac.uk/chembl/) (versão 37), rotuladas em 4 classes:

| Classe | Proteína | Moléculas |
|---|---|---|
| EGFR | Receptor do fator de crescimento epidérmico | 8.108 (29,3%) |
| BACE1 | Beta-secretase 1 | 7.344 (26,5%) |
| DRD2 | Receptor de dopamina D2 | 6.650 (24,0%) |
| HDAC1 | Histona desacetilase 1 | 5.612 (20,2%) |

- **Features:** `Molecular Weight`, `LogP`, `HBA`, `HBD`, `TPSA`.
- **Alvo:** `Protein`.

A base foi inspirada no dataset do Kaggle [MultiTarget Bioactivity ChEMBL](https://www.kaggle.com/datasets/xjoannax88/multitarget-bioactivity-chembl). O CSV publicado lá está incompleto (1.333 linhas, sem EGFR, 95,5% DRD2), então a base foi reconstruída direto da API do ChEMBL.

Dicionário de atributos, origem, hashes e problemas de qualidade: [`DATASET.md`](DATASET.md).

## Estrutura

```
data/
  raw/          dados brutos baixados (ChEMBL e CSV original do Kaggle)
  processed/    chembl_4targets.csv, a base final para modelagem
notebooks/
  01_curadoria.ipynb              etapa 1: download e curadoria
  02_analise_exploratoria.ipynb   etapa 2: análise exploratória da base final
  03_decision_tree.ipynb          etapa 3: treino, ajuste e avaliação da árvore
  04_random_tree.ipynb            etapa 4: Random Tree (RandomTree do Weka)
  05_random_forest.ipynb          etapa 5: Random Forest
  06_gradient_boosting.ipynb      etapa 6: gradient boosting por histogramas
  07_comparacao.ipynb             etapa 7: todos os modelos com 10 seeds e experimento-ponte
scripts/        multiseed.py repete o ajuste de todos os modelos com 10 seeds
src/            código usado pelos notebooks, um módulo por etapa
```

| Módulo | Conteúdo |
|---|---|
| `src/config.py` | Caminhos, alvos, filtros e constantes |
| `src/chembl_api.py` | Cliente da API do ChEMBL |
| `src/download.py` | Download com cache em `data/raw/` |
| `src/inspection.py` | Inspeção das atividades brutas |
| `src/curation.py` | Curadoria e montagem da base final |
| `src/eda.py` | Tabelas da análise exploratória |
| `src/modeling.py` | Features, splits, ajuste e avaliação, comuns a todos os modelos |
| `src/random_tree.py` | Random Tree: padrão do Weka, curva de K, variância entre sementes |
| `src/random_forest.py` | Random Forest: grid e curva por número de árvores |
| `src/gradient_boosting.py` | Gradient boosting: grid e curva por iteração |
| `src/comparison.py` | Tabelas do multiseed e experimento-ponte |
| `src/plots.py` | Gráficos |

## Como executar

Testado com Python 3.13.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Linux/macOS: .venv/bin/python
.venv/Scripts/python -m jupyter notebook notebooks/
```

Rode os notebooks na ordem (01 a 07). O 07 lê `report/results/multiseed.csv`; para gerar de novo, rode `python scripts/multiseed.py` (cerca de 1 hora com 10 seeds). Os dados já estão no repositório, então nada precisa ser baixado. Para baixar tudo de novo do ChEMBL, mude `REFRESH = True` na primeira célula do notebook 01.

## Etapas

- [x] Etapa 1: curadoria da base (`01_curadoria.ipynb`)
- [x] Etapa 2: análise exploratória (`02_analise_exploratoria.ipynb`)
- [x] Etapa 3: treino e avaliação da Decision Tree (`03_decision_tree.ipynb`)
- [x] Etapa 4: Random Tree (`04_random_tree.ipynb`)
- [x] Etapa 5: Random Forest (`05_random_forest.ipynb`)
- [x] Etapa 6: Gradient Boosting (`06_gradient_boosting.ipynb`)
- [x] Etapa 7: comparação entre os modelos (`07_comparacao.ipynb`)

## Resultado

Todos os modelos usam as 5 propriedades físico-químicas mais 12 contagens de caracteres do `SMILES` e são avaliados num split que impede moléculas de descritores idênticos de cair nos dois lados. Média e desvio de 10 seeds (`scripts/multiseed.py`):

| Modelo | Acurácia (%) | F1 macro (%) |
|---|---|---|
| Chutar a classe majoritária | 29,3 ± 0,0 | 11,3 |
| **Árvore de decisão** | **89,4 ± 0,4** | **89,3** |
| Random Tree, padrão do Weka | 87,6 ± 1,1 | 87,5 |
| Random Tree ajustada | 89,0 ± 0,7 | 88,9 |
| Bagging de 300 árvores | 93,8 ± 0,3 | 93,7 |
| Random Forest padrão | 95,2 ± 0,3 | 95,1 |
| Random Forest ajustada | 95,3 ± 0,3 | 95,2 |
| Gradient boosting padrão | 94,8 ± 0,3 | 94,7 |
| Gradient boosting ajustado | 96,6 ± 0,3 | 96,6 |

- As contagens de caracteres do `SMILES` valem cerca de 10 pontos de acurácia para a árvore, e sozinhas superam os 5 descritores ([`03_decision_tree.ipynb`](notebooks/03_decision_tree.ipynb)).
- A Random Tree sozinha perde para a árvore de decisão e varia mais com a semente: o sorteio de atributos esconde o melhor corte de cada nó ([`04_random_tree.ipynb`](notebooks/04_random_tree.ipynb)).
- Mesmo assim, é ela que faz a Random Forest funcionar. Cerca de 80% do ganho da floresta sobre a árvore vem da média de muitas árvores; o sorteio de atributos traz o resto, mas só dentro do conjunto ([`07_comparacao.ipynb`](notebooks/07_comparacao.ipynb)).
- O gradient boosting ajustado é o mais preciso. A Random Forest não precisa de ajuste e é a única cuja confiança separa acertos de erros. Só a árvore de decisão tem regras legíveis.

## Licença dos dados

Os dados do ChEMBL e do Kaggle são distribuídos sob [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).
