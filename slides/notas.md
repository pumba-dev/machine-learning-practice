# Roteiro da apresentação (10 min)

Cada slide traz o roteiro (o que falar), um material de estudo e perguntas prováveis. O estudo e as perguntas servem para dominar o assunto e não fazem parte da fala. As mesmas notas estão no .pptx.

# Bloco 1 · Thiago · slides 1 a 4: O problema, a base e os descritores

## Slide 1: Classificação de alvos proteicos a partir de descritores moleculares do ChEMBL com árvores de decisão

**Roteiro (o que falar)** · Thiago · 0:15

Bom dia, professor e colegas. Eu sou o Thiago e, com o Paulo e o Bernan, vou apresentar como usamos uma árvore de decisão para descobrir a qual proteína uma molécula está associada, e como avaliamos o resultado sem nos enganar.

**Para estudar** (apoio; não faz parte da fala)

- Disciplina: PPGCC010 – Aprendizagem de Máquina (UFPI, 2026.2), Prof. Vinicius Ponte Machado. O relatório segue o formato de artigo da SBC e tem 10 páginas.
- ChEMBL: banco aberto e curado de moléculas e das suas medições de potência contra proteínas, mantido pelo EMBL-EBI (Gaulton et al., 2012; Zdrazil et al., 2024). Usamos a versão ChEMBL_37, extraída em 24/10/2026 pela API REST (Davies et al., 2015).
- Alvo é a proteína com a qual a molécula interage. Aqui os 4 alvos são as 4 classes do problema.
- Em uma frase, o trabalho é: calcular números de cada molécula, prever com uma árvore de decisão qual das 4 proteínas ela está associada e medir isso de forma honesta. Resultado: 89,4% de acurácia na divisão agrupada (média de 10 seeds).
- Código, notebooks e dados: github.com/pumba-dev/machine-learning-practice (o DATASET.md descreve a base e traz o hash SHA-256 de cada arquivo).

**Perguntas prováveis**

- **P:** Isso é um trabalho de biologia?  
  **R:** Não. É classificação supervisionada multiclasse com atributos numéricos. A química só aparece na origem dos números.

- **P:** Por que escolheram esse tema?  
  **R:** Partimos de um conjunto do Kaggle sobre atividade biológica de moléculas e percebemos que o arquivo estava quebrado; reconstruir a base do ChEMBL virou parte do trabalho.

## Slide 2: Prever o alvo de uma molécula é mais difícil do que parece

**Roteiro (o que falar)** · Thiago · 1:15

Nosso problema é de classificação: dada uma molécula, prever a qual de quatro proteínas ela está associada, EGFR, BACE1, DRD2 ou HDAC1. Reunimos 27.714 moléculas, e as classes são equilibradas, como mostram os cartões à esquerda. Isso importa para o piso de comparação: um modelo que responde sempre EGFR, a classe mais frequente, já acerta 29,3%. Qualquer resultado só vale se passar bem desse número. À direita, os três desafios do trabalho. Primeiro, a base de partida, do Kaggle, estava quebrada. Segundo, os cinco descritores da base separam pouco as classes: um descritor sozinho acerta no máximo 45,1%. Terceiro, e mais sutil, 25,8% das moléculas de teste têm uma gêmea no treino, outra molécula com exatamente os mesmos descritores, o que pode inflar o resultado. Vamos passar por cada um.

**Para estudar** (apoio; não faz parte da fala)

- Tarefa: classificação supervisionada multiclasse, 4 classes, 27.714 moléculas na base e 27.476 na modelagem (as outras 238 não têm descritores).
- Piso: responder sempre a classe majoritária (EGFR) dá 29,3% de acurácia e 11,3% de F1 macro. Acurácia é uma métrica aceitável porque as classes são equilibradas (de 20,2% a 29,3%); também reportamos F1 macro, a média simples do F1 das 4 classes.
- 'Associada a um alvo' quer dizer pChEMBL ≥ 6 contra ele. pChEMBL = −log10 da concentração molar em que a molécula tem efeito: 6 equivale a 1 µM, 9 equivale a 1 nM. Quanto maior, mais potente.
- Os 4 alvos, só para você saber responder (não precisa falar): EGFR, receptor do fator de crescimento epidérmico, uma quinase estudada em câncer de pulmão; BACE1, beta-secretase 1, uma protease estudada em Alzheimer; DRD2, receptor de dopamina D2, alvo de antipsicóticos; HDAC1, histona desacetilase 1, enzima de regulação epigenética estudada em oncologia.
- Por que árvore de decisão: as regras são legíveis (perguntas de sim ou não sobre os atributos), não exige normalizar atributos e é o modelo da disciplina. Random Forest e gradient boosting entram só como teto.
- Os três desafios são o fio do trabalho: base quebrada (slide 3), descritores fracos (slides 4 e 5) e vazamento por gêmeas (slide 6).

