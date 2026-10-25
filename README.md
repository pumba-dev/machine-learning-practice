# Machine Learning Practice: classificação de alvos moleculares com Decision Tree

Projeto de prática de Machine Learning. O objetivo é prever **em qual proteína-alvo uma molécula é ativa** a partir de 5 propriedades físico-químicas, usando Decision Tree.

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
  01_curadoria_e_eda.ipynb   download, curadoria, decisões e análise exploratória
src/            código usado pelos notebooks, um módulo por etapa
```

| Módulo | Conteúdo |
|---|---|
| `src/config.py` | Caminhos, alvos, filtros e constantes |
| `src/chembl_api.py` | Cliente da API do ChEMBL |
| `src/download.py` | Download com cache em `data/raw/` |
| `src/inspection.py` | Inspeção das atividades brutas |
| `src/curation.py` | Curadoria e montagem da base final |
| `src/descriptors.py` | Comparação RDKit × ChEMBL |
| `src/eda.py` | Tabelas da análise exploratória |
| `src/plots.py` | Gráficos |

## Como executar

Testado com Python 3.13.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Linux/macOS: .venv/bin/python
.venv/Scripts/python -m jupyter notebook notebooks/01_curadoria_e_eda.ipynb
```

Os dados já estão no repositório, então o notebook roda sem baixar nada. Para baixar tudo de novo do ChEMBL, mude `REFRESH = True` na primeira célula.

## Etapas

- [x] Curadoria da base e análise exploratória (`01_curadoria_e_eda.ipynb`)
- [ ] Treino e avaliação da Decision Tree

## Licença dos dados

Os dados do ChEMBL e do Kaggle são distribuídos sob [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).
