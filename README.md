# Prática de Machine Learning: duas bases, duas famílias de modelos

Trabalhos da disciplina de Aprendizagem de Máquina (PPGCC010, UFPI). Cada família de modelos é estudada numa base própria, escolhida para o tipo de problema que esses modelos resolvem:

| | Base 1: molécula → proteína | Base 2: cliente → empréstimo |
|---|---|---|
| Pergunta | A qual de 4 proteínas-alvo uma molécula está associada? | Um pedido de empréstimo foi aprovado? |
| Tarefa | Classificação multiclasse (4 classes) | Classificação binária |
| Origem | API do [ChEMBL](https://www.ebi.ac.uk/chembl/) (versão 37) | [Kaggle](https://www.kaggle.com/datasets/architsharma01/loan-approval-prediction-dataset) |
| Tamanho | 27.714 moléculas, 17 atributos | 4.269 pedidos, 11 atributos |
| Modelos estudados | Árvore de decisão e variações: Random Tree, Random Forest, Gradient Boosting | Redes neurais (MLP) e SVM |
| Pasta | [`proteinas/`](proteinas/) | [`emprestimos/`](emprestimos/) |

Cada pasta é autocontida: tem os dados, os notebooks, o código, os resultados, o relatório e os slides da sua base.

- [Base 1: moléculas e árvores de decisão](#base-1-moléculas-e-árvores-de-decisão)
- [Base 2: empréstimos, redes neurais e SVM](#base-2-empréstimos-redes-neurais-e-svm)
- [Como executar](#como-executar)

## Organização do repositório

As duas pastas seguem o mesmo formato:

```
proteinas/ ou emprestimos/
  data/raw/         dados como foram baixados
  data/processed/   base final, depois da curadoria
  notebooks/        análise passo a passo, numerada na ordem de execução
  src/              código que os notebooks chamam (os notebooks só chamam funções)
  report/           relatório em LaTeX (formato SBC), com main.pdf, figuras e tabelas geradas
  scripts/          geram os números, figuras e tabelas do relatório e montam os slides
  slides/           apresentações (.pptx e .pdf) e roteiros de fala (.md)
comum/              o que as apresentações das duas bases compartilham: slides_common.py,
                    template SBC e export_slides_pdf.ps1
```

---

## Base 1: moléculas e árvores de decisão

### Os dados

27.714 moléculas do ChEMBL 37, cada uma ativa (pChEMBL ≥ 6) contra exatamente uma de quatro proteínas:

| Classe | Proteína | Moléculas |
|---|---|---|
| EGFR | Receptor do fator de crescimento epidérmico | 8.108 (29,3%) |
| BACE1 | Beta-secretase 1 | 7.344 (26,5%) |
| DRD2 | Receptor de dopamina D2 | 6.650 (24,0%) |
| HDAC1 | Histona desacetilase 1 | 5.612 (20,2%) |

- **Atributos:** 5 descritores físico-químicos (`Molecular Weight`, `LogP`, `HBA`, `HBD`, `TPSA`) e 12 contagens de caracteres do `SMILES`, o texto que descreve a estrutura da molécula.
- **Alvo:** `Protein`.

A base foi inspirada no dataset do Kaggle [MultiTarget Bioactivity ChEMBL](https://www.kaggle.com/datasets/xjoannax88/multitarget-bioactivity-chembl). O CSV publicado lá está incompleto (1.333 linhas, sem EGFR, 95,5% DRD2), então a base foi reconstruída direto da API do ChEMBL. Dicionário de atributos, origem, hashes e problemas de qualidade: [`proteinas/DATASET.md`](proteinas/DATASET.md).

**Um cuidado na avaliação.** Moléculas diferentes podem ter exatamente os mesmos 5 descritores. Se uma cai no treino e a outra no teste, o modelo acerta por memória. Por isso o teste usa uma divisão agrupada, que mantém essas moléculas do mesmo lado.

### Notebooks

| Notebook | O que faz |
|---|---|
| [`01_curadoria`](proteinas/notebooks/01_curadoria.ipynb) | Baixa as atividades do ChEMBL e monta a base final |
| [`02_analise_exploratoria`](proteinas/notebooks/02_analise_exploratoria.ipynb) | Distribuição das classes e dos atributos |
| [`03_decision_tree`](proteinas/notebooks/03_decision_tree.ipynb) | Árvore de decisão: conjuntos de atributos, divisão aleatória contra agrupada, profundidade e poda |
| [`04_random_tree`](proteinas/notebooks/04_random_tree.ipynb) | Random Tree (a `RandomTree` do Weka): sorteio de K atributos por nó |
| [`05_random_forest`](proteinas/notebooks/05_random_forest.ipynb) | Random Forest: busca em grade e curva por número de árvores |
| [`06_gradient_boosting`](proteinas/notebooks/06_gradient_boosting.ipynb) | Gradient boosting por histogramas |
| [`07_comparacao`](proteinas/notebooks/07_comparacao.ipynb) | Todos os modelos com 10 seeds e o experimento-ponte (de onde vem o ganho da Random Forest) |

| Módulo em `proteinas/src/` | Conteúdo |
|---|---|
| `config.py` | Caminhos, alvos, filtros e constantes |
| `chembl_api.py`, `download.py` | Cliente da API do ChEMBL e download com cache em `data/raw/` |
| `inspection.py`, `curation.py` | Inspeção das atividades brutas e montagem da base final |
| `eda.py` | Tabelas da análise exploratória |
| `modeling.py` | Atributos, divisões, ajuste e avaliação, comuns a todos os modelos |
| `random_tree.py`, `random_forest.py`, `gradient_boosting.py` | Um módulo por modelo |
| `comparison.py` | Tabelas das 10 seeds e experimento-ponte |
| `plots.py` | Gráficos |

### Resultados

Os 17 atributos, divisão agrupada, média e desvio de 10 seeds ([`proteinas/scripts/multiseed.py`](proteinas/scripts/multiseed.py)):

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

- As contagens de caracteres do `SMILES` valem cerca de 10 pontos de acurácia para a árvore, e sozinhas superam os 5 descritores.
- A Random Tree sozinha perde para a árvore de decisão e varia mais com a semente: o sorteio de atributos esconde o melhor corte de cada nó.
- Mesmo assim, é ela que faz a Random Forest funcionar. Cerca de 80% do ganho da floresta sobre a árvore vem da média de muitas árvores; o sorteio de atributos traz o resto, mas só dentro do conjunto.
- O gradient boosting ajustado é o mais preciso. A Random Forest não precisa de ajuste e é a única cuja confiança separa acertos de erros. Só a árvore de decisão tem regras legíveis.

### Material

- Relatório: [`proteinas/report/main.pdf`](proteinas/report/main.pdf)
- Apresentação 1, árvore de decisão: [`proteinas/slides/apresentacao.pdf`](proteinas/slides/apresentacao.pdf), roteiro em [`notas.md`](proteinas/slides/notas.md)
- Apresentação 2, Random Tree e conjuntos de árvores: [`proteinas/slides/apresentacao_random_tree.pdf`](proteinas/slides/apresentacao_random_tree.pdf), roteiro em [`notas_random_tree.md`](proteinas/slides/notas_random_tree.md)

---

## Base 2: empréstimos, redes neurais e SVM

### Os dados

[Loan Approval Prediction](https://www.kaggle.com/datasets/architsharma01/loan-approval-prediction-dataset) do Kaggle (versão 1): 4.269 pedidos de empréstimo, 62,2% aprovados.

- **Atributos (11):** dependentes, escolaridade, autônomo, renda anual, valor do empréstimo, prazo, score de crédito e quatro tipos de patrimônio.
- **Alvo:** `loan_status` (aprovado ou rejeitado).

A curadoria tira os espaços dos nomes e valores, converte em 0/1 as duas colunas de texto e o alvo, e zera 28 valores negativos de patrimônio residencial. O código e os dados mantêm os nomes de coluna originais; gráficos e relatório usam os nomes em português.

**O que a base tem de especial.** O score de crédito decide quase tudo: abaixo de 550 pontos, 10,4% dos pedidos são aprovados; acima, 99,5%. O rótulo segue quase um degrau, e uma árvore representa um degrau com um único corte. Isso torna a base um bom teste para modelos de fronteira suave, como redes neurais e SVM.

### Protocolo de avaliação

Todos os modelos passam pelo mesmo protocolo ([`emprestimos/src/avaliacao.py`](emprestimos/src/avaliacao.py)):

- 10 seeds (0 a 9); em cada uma, divisão estratificada 80/20;
- busca de hiperparâmetros só no treino, com validação cruzada estratificada de 5 partes;
- métricas no teste: acurácia, F1 macro, AUC e matriz de confusão. A base é moderadamente desbalanceada (cerca de 1,6 aprovado por rejeitado), por isso o F1 macro e a AUC;
- tempo de treino, de busca e de previsão, medido num único núcleo, com aquecimento descartado; o resumo usa a mediana das seeds.

Cinco modelos de referência servem de régua: classe majoritária, regra de um corte (uma árvore de profundidade 1), regressão logística, árvore de decisão e Random Forest.

### Notebooks

| Notebook | O que faz |
|---|---|
| [`01_curadoria`](emprestimos/notebooks/01_curadoria.ipynb) | Confere o hash do CSV, limpa e grava `emprestimos.csv` |
| [`02_analise_exploratoria`](emprestimos/notebooks/02_analise_exploratoria.ipynb) | Mostra o degrau no score de crédito e a correlação entre os atributos |
| [`03_referencias`](emprestimos/notebooks/03_referencias.ipynb) | Define o protocolo e roda os modelos de referência |
| [`04_rede_neural`](emprestimos/notebooks/04_rede_neural.ipynb) | Rede neural: padronização, neurônios, épocas e paciência, busca em grade, comparação, tempo e erros |
| `05_svm` | A fazer |

| Módulo em `emprestimos/src/` | Conteúdo |
|---|---|
| `config.py` | Caminhos, colunas, nomes em português, hash do CSV, seeds |
| `avaliacao.py` | Protocolo: divisão, validação cruzada, medição de tempo e resumo das seeds |
| `rede.py` | MLP com padronização, grade de hiperparâmetros e curvas por época |

### Redes neurais

A rede é um `MLPClassifier` (ReLU, Adam) num Pipeline com `StandardScaler`, com parada antecipada e paciência 30. A busca testa 24 combinações: 6 arquiteturas, 2 valores de regularização L2 e 2 taxas de aprendizado.

Média de 10 seeds ([`emprestimos/resultados/`](emprestimos/resultados/)):

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
- **A rede supera a logística em todas as seeds, mas perde para a árvore em todas.** A árvore representa o degrau em 550 com um corte; a rede desenha uma rampa e erra perto do degrau. Pela AUC, a rede ordena os pedidos melhor que a árvore; o que ela erra é o corte em 50%.
- **Tipos de erro.** A rede erra mais dos dois lados: em média, 16,5 falsos positivos (aprova quem seria rejeitado) e 14,4 falsos negativos (recusa quem seria aprovado) por seed, contra 9,4 e 6,6 da árvore.
- **Custo.** Treinar a rede final leva cerca de 50 vezes o tempo de treinar a árvore, e a busca de hiperparâmetros da rede, cerca de 36 vezes o da busca da árvore.

### SVM

A fazer. A SVM vai passar pelo mesmo protocolo e ser comparada com a rede neural e com os modelos de referência acima.

### Material

- Relatório (redes neurais): [`emprestimos/report/main.pdf`](emprestimos/report/main.pdf)
- Apresentação 3, redes neurais: [`emprestimos/slides/apresentacao_redes_neurais.pdf`](emprestimos/slides/apresentacao_redes_neurais.pdf), roteiro em [`notas_redes_neurais.md`](emprestimos/slides/notas_redes_neurais.md)

---

## Como executar

Testado com Python 3.13.

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Linux/macOS: .venv/bin/python
.venv/Scripts/python -m jupyter notebook
```

Rode os notebooks de cada base na ordem. Os dados já estão no repositório, então nada precisa ser baixado. Para baixar a base 1 de novo do ChEMBL, mude `REFRESH = True` na primeira célula de `proteinas/notebooks/01_curadoria.ipynb`.

O notebook 07 da base 1 lê `proteinas/report/results/multiseed.csv`. Para gerar esse arquivo de novo, rode `python proteinas/scripts/multiseed.py` (cerca de 1 hora com 10 seeds).

Relatórios e slides, a partir da raiz. Os slides precisam de `python-pptx`, e o PDF dos slides, do PowerPoint. Cada script grava no `report/` ou `slides/` da própria base:

```bash
# base 1: moléculas
python proteinas/scripts/results_tables.py      # tabelas e números do relatório
python proteinas/scripts/export_figures.py      # figuras do relatório
python proteinas/scripts/slides_data.py && python proteinas/scripts/build_slides.py          # apresentação 1
python proteinas/scripts/slides_rt_data.py && python proteinas/scripts/build_slides_rt.py    # apresentação 2

# base 2: empréstimos
python emprestimos/scripts/rn_data.py && python emprestimos/scripts/rn_report.py   # números, figuras e tabela
python emprestimos/scripts/build_slides_rn.py                                       # apresentação 3

# PDF de uma apresentação
powershell -File comum/export_slides_pdf.ps1 proteinas/slides/apresentacao_random_tree.pptx
```

Para compilar um relatório, rode `latexmk -pdf main.tex` dentro de `proteinas/report/` ou `emprestimos/report/`.

## Licença dos dados

Os dados do ChEMBL e o dataset de moléculas do Kaggle são distribuídos sob [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). A base de empréstimos do Kaggle é distribuída sob licença MIT.