**Perguntas prováveis**

- **P:** Por que só 4 alvos?  
  **R:** É uma versão controlada do problema, inspirada no conjunto do Kaggle, que descrevia esses 4 alvos. Mais alvos é trabalho futuro.

- **P:** Por que não usaram uma rede neural?  
  **R:** O foco é a árvore de decisão pela interpretabilidade. Os modelos mais fortes aparecem só como referência de teto.

## Slide 3: A base do Kaggle estava quebrada, então reconstruímos do ChEMBL

**Roteiro (o que falar)** · Thiago · 1:00

Começando pela base. Partimos de um arquivo do Kaggle que não batia com a própria descrição: 1.333 linhas em vez de 8.711, nenhuma molécula de EGFR e 95,5% das linhas de DRD2. Não dava para treinar com isso, então reconstruímos a base direto do ChEMBL, na versão 37. O funil à direita mostra o caminho. Partimos de 58.736 medições de ligação. Tiramos duplicatas e registros sem SMILES. Agrupamos por par molécula e alvo, pela mediana. Mantivemos os pares com pChEMBL de pelo menos 6, uma medida de potência. E removemos 42 moléculas associadas a mais de um alvo, porque cada molécula precisa de uma única classe. Para modelar, saem ainda 238 moléculas sem descritores. Ficamos com 27.476.

**Para estudar** (apoio; não faz parte da fala)

- Arquivo do Kaggle (versão 17, atualizada em 28/09/2026): 1.333 linhas contra as 8.711 descritas; 3 alvos em vez de 4, sem nenhuma linha de EGFR; DRD2 com 95,5%, HDAC1 com 4,4% e BACE1 com 2 linhas. A página também trazia um identificador errado para BACE1 (CHEMBL1987 é outra proteína; o correto é CHEMBL4822). As versões anteriores exigem login para baixar.
- Consulta à API: ensaios de ligação (assay_type = B), valor exato (relação '=') e pChEMBL preenchido, para os 4 alvos: 58.736 medições.
- Qualidade: 7.328 registros marcados pelo ChEMBL como duplicata potencial e 49 sem SMILES; o filtro de validade de dados não removeu nenhum. Restam 51.359.
- Agregação: mediana do pChEMBL por par molécula-alvo (37.424 pares; em média 1,37 medições por par, no máximo 119). A mediana é robusta a medições discrepantes do mesmo par.
- Limiar de potência: pChEMBL ≥ 6 (27.798 pares). O notebook 01 mostra que com limiar 5 quase tudo vira associado e com limiar 7 cada alvo perde metade ou mais das moléculas.
- Moléculas com mais de um alvo: 42 (35 EGFR e HDAC1, 4 DRD2 e EGFR, 3 BACE1 e EGFR); saem porque a molécula precisa de um rótulo único. Sobram 27.714.
- 238 moléculas (0,86%) sem LogP, HBA, HBD e TPSA, quase todas moléculas muito grandes, para as quais o ChEMBL não calcula esses descritores. Saem só na modelagem, sem imputar valores.
- Conferência com o Kaggle: nas 525 moléculas presentes nos dois, 99,6% têm o mesmo rótulo e 99,4% os mesmos descritores.

**Perguntas prováveis**

- **P:** Por que pChEMBL ≥ 6?  
  **R:** É o limiar usual (1 µM). Com 5 quase tudo entra e com 7 cada alvo perde metade ou mais das moléculas.

- **P:** Por que tirar as moléculas com mais de um alvo?  
  **R:** Cada molécula precisa de uma única classe. Eram só 42, então o custo é pequeno.

- **P:** A reconstrução é reproduzível?  
  **R:** Sim. O download fica em cache, o DATASET.md traz o SHA-256 dos arquivos e o notebook 01 refaz o processo.

## Slide 4: A base traz 5 descritores por molécula, calculados da estrutura

**Roteiro (o que falar)** · Thiago · 1:00

