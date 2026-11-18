# MultiTarget Bioactivity ChEMBL

Base de moléculas extraídas do [ChEMBL](https://www.ebi.ac.uk/chembl/) e rotuladas pela proteína-alvo em que são ativas. Cada linha é uma molécula descrita por cinco propriedades físico-químicas. O objetivo de modelagem é prever a proteína-alvo (`Protein`) a partir dessas propriedades, usando Decision Tree.

A base foi inspirada no dataset do Kaggle [xjoannax88/multitarget-bioactivity-chembl](https://www.kaggle.com/datasets/xjoannax88/multitarget-bioactivity-chembl). O arquivo publicado lá está incompleto (ver [Base original do Kaggle](#base-original-do-kaggle)), então a base foi reconstruída direto da API do ChEMBL.

## Origem

| Item | Valor |
|---|---|
| Fonte | API REST do ChEMBL (`https://www.ebi.ac.uk/chembl/api/data/`) |
| Versão do ChEMBL | ChEMBL_37 (lançada em 2026-05-01) |
| Data da extração | 2026-10-24 |
| Licença dos dados | CC BY-SA 3.0 |

## Arquivos

| Arquivo | Conteúdo | Linhas | SHA-256 |
|---|---|---|---|
| `data/raw/chembl_activities.csv` | Medições de atividade brutas, uma por linha | 58.736 | `558b6ffacf484ceb7cdd4b9c72bd4bbf1cfd22c4092208f2e0ab24cfc22f97e3` |
| `data/raw/chembl_download_info.json` | Versão do ChEMBL, data do download, alvos e filtros usados | - | - |
| `data/raw/chembl_molecule_properties.csv` | Propriedades das moléculas (cache da API) | 27.714 | `7d252e2edb53e255be6ec90ab0c164c0c0e46ca0bdaab1f0e80e3d89c18fad8c` |
| `data/processed/chembl_4targets.csv` | **Base final para modelagem**, uma molécula por linha | 27.714 | `8f951498153e1f5e52ab5ed6575580eb02394fb9865bc2cb53778ab396363c6b` |
| `data/raw/molecule_classification_dataset.csv` | CSV original do Kaggle, mantido só para referência | 1.333 | `c373e3fd1771adcf602139595aba614581f055da57b214193f1d478ea228a0a2` |

## Como reproduzir

O processo está em dois notebooks: [`notebooks/01_curadoria.ipynb`](notebooks/01_curadoria.ipynb) (download e curadoria) e [`notebooks/02_analise_exploratoria.ipynb`](notebooks/02_analise_exploratoria.ipynb) (análise exploratória) e [`notebooks/03_decision_tree.ipynb`](notebooks/03_decision_tree.ipynb) (treino e avaliação da árvore). Os notebooks só chamam funções; a implementação fica no pacote `src/`, com um módulo por etapa:

| Módulo | Conteúdo |
|---|---|
| `src/config.py` | Caminhos, alvos, filtros e constantes |
| `src/chembl_api.py` | Cliente da API do ChEMBL |
| `src/download.py` | Download com cache em `data/raw/` |
| `src/inspection.py` | Inspeção das atividades brutas |
| `src/curation.py` | Curadoria e montagem da base final |
| `src/eda.py` | Tabelas da análise exploratória |
| `src/modeling.py` | Features, splits, ajuste e avaliação da árvore |
| `src/plots.py` | Gráficos |

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m jupyter notebook notebooks/
```

O notebook 01 salva os downloads em `data/raw/` e os reaproveita nas execuções seguintes. Para baixar tudo de novo, mude `REFRESH` para `True` na célula de configuração. A primeira execução faz cerca de 360 requisições à API do ChEMBL.

## Pipeline de construção

1. **Download das atividades** (notebook 01, seção 3; `download.load_activities`). Para cada alvo, baixa as medições que atendem a todos estes critérios:
   - `assay_type = B`: ensaio de ligação (binding).
   - `standard_relation = "="`: valor exato, sem `<` ou `>`.
   - `pchembl_value` preenchido: potência padronizada (IC50, Ki, Kd, EC50 etc. convertidos para -log10 molar).
2. **Filtros de qualidade** (notebook 01, seção 5; `curation.apply_quality_filters`). Remove medições com `data_validity_comment` preenchido (dado marcado como suspeito pelo ChEMBL) ou com `potential_duplicate` ativo. Restam 51.359 medições.
3. **Agregação.** Calcula a mediana do pChEMBL de cada par molécula-alvo.
4. **Seleção de ativos.** Mantém só pares com pChEMBL >= 6 (potência de 1 µM ou melhor). Restam 27.798 pares.
5. **Remoção de rótulos ambíguos.** Remove 42 moléculas ativas em mais de um alvo, porque uma molécula precisa ter uma única classe.
6. **Descritores.** Busca `molecule_properties` de cada molécula na API (`full_mwt`, `alogp`, `hba`, `hbd`, `psa`). O ChEMBL calcula esses valores sobre a molécula parental, sem sal nem contraíon. É a mesma fonte do CSV do Kaggle: nas 525 moléculas em comum, os valores batem em 99,4% das linhas (as diferenças são linhas sem descritor).

## Visão geral

| Item | Valor |
|---|---|
| Linhas | 27.714 (uma por molécula) |
| Colunas | 9 (2 identificadores/texto, 5 features, 1 informativa, 1 alvo) |
| Tarefa | Classificação multiclasse |
| Alvo | `Protein` |
| Classes | 4 (EGFR, BACE1, DRD2, HDAC1) |
| Linhas com descritor faltante | 238 (0,86%) |

## Dicionário de atributos

| Coluna | Tipo | Papel | Descrição | Faltantes |
|---|---|---|---|---|
| `ChEMBL ID` | texto | identificador | ID da molécula no ChEMBL (ex.: `CHEMBL303519`). Único por linha. Página da molécula: `https://www.ebi.ac.uk/chembl/compound_report_card/<ID>`. | 0 |
| `SMILES` | texto | opcional | Estrutura da molécula em notação SMILES canônica. A árvore não usa texto direto, mas é possível gerar fingerprints a partir dele. | 0 |
| `Molecular Weight` | float | feature | Massa molecular completa, em Dalton (g/mol). Campo `full_mwt` do ChEMBL. | 0 |
| `LogP` | float | feature | Coeficiente de partição octanol/água calculado (campo `alogp`). Mede lipofilicidade: valor alto indica molécula mais "gordurosa" e menos solúvel em água. | 238 |
| `HBA` | inteiro (salvo como float) | feature | Número de aceptores de ligação de hidrogênio. | 238 |
| `HBD` | inteiro (salvo como float) | feature | Número de doadores de ligação de hidrogênio. | 238 |
| `TPSA` | float | feature | Área de superfície polar topológica, em Å² (campo `psa`). Relacionada a permeabilidade de membrana. | 238 |
| `pChEMBL` | float | **não usar como feature** | Mediana da potência da molécula no alvo (-log10 molar). Serve para análise exploratória. Depende do alvo medido, então usar como feature vaza informação do rótulo. | 0 |
| `Protein` | texto | **alvo** | Proteína-alvo em que a molécula é ativa. | 0 |

`HBA` e `HBD` são contagens inteiras, mas o pandas lê como `float64` por causa dos valores faltantes.

## Estatísticas das features

Calculadas sobre as linhas sem valor faltante na coluna.

| Feature | Mín. | 1º quartil | Mediana | Média | 3º quartil | Máx. |
|---|---|---|---|---|---|---|
| Molecular Weight | 127,14 | 398,22 | 453,63 | 469,20 | 518,68 | 3.771,26 |
| LogP | -3,83 | 3,13 | 3,98 | 4,02 | 4,85 | 14,00 |
| HBA | 0 | 5 | 6 | 6,11 | 7 | 18 |
| HBD | 0 | 1 | 2 | 2,07 | 3 | 13 |
| TPSA | 3,24 | 67,40 | 89,60 | 90,35 | 110,77 | 404,94 |
| pChEMBL | 6,00 | 6,61 | 7,21 | 7,32 | 7,92 | 11,00 |

## Variável alvo: `Protein`

| Classe | ChEMBL ID | Tipo de proteína | Relevância | Linhas | % |
|---|---|---|---|---|---|
| EGFR | CHEMBL203 | Quinase (receptor tirosina-quinase) | Receptor do fator de crescimento epidérmico. Alvo em câncer de pulmão. | 8.108 | 29,3% |
| BACE1 | CHEMBL4822 | Enzima (protease aspártica) | Beta-secretase 1. Alvo em Alzheimer. | 7.344 | 26,5% |
| DRD2 | CHEMBL217 | Receptor acoplado à proteína G (GPCR) | Receptor de dopamina D2. Alvo de antipsicóticos. | 6.650 | 24,0% |
| HDAC1 | CHEMBL325 | Enzima (histona desacetilase) | Regulação epigenética. Alvo em oncologia. | 5.612 | 20,2% |

As classes estão razoavelmente balanceadas. Um modelo que sempre responde a classe majoritária (EGFR) acerta 29,3%.

> **ID do BACE1.** A página do Kaggle cita `CHEMBL1987` para BACE1, mas esse ID é o receptor de prostaglandina F2-alfa. O ID correto da beta-secretase 1 humana é `CHEMBL4822`.

### Medianas por classe

| Classe | Molecular Weight | LogP | HBA | HBD | TPSA | pChEMBL |
|---|---|---|---|---|---|---|
| BACE1 | 452,93 | 3,41 | 6 | 2 | 99,55 | 7,35 |
| DRD2 | 434,46 | 4,13 | 5 | 1 | 54,46 | 6,95 |
| EGFR | 497,60 | 4,60 | 7 | 2 | 97,84 | 7,48 |
| HDAC1 | 430,44 | 3,68 | 6 | 3 | 100,55 | 7,04 |

Leituras iniciais:

- DRD2 se destaca por `TPSA` baixa e `HBD` baixo. Ligantes de receptores no cérebro tendem a ser menos polares.
- EGFR tem as moléculas mais pesadas e mais lipofílicas.
- HDAC1 tem o maior `HBD`. Muitos inibidores de HDAC têm grupo ácido hidroxâmico (`-C(=O)NHOH`).
- BACE1 e HDAC1 têm `TPSA` parecida. A árvore deve depender de `LogP` e `HBD` para separar essas duas.

## Problemas de qualidade

1. **Valores faltantes (238 linhas, 0,86%).** Essas linhas têm `Molecular Weight`, mas não têm `LogP`, `HBA`, `HBD` nem `TPSA`. A maioria são moléculas grandes (mediana de 1.103 Da), como peptídeos, para as quais o ChEMBL não calcula esses descritores. Distribuição por classe: DRD2 116, EGFR 49, HDAC1 43, BACE1 30.
2. **Descritores repetidos.** Não há `ChEMBL ID` duplicado. Porém 4.777 linhas completas repetem exatamente os 5 descritores de outra linha (isômeros e análogos próximos). Todas as repetições são da mesma classe.
3. **SMILES duplicado.** `CHEMBL3260841` e `CHEMBL3652433` têm o mesmo SMILES e a mesma classe (BACE1).
4. **Outliers.** 182 moléculas passam de 1.000 Da (máximo de 3.771 Da) e há `LogP` até 14. A árvore lida bem com outliers, então não é preciso removê-los.
5. **Viés de seleção.** A base só tem moléculas ativas (pChEMBL >= 6). O modelo aprende a distinguir entre alvos, não a distinguir molécula ativa de inativa.

## Implicações para Decision Tree

- **Features:** `Molecular Weight`, `LogP`, `HBA`, `HBD` e `TPSA`. Todas numéricas, sem necessidade de encoding ou normalização.
- **Descartar:** `ChEMBL ID`, `SMILES` (a menos que vire fingerprint) e `pChEMBL`.
- **Faltantes:** remover as 238 linhas é a opção mais simples (perde 0,86% da base).
- **Divisão:** usar `train_test_split(..., stratify=y, shuffle=True)`. O arquivo está ordenado por `ChEMBL ID`, não por classe.
- **Métricas:** acurácia é aceitável porque as classes estão balanceadas. Reportar também F1 macro e matriz de confusão.
- **Expectativa:** só 5 descritores globais para separar 4 alvos. Haverá sobreposição entre classes, principalmente BACE1 e HDAC1. Fingerprints de SMILES são o próximo passo natural se a árvore ficar limitada.

## Base original do Kaggle

O CSV do Kaggle (`data/raw/molecule_classification_dataset.csv`, versão 17, atualizada em 2026-09-28) não bate com a descrição da própria página:

| | Descrição no Kaggle | Arquivo real |
|---|---|---|
| Moléculas | 8.711 | 1.333 |
| Alvos | 4 (EGFR, DRD2, BACE1, HDAC1) | 3, sem nenhuma linha de EGFR |
| Distribuição | não informada | DRD2 95,5%, HDAC1 4,4%, BACE1 2 linhas |

Outros problemas do arquivo original:

- Tem uma coluna de índice sem nome e uma coluna `Name` vazia em 90,5% das linhas.
- 10 linhas de DRD2 não têm descritores.
- As linhas estão ordenadas por classe.
- O zip também traz uma pasta `tmp/` com nove imagens `df_00X.png`, que não fazem parte dos dados.

As versões anteriores não estão disponíveis para download sem login. Por isso a base foi reconstruída do zero.
