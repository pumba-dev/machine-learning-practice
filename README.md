# Prática de Machine Learning: três bases, quatro famílias de modelos

Trabalhos da disciplina de Aprendizagem de Máquina (PPGCC010, UFPI). Cada família de modelos é estudada numa base própria, escolhida para o tipo de problema que esses modelos resolvem:

| | Base 1: molécula → proteína | Base 2: cliente → empréstimo | Base 3: pessoa → renda |
|---|---|---|---|
| Pergunta | A qual de 4 proteínas-alvo uma molécula está associada? | Um pedido de empréstimo foi aprovado? | A renda anual de uma pessoa passa de 50 mil dólares? |
| Tarefa | Classificação multiclasse (4 classes) | Classificação binária | Classificação binária e agrupamento (não supervisionado) |
| Origem | API do [ChEMBL](https://www.ebi.ac.uk/chembl/) (versão 37) | [Kaggle](https://www.kaggle.com/datasets/architsharma01/loan-approval-prediction-dataset) | [Kaggle](https://www.kaggle.com/datasets/uciml/adult-census-income) (UCI Adult, censo dos EUA de 1994) |
| Tamanho | 27.714 moléculas, 17 atributos | 4.269 pedidos, 11 atributos | 32.561 pessoas, 14 atributos (30.139 e 10 atributos após a curadoria) |
| Modelos estudados | Árvore de decisão e variações: Random Tree, Random Forest, Gradient Boosting | Redes neurais (MLP) | SVM, comparada com a rede neural; clusterização (K-means) |
| Pasta | [`proteinas/`](proteinas/) | [`emprestimos/`](emprestimos/) | [`renda/`](renda/) |

Cada pasta é autocontida: tem os dados, os notebooks, o código, os resultados, o relatório e os slides da sua base.

- [Base 1: moléculas e árvores de decisão](#base-1-moléculas-e-árvores-de-decisão)
- [Base 2: empréstimos e redes neurais](#base-2-empréstimos-e-redes-neurais)
- [Base 3: renda, SVM e clusterização](#base-3-renda-svm-e-clusterização)
- [Como executar](#como-executar)

## Organização do repositório

As pastas das bases seguem o mesmo formato:

```
proteinas/, emprestimos/ ou renda/
  data/raw/         dados como foram baixados
  data/processed/   base final, depois da curadoria
  notebooks/        análise passo a passo, numerada na ordem de execução
  src/              código que os notebooks chamam (os notebooks só chamam funções)
  report/           relatório em LaTeX (formato SBC), com main.pdf, figuras e tabelas geradas
  scripts/          geram os números, figuras e tabelas do relatório e montam os slides
  slides/           apresentações (.pptx e .pdf) e roteiros de fala (.md)
comum/              o que as apresentações das bases compartilham: slides_common.py,
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

## Base 2: empréstimos e redes neurais

### Os dados

[Loan Approval Prediction](https://www.kaggle.com/datasets/architsharma01/loan-approval-prediction-dataset) do Kaggle (versão 1): 4.269 pedidos de empréstimo, 62,2% aprovados.

- **Atributos (11):** dependentes, escolaridade, autônomo, renda anual, valor do empréstimo, prazo, score de crédito e quatro tipos de patrimônio.
- **Alvo:** `loan_status` (aprovado ou rejeitado).

A curadoria tira os espaços dos nomes e valores, converte em 0/1 as duas colunas de texto e o alvo, e zera 28 valores negativos de patrimônio residencial. O código e os dados mantêm os nomes de coluna originais; gráficos e relatório usam os nomes em português.

**O que a base tem de especial.** O score de crédito decide quase tudo: abaixo de 550 pontos, 10,4% dos pedidos são aprovados; acima, 99,5%. O rótulo segue quase um degrau, e uma árvore representa um degrau com um único corte. Isso torna a base um bom teste para modelos de fronteira suave, como redes neurais.

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

### Material

- Relatório (redes neurais): [`emprestimos/report/main.pdf`](emprestimos/report/main.pdf)
- Apresentação 3, redes neurais: [`emprestimos/slides/apresentacao_redes_neurais.pdf`](emprestimos/slides/apresentacao_redes_neurais.pdf), roteiro em [`notas_redes_neurais.md`](emprestimos/slides/notas_redes_neurais.md)

---

## Base 3: renda, SVM e clusterização

### Os dados

[Adult Census Income](https://www.kaggle.com/datasets/uciml/adult-census-income) do Kaggle, a base Adult da UCI, extraída do censo dos EUA de 1994: 32.561 pessoas, 24,1% com renda anual acima de 50 mil dólares.

- **Alvo:** `income` (`<=50K` ou `>50K`).
- **Atributos usados (10):**
  - 5 numéricos: idade, anos de estudo (`education.num`), ganho de capital, perda de capital e horas por semana;
  - 5 categóricos: classe de trabalho, estado civil, ocupação, relacionamento e país de origem.

**Curadoria** ([`01_curadoria`](renda/notebooks/01_curadoria.ipynb)):

- remove 24 linhas duplicadas e 2.398 linhas com `?` (valores ausentes). Sobram 30.139 pessoas, 24,9% com renda acima de 50 mil;
- tira `fnlwgt`, um peso amostral do censo e não um atributo da pessoa (correlação de −0,009 com o alvo);
- tira `education`, que é o texto de `education.num` (uma correspondência de 1 para 1).

Raça e sexo ficam fora dos modelos. Só voltam depois da previsão, para comparar os erros entre grupos.

**O que a base tem de especial.**

- **Nenhum atributo decide sozinho.** A regra de um corte pergunta se a pessoa é casada, mas responde `<=50K` dos dois lados.
- **Há um erro que nenhum modelo evita.** 673 perfis (2.404 pessoas, 8%) aparecem com as duas rendas, o que limita a acurácia a 97,1%.
- **O tamanho pesa.** Com 24 mil pessoas no treino, a SVM com kernel já é cara.

### Protocolo de avaliação

O mesmo da base 2 ([`renda/src/avaliacao.py`](renda/src/avaliacao.py)), com 10 seeds, divisão estratificada 80/20, validação cruzada de 5 partes no treino e tempos num único núcleo.

- **Pré-processamento:** o one-hot dos categóricos e a padronização dos numéricos ficam dentro do `Pipeline` e resultam em 80 colunas.
- **Métricas:** acurácia, F1 macro, F1 da classe `>50K`, AUC, falsos positivos e falsos negativos.
- **Desbalanceamento:** como há 3 pessoas `<=50K` para cada `>50K`, o chute fica em 75,1%.

### Notebooks

| Notebook | O que faz |
|---|---|
| [`01_curadoria`](renda/notebooks/01_curadoria.ipynb) | Confere o hash, remove duplicatas e `?`, escolhe os atributos e mede o erro irredutível |
| [`02_analise_exploratoria`](renda/notebooks/02_analise_exploratoria.ipynb) | Classes, atributos numéricos e categóricos, raça e sexo, regras simples |
| [`03_referencias`](renda/notebooks/03_referencias.ipynb) | Protocolo e modelos de referência |
| [`04_svm_estudo`](renda/notebooks/04_svm_estudo.ipynb) | Estudo numa seed: distância à fronteira, kernels, mapa C × gamma, padronização, vetores de suporte, tempo por tamanho, pesos por classe (cerca de 45 min) |
| [`05_svm_comparacao`](renda/notebooks/05_svm_comparacao.ipynb) | SVM linear, RBF, polinomial e RBF com pesos em 10 seeds, erros por sexo e raça (cerca de 2 h) |
| [`06_rede_comparacao`](renda/notebooks/06_rede_comparacao.ipynb) | Rede neural da base 2 em 10 seeds e comparação final (cerca de 20 min) |
| [`07_kmeans`](renda/notebooks/07_kmeans.ipynb) | K-means sem a renda: peso de cada atributo na distância, com e sem log no capital, curvas de k = 2 a 10 e estabilidade nas 10 seeds, perfil dos 6 grupos e comparação com a renda (cerca de 4 min) |

| Módulo em `renda/src/` | Conteúdo |
|---|---|
| `config.py` | Caminhos, atributos, nomes em português, hash do CSV, seeds |
| `avaliacao.py` | Pré-processamento e protocolo (cópia adaptada do da base 2) |
| `svm.py` | Pipelines da SVC e da LinearSVC e as grades de busca |
| `rede.py` | A rede neural da base 2, com o pré-processamento desta base |
| `clusters.py` | Pré-processamento com log no capital, K-means, métricas internas, estabilidade e perfil dos grupos |

### Resultados da SVM

Média de 10 seeds ([`renda/resultados/`](renda/resultados/)). A busca e a previsão estão em mediana por seed, e a previsão cobre as 6.028 pessoas do teste.

| Modelo | Grade da busca | Acurácia (%) | F1 macro (%) | AUC (%) | Busca | Previsão |
|---|---|---|---|---|---|---|
| Classe majoritária | – | 75,1 ± 0,0 | 42,9 | 50,0 | – | – |
| Regressão logística | – | 84,8 ± 0,3 | 78,3 | 90,2 | – | 4,5 ms |
| Árvore de decisão | critério × profundidade × folha mínima (30) | 85,2 ± 0,4 | 78,4 | 90,0 | 7 s | 5 ms |
| Random Forest | – (300 árvores, padrão) | 84,3 ± 0,4 | 78,1 | 89,1 | – | 180 ms |
| SVM linear (LinearSVC) | C ∈ {0,001 … 10} | 84,8 ± 0,3 | 78,2 | 90,2 | 1 s | 4,5 ms |
| **SVM RBF** | C ∈ {0,1; 1; 10; 100} × gamma ∈ {0,01; 0,03; 0,1; 0,3} | **85,4 ± 0,4** | 79,0 | 88,9 | 8 min | 2,0 s |
| SVM polinomial | grau ∈ {2, 3} × C ∈ {0,1; 1; 10} | 85,2 ± 0,4 | 78,7 | 90,2 | 2 min | 0,5 s |
| SVM RBF com pesos por classe | C e gamma do RBF | 80,9 ± 0,3 | 77,6 | 89,8 | – | 2,3 s |
| **Rede neural** | 6 arquiteturas × 2 alphas × 2 taxas | 85,2 ± 0,6 | **79,4** | **90,8** | 1,7 min | 5,6 ms |

- **A SVM RBF tem a melhor acurácia**, à frente da SVM linear e da Random Forest nas 10 seeds. Contra a árvore ajustada é empate: vence em 6 das 10 seeds, por 0,2 ponto.
- **A SVM linear é, na prática, a regressão logística.** A diferença é de 0,02 ponto. As duas traçam uma reta nas mesmas 80 colunas.
- **Na AUC, a SVM RBF fica atrás da SVM linear nas 10 seeds.**
  - A busca escolhe pela acurácia e prefere gamma alto, o que acerta o lado da fronteira mas ordena mal as pessoas longe dela.
  - Nas seeds em que a busca escolheu gamma = 0,3, a AUC foi 88,0%; com gamma = 0,1, foi 89,7%.
- **A rede neural tem o melhor F1 macro e a melhor AUC**, esta à frente de todos os modelos nas 10 seeds. Busca em 1,7 min e prevê 360 vezes mais rápido que a SVM RBF.
- **Padronização:** essencial para o RBF (85,0% contra 80,6% sem ela) e indiferente para a SVM linear.
- **Custo da SVC:** o tempo de treino cresce com o quadrado do número de pessoas (inclinação de 1,9 no gráfico log-log). A previsão cresce com o número de vetores de suporte, cerca de 8.800 no RBF.
- **Pesos por classe:** os falsos negativos caem de 587 para 221 e os falsos positivos sobem de 294 para 929.
- **Erros por sexo:**
  - a SVM RBF deixa passar 47,6% das mulheres de renda alta, contra 37,6% dos homens, sem usar o sexo como atributo;
  - a rede repete a diferença (43,6% contra 34,0%);
  - a diferença vem dos atributos relacionados ao sexo, como o relacionamento (`Husband` e `Wife`).

### Clusterização

A quinta análise estuda aprendizado não supervisionado na mesma base: o K-means forma grupos de pessoas a partir dos mesmos 10 atributos, sem ver a renda, que entra só no fim, para comparar. Não há divisão treino/teste.

- **Pré-processamento:** o mesmo da SVM (80 colunas), com log (`log1p`) no ganho e na perda de capital antes da padronização.
- **Escolha do k:** inércia (cotovelo), silhueta e Davies-Bouldin para k de 2 a 10, cada k com as 10 seeds e 10 inicializações por seed, mais a estabilidade (ARI entre as seeds).
- **Partição descrita:** k = 6, seed 42.

| Grupo | Pessoas | Perfil | % >50K |
|---|---|---|---|
| 1. Jovens solteiros | 8.439 | 26 anos, 82% nunca casados, 45% moram com os pais | 1,1 |
| 2. Mais velhos sem cônjuge | 5.443 | 53 anos, divorciados e viúvos, 8,5 anos de estudo | 12,6 |
| 3. Casados em ofícios manuais | 6.538 | 38 anos, 90% casados, 48 h por semana | 27,5 |
| 4. Profissionais com muito estudo | 5.791 | 13,3 anos de estudo, especialistas e gerentes | 44,8 |
| 5. Com perda de capital | 1.427 | todos com perda de capital | 51,6 |
| 6. Com ganho de capital | 2.501 | todos com ganho de capital | 63,8 |
| Base inteira | 30.139 | | 24,9 |

- **k = 6:** cotovelo entre 5 e 6, e as 10 seeds chegam aos mesmos grupos (ARI de 0,995). Silhueta e Davies-Bouldin preferem k = 2, que só separa quem tem ganho de capital.
- **A base não tem grupos nítidos:** silhueta de 0,17 de k = 4 em diante. Os grupos são regiões de uma nuvem contínua.
- **10 inicializações são necessárias:** com uma só, o ARI entre seeds cai de 0,995 para 0,59 em k = 6.
- **O capital domina a distância:**
  - sem log, as 148 pessoas com ganho de 99.999 (o teto do censo) formam um grupo só delas;
  - com log, esse grupo some, mas quem tem ganho ou perda (13% da base) forma dois grupos próprios.
- **Os grupos descrevem, não preveem:**
  - eles se ordenam pela renda sem tê-la visto;
  - a pureza (cada grupo responde a renda da sua maioria) é de 77,5%, contra 75,1% do chute e 85,4% da SVM RBF;
  - o ARI contra a renda é de 0,09.
- **Custo:** 0,9 s por ajuste com k = 6 e 10 inicializações, num núcleo; o estudo inteiro leva cerca de 4 min.

### Material

- Relatório (SVM; clusterização a fazer): [`renda/report/main.pdf`](renda/report/main.pdf)
- Apresentação 4, SVM: [`renda/slides/apresentacao_svm.pdf`](renda/slides/apresentacao_svm.pdf), roteiro em [`notas_svm.md`](renda/slides/notas_svm.md)
- Apresentação 5, clusterização: [`renda/slides/apresentacao_clusters.pdf`](renda/slides/apresentacao_clusters.pdf), roteiro em [`notas_clusters.md`](renda/slides/notas_clusters.md)

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

# base 3: renda
python renda/scripts/svm_data.py && python renda/scripts/svm_report.py   # números, figuras e tabelas do relatório
python renda/scripts/build_slides_svm.py                                 # apresentação 4
python renda/scripts/clusters_data.py && python renda/scripts/build_slides_clusters.py   # apresentação 5

# PDF de uma apresentação
powershell -File comum/export_slides_pdf.ps1 proteinas/slides/apresentacao_random_tree.pptx
```

Para compilar um relatório, rode `latexmk -pdf main.tex` dentro da pasta `report/` da base.

## Licença dos dados

Os dados do ChEMBL e o dataset de moléculas do Kaggle são distribuídos sob [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). A base de empréstimos do Kaggle é distribuída sob licença MIT. A base Adult da UCI é distribuída sob [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