Antes de usar a base, é preciso entender o que o modelo enxerga. A base traz cinco descritores por molécula, calculados pelo ChEMBL a partir da estrutura dela. Aqui estão os valores de uma molécula real, a CHEMBL1085117. A massa molecular é a soma das massas dos átomos: mede o tamanho da molécula. O LogP mede quanto ela prefere gordura a água. HBA e HBD contam os átomos aceptores e doadores de ligação de hidrogênio: aqui, 7 e 4. E a TPSA é a área ocupada pelos átomos polares. Para o modelo, essa molécula é só uma linha com cinco números: ele não vê a estrutura, nem o nome.

> Passagem para Paulo: “Esses cinco números são tudo que o modelo vê de cada molécula. Será que bastam?”

**Para estudar** (apoio; não faz parte da fala)

- Massa molecular, em dáltons: soma das massas atômicas. Na base, mediana 453,6, mínimo 127,1 e máximo 3.771,3 (182 moléculas passam de 1.000).
- LogP: coeficiente de partição octanol/água, calculado pelo ChEMBL (ALogP, estimado a partir da estrutura, não medido em laboratório). Valor alto significa mais afinidade por gordura que por água. Mediana 3,98; faixa de −3,83 a 14,00.
- HBA e HBD: contagens de aceptores (em geral átomos de N e O) e de doadores (hidrogênios ligados a N ou O) de ligação de hidrogênio. Medianas 6 (0 a 18) e 2 (0 a 13).
- TPSA, área de superfície polar topológica, em Å²: soma de contribuições de fragmentos polares (Ertl et al., 2000). Mediana 89,6; faixa de 3,2 a 404,9.
- Massa molecular, LogP, HBD e HBA são as quatro propriedades da regra dos cinco de Lipinski, por isso são descritores clássicos. A TPSA é um quinto descritor, também de polaridade.
- Leitura por alvo (medianas): DRD2 tem TPSA baixa (54,5) e HBD 1; EGFR tem as moléculas mais pesadas (497,6) e LogP 4,6; HDAC1 tem o maior HBD (3); BACE1 e HDAC1 se sobrepõem em massa, TPSA e HBA.
- TPSA, HBA e HBD são correlacionadas (Spearman 0,72 entre TPSA e HBA; 0,69 entre TPSA e HBD). A árvore tolera isso, mas a importância se divide entre elas.
- 4.777 linhas (17%) repetem exatamente os 5 valores de outra linha, sempre da mesma classe: isômeros e análogos próximos. É o gancho do slide 6.

**Perguntas prováveis**

- **P:** Por que não normalizaram os atributos?  
  **R:** Árvores só comparam um atributo com um limiar; mudar a escala não muda as divisões.

- **P:** O pChEMBL não seria um bom atributo?  
  **R:** Não: ele é o resultado do ensaio contra o próprio alvo, então vazaria o rótulo. Os descritores, ao contrário, são propriedades da molécula.

- **P:** Os descritores são medidos ou calculados?  
  **R:** Calculados pelo ChEMBL a partir da estrutura da molécula parental; são as mesmas colunas do arquivo do Kaggle (99,4% iguais nas 525 moléculas em comum).

# Bloco 2 · Paulo · slides 5 a 7: Atributos do SMILES, avaliar sem se enganar e o resultado principal

## Slide 5: Cinco descritores não bastam; contar o SMILES ajuda

**Roteiro (o que falar)** · Paulo · 1:00

Obrigado, Thiago. Será que esses cinco números bastam? Fizemos um experimento: para cada descritor, treinamos uma árvore de decisão de profundidade 3 que enxerga só aquele descritor e medimos a acurácia por validação cruzada. O melhor, o HBD, chega a 45,1%, contra o piso de 29,3%. Nenhum separa os alvos sozinho. Então criamos 12 atributos novos a partir do SMILES, o texto que descreve a estrutura da molécula, só contando caracteres. Na molécula do exemplo, são 48 caracteres, 6 átomos de nitrogênio, 4 de oxigênio, 2 anéis e 9 átomos aromáticos. É uma representação simples, mas, como vamos ver, carrega bastante informação.

**Para estudar** (apoio; não faz parte da fala)

