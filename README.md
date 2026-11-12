# Machine Learning Practice: árvores e redes neurais em duas tarefas de classificação

Projeto de prática de Machine Learning, em três partes:

1. **Árvore de decisão:** prever **em qual proteína-alvo uma molécula é ativa** a partir de 5 propriedades físico-químicas.
2. **Comparação de modelos:** a mesma tarefa com Random Tree, Random Forest e Gradient Boosting.
3. **Rede neural:** prever **se um pedido de empréstimo é aprovado** com um MLP, comparado com a árvore de decisão e modelos de referência, incluindo o tempo de execução ([seção própria](#parte-3-rede-neural-na-aprovação-de-empréstimos)).

As seções a seguir, até "Resultado", tratam das partes 1 e 2.

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
emprestimos/    terceira parte, autocontida (detalhes na seção da parte 3):
  data/         loan_approval_dataset.csv (bruto, do Kaggle) e emprestimos.csv (processado)
  notebooks/    01_curadoria, 02_analise_exploratoria, 03_referencias, 04_rede_neural
  src/          config.py, avaliacao.py (protocolo e tempos), rede.py (MLP, grade e curvas por época)
  resultados/   referencias.csv e rede.csv, uma linha por seed e modelo
report/         relatório (LaTeX, formato SBC), figuras e tabelas geradas
scripts/        multiseed.py, tabelas e figuras do relatório, montagem dos slides
slides/         apresentacao.pptx (primeira parte, árvore de decisão),
                apresentacao_random_tree.pptx (segunda parte, comparação de modelos) e
                apresentacao_redes_neurais.pptx (terceira parte, rede neural), com roteiros em .md
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

Relatório e slides, a partir da raiz (os slides precisam de `python-pptx`; o PDF, do PowerPoint):

```bash
python scripts/results_tables.py      # tabelas e números do relatório (report/results/)
python scripts/export_figures.py      # figuras do relatório (report/figures/)
python scripts/slides_data.py && python scripts/build_slides.py          # primeira apresentação
python scripts/slides_rt_data.py && python scripts/build_slides_rt.py    # segunda apresentação
python scripts/rn_data.py && python scripts/rn_report.py                 # terceira parte: números, figuras e tabela
python scripts/build_slides_rn.py                                         # terceira apresentação
powershell -File scripts/export_slides_pdf.ps1 slides/apresentacao_random_tree.pptx
```

## Etapas

- [x] Etapa 1: curadoria da base (`01_curadoria.ipynb`)
- [x] Etapa 2: análise exploratória (`02_analise_exploratoria.ipynb`)
- [x] Etapa 3: treino e avaliação da Decision Tree (`03_decision_tree.ipynb`)
- [x] Etapa 4: Random Tree (`04_random_tree.ipynb`)
- [x] Etapa 5: Random Forest (`05_random_forest.ipynb`)
- [x] Etapa 6: Gradient Boosting (`06_gradient_boosting.ipynb`)
- [x] Etapa 7: comparação entre os modelos (`07_comparacao.ipynb`)
- [x] Parte 3: rede neural na base de empréstimos (`emprestimos/notebooks/01` a `04`)

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

## Parte 3: rede neural na aprovação de empréstimos

Base [Loan Approval Prediction](https://www.kaggle.com/datasets/architsharma01/loan-approval-prediction-dataset) do Kaggle (versão 1): 4.269 pedidos, 11 atributos, 62,2% aprovados. A curadoria tira os espaços dos nomes e valores, converte em 0/1 as duas colunas de texto e o alvo, e zera 28 valores negativos de patrimônio residencial.

| Notebook | O que faz |
|---|---|
| [`01_curadoria`](emprestimos/notebooks/01_curadoria.ipynb) | Confere o CSV, limpa e grava `emprestimos.csv` |
| [`02_analise_exploratoria`](emprestimos/notebooks/02_analise_exploratoria.ipynb) | Mostra que o score de crédito decide quase tudo: abaixo de 550, 10,4% de aprovação; acima, 99,5% |
| [`03_referencias`](emprestimos/notebooks/03_referencias.ipynb) | Define o protocolo e os pontos de referência: classe majoritária, regra de um corte, regressão logística, árvore e Random Forest |
| [`04_rede_neural`](emprestimos/notebooks/04_rede_neural.ipynb) | Rede neural: padronização, neurônios, épocas e paciência, busca em grade, comparação, tempo e erros |

**Protocolo.** 10 seeds; em cada uma, divisão estratificada 80/20 e busca de hiperparâmetros só no treino, com validação cruzada de 5 partes. A rede é um `MLPClassifier` (ReLU, Adam) num Pipeline com `StandardScaler`, com parada antecipada e paciência 30. A busca testa 24 combinações: 6 arquiteturas, 2 valores de regularização L2 e 2 taxas de aprendizado. Os tempos são medianas num único núcleo, com aquecimento descartado e a busca medida à parte.

Média de 10 seeds (`emprestimos/resultados/`):

| Modelo | Acurácia (%) | F1 macro (%) | AUC (%) | Treino | Busca por seed |
|---|---|---|---|---|---|
| Classe majoritária | 62,2 ± 0,0 | 38,3 | 50,0 | 0,2 ms | – |
| Regressão logística | 91,9 ± 1,1 | 91,3 | 97,0 | 3,5 ms | – |
| Regra de um corte (score) | 95,5 ± 0,6 | 95,3 | 96,2 | 1,9 ms | – |
| **Rede neural** | **96,4 ± 1,1** | **96,2** | **99,3** | 183 ms | 23,5 s |
| Árvore de decisão | 98,1 ± 0,5 | 98,0 | 98,7 | 3,7 ms | 0,65 s |
| Random Forest | 98,3 ± 0,4 | 98,2 | 99,8 | 490 ms | – |

- **Padronização é obrigatória.** Sem ela, a rede de 16 neurônios fica em 59,5% de acurácia e 51,0% de AUC, abaixo de chutar a classe majoritária. Com ela, sobe para 93,9%.
- **Paciência 10 para cedo demais.** Com a taxa 0,001, a parada antecipada encerra o treino na época 37 com 92,1% de validação, quando a rede ainda chegaria a 96,5%. Por isso usamos paciência 30 e pusemos a taxa na busca; a taxa 0,01 venceu nas 10 seeds.
- **Duas camadas ocultas.** A busca escolheu 32-16 (11 → 32 → 16 → 1) em 7 seeds, 64-32 em 2 e uma camada de 8 neurônios em 1.
- **A rede supera a logística em todas as seeds, mas perde para a árvore em todas.** O motivo é a forma da regra: a aprovação cai como um degrau em score 550. A árvore representa isso com um corte; a rede desenha uma rampa e erra perto do degrau. Pela AUC, a rede ordena os pedidos melhor que a árvore; o que ela erra é o corte em 50%.
- **Custo.** Treinar a rede final leva ~50 vezes o tempo de treinar a árvore. A busca de hiperparâmetros da rede (120 redes por seed) leva ~36 vezes o tempo da busca da árvore (150 árvores). Nas 10 seeds, só a busca da rede soma uns 4 minutos.

Para regerar os números, figuras e tabela do relatório e a terceira apresentação, use os comandos de [Como executar](#como-executar). O roteiro da fala está em [`slides/notas_redes_neurais.md`](slides/notas_redes_neurais.md).

## Licença dos dados

Os dados do ChEMBL e o dataset de moléculas do Kaggle são distribuídos sob [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). A base de empréstimos do Kaggle é distribuída sob licença MIT.