- Experimento do descritor isolado: árvore de profundidade 3, validação cruzada de 5 partes, um descritor por vez. HBD 45,1%, TPSA 44,9%, HBA 43,3%, LogP 38,7%, massa molecular 37,8%; piso 29,3%. É um diagnóstico, não o modelo final.
- SMILES (Weininger, 1988): a molécula escrita como texto. Letras são átomos (minúscula indica átomo aromático), dígitos fecham anéis, parênteses abrem ramificações, '=' é ligação dupla, '#' é tripla, '+' e '-' são cargas e '@' e '/' marcam estereoquímica.
- Os 12 atributos: comprimento da cadeia; número de átomos de N, de O e de S; de halogênios (F, Cl, Br, I); de anéis (dígitos de fechamento divididos por 2); de ramificações; de átomos aromáticos; de ligações duplas e de triplas; de cargas; e de marcas de estereoquímica.
- Leitura da molécula de exemplo (HDAC1): 48 caracteres; N = 6, O = 4, S = 0; halogênios = 0; anéis = 2; ramificações = 5; aromáticos = 9; ligações duplas = 3; triplas = 0; cargas = 0; estereoquímica = 0.
- Limite: contar caracteres diz quantos átomos de cada tipo existem, mas não como eles se ligam; não enxerga subestruturas.
- Adiantando o resultado: só as 12 contagens dão 87,6%, mais que os 5 descritores (77,1%); juntos, 89,4% (divisão agrupada, média de 10 seeds).

**Perguntas prováveis**

- **P:** Por que não usaram uma biblioteca de química?  
  **R:** Foi uma decisão do projeto: ficar só com as propriedades do ChEMBL e contagens simples. Representações estruturais exigiriam essa biblioteca e são o próximo passo.

- **P:** Usar o SMILES não é vazamento?  
  **R:** Não: o SMILES é entrada, não rótulo. O risco é outro: moléculas parecidas no treino e no teste. O agrupamento por descritores idênticos não cobre isso, e declaramos como limitação.

- **P:** Como contam os halogênios?  
  **R:** F, Cl, Br e I. Cl e Br são tratados como um símbolo só para o 'C' de Cl não ser contado como carbono.

## Slide 6: A divisão aleatória deixa o teste ver a resposta

**Roteiro (o que falar)** · Paulo · 1:30

Agora o cuidado central do trabalho: como avaliar. Muitas moléculas diferentes têm exatamente os mesmos cinco descritores, e para o modelo elas são o mesmo ponto. Na divisão aleatória, à esquerda, uma dessas gêmeas pode cair no treino e a outra no teste, e acertar o teste vira só lembrar o treino. É o que o desenho mostra: as linhas tracejadas atravessam a fronteira. Medimos que 25,8% das moléculas de teste têm gêmea no treino. Na divisão agrupada, à direita, todas as gêmeas ficam do mesmo lado, e o teste exige generalizar. Comparamos então três conjuntos de atributos, só descritores, só SMILES e os dois juntos, com as duas divisões. São seis cenários, e repetimos tudo com dez seeds, para a conclusão não depender de um sorteio de sorte. Um detalhe: a validação que escolhe os hiperparâmetros também respeita os grupos.

**Para estudar** (apoio; não faz parte da fala)

- Vazamento de dados é quando informação do conjunto de teste chega ao treino; é uma causa conhecida de resultados superestimados (Kapoor e Narayanan, 2023).
- Números: das 27.476 moléculas, 22.699 têm uma tupla de descritores distinta e 4.777 repetem a de outra molécula; o maior grupo tem 12; nenhum grupo mistura classes. Na divisão aleatória, 25,8 ± 0,4% do teste tem gêmea no treino (10 seeds; na seed 42, 25,4%).
- Por que isso infla o resultado: a árvore sem limite de profundidade decora o treino. Como a gêmea é o mesmo ponto e tem a mesma classe, acertá-la não exige generalizar.
- Como é a divisão agrupada: validação cruzada de 5 partes, estratificada por classe e sem separar grupos (StratifiedGroupKFold, do scikit-learn); uma parte (20%) é o teste. As duas divisões têm 21.980 moléculas de treino e 5.496 de teste e preservam a proporção das classes.
- A validação cruzada interna, que escolhe os hiperparâmetros, também é agrupada. Com dobras comuns ela ficaria cerca de 5 pontos otimista, segundo o comentário no código.
- Busca em grade, 72 combinações: critério (Gini ou entropia), profundidade máxima (8, 12, 16 ou sem limite), mínimo por folha (1, 5 ou 20) e poda α (0, 1e-4 ou 3e-4). Em todos os cenários venceram a entropia, sem limite de profundidade e folha mínima 1; a poda só entrou com os descritores sozinhos.
- Os 6 cenários são os 3 conjuntos de atributos (descritores, SMILES, ambos) vezes as 2 divisões. As 10 seeds (0 a 9) mudam as divisões, as partes da validação e a semente dos modelos; a base é a mesma.
- Limite: o agrupamento só vê descritores idênticos. Moléculas muito parecidas (da mesma série química) continuam espalhadas entre treino e teste. Dividir por esqueleto molecular seria mais exigente e precisa de biblioteca de química.
- O desenho do slide é um esquema, não são dados reais.

**Perguntas prováveis**

- **P:** Por que 25,8% e não 20%?  
  **R:** 20% é o tamanho do teste. O número do slide é a fração dessas moléculas de teste cuja tupla de descritores também aparece no treino.

- **P:** Isso não é só overfitting?  
  **R:** A árvore sem poda ajusta 100% do treino nos dois casos. O problema é de avaliação: na divisão aleatória o teste não é independente do treino.

- **P:** Por que 10 seeds?  
  **R:** Um único sorteio pode ser favorável por acaso. As seeds mudam as divisões e as partes da validação; a base continua a mesma, então o desvio não mede incerteza para dados novos.

## Slide 7: Contar o SMILES eleva a acurácia em 16%

**Roteiro (o que falar)** · Paulo · 1:00

O resultado principal está neste gráfico, em média de dez seeds. Na divisão agrupada, os descritores sozinhos dão 77,1% de acurácia. Juntando as contagens de SMILES, chegamos a 89,4%: um ganho relativo de 16%. Repare no efeito da divisão aleatória, as colunas cinza. Ela superestima o resultado em 5,3% quando só há descritores, porque a árvore decora as gêmeas. Com os atributos de SMILES, o excesso cai para 1,5%, porque moléculas com os mesmos descritores têm SMILES diferentes. O desvio padrão fica abaixo de 0,8%, então a diferença é bem maior que a variação entre seeds.

> Passagem para Bernan: “Vamos ver agora o que essa árvore aprendeu e onde ela erra.”

**Para estudar** (apoio; não faz parte da fala)

- Descritores: 81,2% na aleatória e 77,1 ± 0,8% na agrupada. Só SMILES: 88,9% e 87,6 ± 0,6%. Ambos: 90,8% e 89,4 ± 0,4%.
- Ganho relativo = (B − A) / A, calculado por seed e depois com a média. De 77,1% para 89,4% são 12,3 pontos percentuais, ou 16% em relação a 77,1%. O artigo usa o relativo; só as contagens de SMILES já dão 14% sobre os descritores.
- Superestimativa da divisão aleatória, também relativa: 5,3 ± 1,2% com descritores, 1,5% com SMILES e 1,5% com ambos.
- Por que a superestimativa quase some com SMILES: duas moléculas com os mesmos descritores têm SMILES diferentes, então as contagens não são copiadas junto e decorar vale menos.
- F1 macro é a média simples do F1 das 4 classes; com classes equilibradas fica perto da acurácia (89,3% no cenário com os 17 atributos). Por classe: EGFR 89,2%, BACE1 90,9%, DRD2 90,4%, HDAC1 86,6%.
- Na seed 42, usada nas figuras e nos notebooks, a árvore acerta 89,7%, dentro da faixa de 88,6% a 89,9% das 10 seeds.

**Perguntas prováveis**

- **P:** Fizeram teste estatístico?  
  **R:** Não. Usamos média e desvio padrão entre seeds. O ganho de 12,3 pontos percentuais é muito maior que o desvio (0,8% no máximo).

- **P:** Por que ganho relativo e não em pontos?  
  **R:** É escolha de apresentação, e os dois dizem o mesmo: 12,3 pontos percentuais equivalem a 16% sobre 77,1%.

- **P:** Qual conjunto de atributos vocês escolheram?  
  **R:** Os 17 atributos juntos com divisão agrupada: é o cenário honesto, com o melhor desempenho.

# Bloco 3 · Bernan · slides 8 a 10: O que a árvore aprendeu, onde erra e a conclusão

## Slide 8: A Random Forest supera a árvore em 6,4%, mas só a árvore tem regras legíveis

**Roteiro (o que falar)** · Bernan · 1:00

Obrigado, Paulo. Para saber se 89,4% é bom, comparamos com um piso e um teto. A Random Forest chega a 95,2% e o gradient boosting a 94,8%: a Random Forest supera a nossa árvore em 6,4%. Então por que ficar com a árvore? Porque só ela tem regras legíveis. À direita, a primeira pergunta é: a TPSA é no máximo 67,9? Se sim, 69% das moléculas são DRD2. A árvore completa tem 1.854 folhas, e a TPSA e o número de átomos aromáticos são os atributos mais importantes. Ou seja, dá para explicar por que uma molécula foi classificada como DRD2, o que um conjunto de árvores não oferece.

**Para estudar** (apoio; não faz parte da fala)

- Random Forest com 300 árvores (95,2 ± 0,3%) e gradient boosting baseado em histogramas (94,8 ± 0,3%), ambos sem ajuste de hiperparâmetros, na mesma divisão agrupada e com os 17 atributos. Servem de teto de referência.
- Diferença: 5,8 pontos percentuais, ou 6,4% em termos relativos. Piso: 29,3%.
- A árvore escolhida (seed 42) tem 1.854 folhas e 24 níveis. Sobreajuste: o treino chega a 100% na profundidade 25 e a validação estaciona perto de 87% a partir da 16.
- Poda por custo-complexidade: com α = 1e-4 a árvore cai de 2.054 para 899 folhas sem perder acurácia de validação (87,0% para 87,2%); a partir de 1e-3 a poda custa acurácia e com α = 1e-2 sobram 8 folhas e 66,5%. Na busca em grade, a poda só venceu com os descritores sozinhos.
- Raiz: TPSA ≤ 67,9. Ramo 'sim': 25,5% das moléculas, 69% são DRD2. Ramo 'não': 74,5% das moléculas; a classe mais comum é EGFR, com só 34% (mistura). Depois vêm átomos aromáticos (≤ 14 no ramo 'sim', ≤ 12 no 'não'), HBD, anéis, comprimento do SMILES e halogênios.
- Importância dos atributos (seed 42), por duas medidas: por impureza, medida no treino, e por permutação, a queda de acurácia no teste ao embaralhar o atributo. TPSA e átomos aromáticos lideram nas duas (queda perto de 0,26 na permutação), seguidos de HBD (perto de 0,17) e de contagens de SMILES (átomos de N, halogênios, estereoquímica, anéis) acima de LogP e HBA.

**Perguntas prováveis**

- **P:** Por que não podaram a árvore?  
  **R:** A busca em grade incluía poda (α de 0, 1e-4 e 3e-4) e, com os atributos de SMILES, a melhor foi sem poda. A poda reduz folhas sem perder acurácia, mas escolhemos pela validação.

- **P:** Vale perder cerca de 6% por causa da interpretabilidade?  
  **R:** Depende do uso. A árvore explica cada previsão com um caminho de perguntas; os conjuntos de árvores não têm regras legíveis.

- **P:** A Random Forest sem ajuste não é injusta com ela?  
  **R:** Pode estar subestimando o teto, e dizemos isso nas limitações. Ela serve só de referência.

## Slide 9: A árvore erra entre HDAC1 e EGFR e não sabe que errou

**Roteiro (o que falar)** · Bernan · 1:00

Onde a árvore erra? A matriz de confusão, na seed 42, mostra que o maior erro é entre HDAC1 e EGFR: 28,7% de todos os erros. Olhamos exemplos desses erros e alguns têm um mesmo grupo de átomos, o C(=O)NO, que contagens de caracteres não conseguem distinguir. Outro ponto importante: sem poda, toda folha da árvore é pura, então ela diz ter 100% de confiança nas 5.496 previsões do teste, embora 10,3% estejam erradas. A confiança dela, portanto, não distingue acerto de erro. Isso aponta para os próximos passos.

**Para estudar** (apoio; não faz parte da fala)

- Matriz (seed 42): acertos EGFR 1.449 de 1.612, BACE1 1.335 de 1.463, DRD2 1.178 de 1.307, HDAC1 966 de 1.114. Erros: 568 de 5.496 (10,3%).
- Maiores confusões: HDAC1 lido como EGFR (88, 15,5% dos erros), EGFR como HDAC1 (75, 13,2%), DRD2 como EGFR (63, 11,1%), BACE1 como EGFR (52, 9,2%). HDAC1 e EGFR juntos somam 28,7%; 7,9% das moléculas de HDAC1 viram EGFR.
- Os erros não se concentram numa região: acertos e erros têm medianas quase iguais nos 17 atributos. Só o número de átomos de O (+1) e de halogênios (−1) se deslocam meio intervalo interquartil.
- C(=O)NO é o grupo hidroxamato, típico de inibidores de HDAC. Entre 6 exemplos de HDAC1 lidos como EGFR, 2 o têm. As contagens dizem quantos átomos de O e N existem, mas não como estão ligados.
- Confiança: sem poda toda folha é pura, então a probabilidade de classe que a árvore reporta (a pureza da folha) é sempre 100%. Por isso ela não distingue acerto de erro. Probabilidade calibrada exigiria poda ou um conjunto de árvores.
- Curva de aprendizado: a acurácia de validação sobe de 61,5% (879 linhas) a 87,0% (17.584) e não achata, então mais dados provavelmente ajudariam.

**Perguntas prováveis**

- **P:** Como reduzir o erro entre HDAC1 e EGFR?  
  **R:** Com uma representação que enxergue subestruturas, como representações estruturais da molécula, e com mais dados.

- **P:** Se a árvore diz 100% de confiança, como confiar nela?  
  **R:** Não se deve confiar nessa probabilidade: ela é a pureza da folha. Para priorizar moléculas seria preciso calibrar, com poda ou com um conjunto de árvores.

- **P:** O erro é maior em alguma classe?  
  **R:** HDAC1 é a mais difícil (F1 86,6%); BACE1 é a mais fácil (90,9%).

## Slide 10: Conclusões e próximos passos

**Roteiro (o que falar)** · Bernan · 1:00

Resumindo. Com avaliação honesta, a árvore chega a 89,4% de acurácia. Contar o SMILES dá um ganho relativo de 16% sobre só os descritores. E a divisão aleatória superestimaria o resultado entre 1,5% e 5,3%. Os limites: o agrupamento cobre só descritores idênticos, não famílias de moléculas parecidas; o modelo sempre escolhe uma entre quatro classes; e não há validação externa. Como próximos passos: representações estruturais da molécula, divisão por esqueleto molecular, mais dados e probabilidades calibradas. O código e os dados estão no repositório. Obrigado, e estamos abertos a perguntas.

> Bernan conduz as perguntas.

**Para estudar** (apoio; não faz parte da fala)

- Contribuições: (1) uma base reconstruída do ChEMBL_37 com 27.714 moléculas de quatro alvos; (2) 12 atributos obtidos só contando caracteres do SMILES, com ganho relativo de 16%; (3) avaliação com divisão agrupada e 10 seeds, que mede a superestimativa da divisão aleatória e situa a árvore entre o piso (29,3%) e o teto (Random Forest, 95,2%).
- Limites em detalhe: o agrupamento só considera descritores idênticos; o modelo é de conjunto fechado de 4 classes, sem a opção 'nenhuma das quatro'; as 10 seeds variam o sorteio mas não os dados, então o desvio não mede incerteza para dados novos; não há validação externa; Random Forest e gradient boosting estão sem ajuste; 238 moléculas sem descritores foram descartadas; as probabilidades da árvore não são calibradas.
- Próximos passos: representações estruturais da molécula (calculadas com biblioteca de química) enxergariam subestruturas como o C(=O)NO; divisão por esqueleto molecular daria uma estimativa menos otimista; mais dados (outros alvos ou limiar de pChEMBL mais baixo), já que a curva de aprendizado ainda sobe; e poda ou conjunto de árvores para probabilidades calibradas.
- Reprodutibilidade: seeds de 0 a 9, notebooks 01 a 03, hash SHA-256 de cada arquivo no DATASET.md; dados derivados do ChEMBL sob a licença CC BY-SA 3.0.

**Perguntas prováveis**

- **P:** Qual a principal contribuição?  
  **R:** Mostrar, com um protocolo reproduzível, que contar o SMILES dá 16% de ganho relativo e que a divisão aleatória superestima o resultado em 1,5% a 5,3%.

- **P:** Dá para usar isso na prática?  
  **R:** Ainda não: são só 4 classes fixas, a estimativa ainda é otimista para moléculas novas e não há validação externa.

- **P:** Por que acurácia e F1 macro, e não AUC?  
  **R:** O problema é multiclasse e as classes são equilibradas; acurácia e F1 macro resumem bem. A matriz de confusão mostra onde erra.
