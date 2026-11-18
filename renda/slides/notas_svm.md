# Roteiro da quarta apresentação (10 min)

Cada slide traz o roteiro (o que falar), um material de estudo e perguntas prováveis. O estudo e as perguntas servem para dominar o assunto e não fazem parte da fala. As mesmas notas estão no .pptx.

# Bloco 1 · Thiago · slides 1 a 5: A base, a curadoria e as réguas

## Slide 1: SVM na previsão de renda

**Roteiro (o que falar)** · Thiago · 0:25

Bom dia, professor e colegas. Eu sou o Thiago e, com o Paulo e o Bernan, vou apresentar a quarta parte do trabalho. Mais uma vez a base muda: agora são pessoas do censo americano, e a pergunta é se a renda passa de 50 mil dólares por ano. O modelo estudado é a SVM, a máquina de vetores de suporte, comparada com os modelos das partes anteriores, inclusive a rede neural.

**Para estudar** (apoio; não faz parte da fala)

- Disciplina: PPGCC010 – Aprendizagem de Máquina (UFPI, 2026.2), Prof. Vinicius Ponte Machado.
- Tudo no repositório, pasta renda/: notebooks 01 a 06, resultados em renda/resultados/.
- Biblioteca: scikit-learn (SVC, LinearSVC, MLPClassifier), a mesma das partes anteriores.
- Por que uma base nova: a de empréstimos era pequena (4.269 pedidos) e quase resolvida por um corte no score. A Adult tem atributos de texto, valores ausentes e tamanho suficiente para o custo da SVM aparecer.

**Perguntas prováveis**

- **P:** Por que não usar a SVM na base de empréstimos?  
  **R:** Lá uma regra de um corte já acertava 95,5% e a árvore 98%: sobrava pouco para a SVM mostrar. A Adult é maior, tem atributos categóricos e nenhuma regra simples resolve, então as diferenças entre fronteiras retas e curvas e o custo da SVM aparecem.

## Slide 2: 30.139 pessoas do censo, 10 atributos

**Roteiro (o que falar)** · Thiago · 0:40

A base é a Adult, do repositório da UCI, extraída do censo dos Estados Unidos de 1994. Depois da curadoria, ficam 30.139 pessoas e 10 atributos: cinco numéricos, como idade, anos de estudo e horas por semana, e cinco de texto, como estado civil e ocupação. O rótulo diz se a pessoa ganha mais de 50 mil por ano: 24,9% ganham. Então responder sempre ‘não’ já acerta 75,1%; esse é o piso.

**Para estudar** (apoio; não faz parte da fala)

- Base bruta: 32.561 linhas, 24,1% acima de 50 mil. Kaggle (uciml/adult-census-income), cópia da Adult da UCI (CC BY 4.0). Arquivo conferido pelo hash SHA-256 no notebook 01.
- Numéricos: idade, anos de estudo (education.num, de 1 a 16), ganho de capital, perda de capital, horas por semana.
- Categóricos: classe de trabalho (7), estado civil (7), ocupação (14), relacionamento (6), país de origem (41).
- A SVM só trabalha com números: cada categoria vira uma coluna 0/1 (one-hot). São 80 colunas no total, metade delas só de país (91% nasceram nos EUA).
- O valor de 50 mil dólares é de 1994; corrigido pela inflação, seria perto de 100 mil hoje.

**Perguntas prováveis**

- **P:** O que é one-hot?  
  **R:** Uma coluna por categoria, com 1 na categoria da pessoa e 0 nas outras. ‘Estado civil’ com 7 valores vira 7 colunas. Assim o modelo não supõe uma ordem que não existe, como ‘casado > divorciado’.

- **P:** Por que não usar a escolaridade em texto?  
  **R:** Porque ela é a mesma informação de anos de estudo: cada nível corresponde a exatamente um número. Usamos o número, que já tem ordem.

## Slide 3: Curadoria: 2.422 linhas e 2 atributos fora

**Roteiro (o que falar)** · Thiago · 0:40

A curadoria tirou três coisas. Primeiro, 24 linhas repetidas. Depois, 2.398 linhas com valor ausente, marcado com interrogação, quase todas em classe de trabalho e ocupação. Sobram 30.139 pessoas, o que ainda é bastante. E tiramos dois atributos: o fnlwgt, que é um peso amostral do censo, quantas pessoas cada linha representa, e não uma característica da pessoa; e a escolaridade em texto, que repete os anos de estudo.

**Para estudar** (apoio; não faz parte da fala)

- As linhas com ‘?’ eram 7% da base. Nelas, 13,9% ganham mais de 50 mil, contra 24,9% no resto: removê-las tira mais gente de renda baixa, mas a proporção quase não muda.
- Classe de trabalho e ocupação faltam juntas em 1.836 linhas. As 7 linhas com só a ocupação ausente são de quem nunca trabalhou (classe ‘Never-worked’): não há ocupação a informar.
- fnlwgt: correlação de -0,009 com a renda. Serve para estimar totais do país, não para prever a renda de uma pessoa.
- Raça e sexo também ficaram fora dos atributos do modelo; o relatório explica a decisão. Os dados continuam no arquivo, mas nenhum modelo os usa.

**Perguntas prováveis**

- **P:** Por que não preencher os ausentes em vez de remover?  
  **R:** Eram 7% das linhas, e ainda sobram 30 mil pessoas. Preencher a ocupação de alguém com a mais comum inventaria uma informação justamente num dos atributos mais importantes.

- **P:** Raça e sexo entraram no modelo?  
  **R:** Não. Ficaram fora dos atributos por decisão do grupo, explicada no relatório. O modelo usa só os 10 atributos do slide anterior.

## Slide 4: Nenhum atributo decide sozinho

**Roteiro (o que falar)** · Thiago · 0:45

O que torna a base difícil é que nenhum atributo decide sozinho. O mais forte é o estado civil: entre os casados, 46% ganham mais de 50 mil; entre quem nunca casou, 5%. Mas nem os casados passam da metade. A regra de um corte faz essa pergunta e responde ‘não’ dos dois lados, então fica nos mesmos 75,1% do chute. Na base de empréstimos, essa regra acertava 95%. E há um limite: 673 perfis idênticos aparecem com as duas rendas, então nenhum modelo passa de 97,1%.

**Para estudar** (apoio; não faz parte da fala)

- Perfis em conflito: 673 combinações dos 10 atributos aparecem com as duas rendas, em 2.404 linhas (8%). Em cada perfil, o melhor possível é responder a renda mais comum, e erra-se o resto: 867 erros no mínimo, ou 2,9% da base.
- São pessoas diferentes com os mesmos dados (não duplicatas: a linha completa, com fnlwgt, era diferente).
- Na análise exploratória, a melhor regra de duas perguntas (casado com 13 anos de estudo ou mais, ou não casado com ganho de capital alto) acerta 82,4%.
- A AUC da regra de um corte é 75,6%, bem acima de 50%: a pergunta ordena bem as pessoas, mas o corte em 50% não muda a resposta.

**Perguntas prováveis**

- **P:** Se a regra pergunta algo útil, por que acerta o mesmo que o chute?  
  **R:** Porque nos dois lados a maioria ganha até 50 mil (55% dos casados, 93% dos demais). Cada lado responde a sua maioria, e as duas maiorias são ‘não’.

- **P:** Como pode haver erro inevitável?  
  **R:** Duas pessoas com exatamente os mesmos 10 atributos podem ter rendas diferentes. Qualquer modelo dá a mesma resposta para as duas, e erra pelo menos uma.

## Slide 5: As réguas: 75% de chute, 85% dos clássicos

**Roteiro (o que falar)** · Thiago · 0:35

O protocolo é o mesmo da parte anterior: dez divisões diferentes, 80% para treino e 20% para teste, busca de hiperparâmetros com validação cruzada só no treino, e tempo medido num único núcleo. Como há três pessoas abaixo para cada uma acima, olhamos também o F1 macro e a AUC. As réguas são estas: a regressão logística, a árvore ajustada e a Random Forest ficam entre 84,3 e 85,2% de acurácia. A meta da SVM é passar de 85% e de 78% de F1 macro.

> Passagem para Paulo: “Com essas réguas, como a SVM funciona e o que ela precisa para chegar lá?”

**Para estudar** (apoio; não faz parte da fala)

- Validação cruzada estratificada de 5 partes dentro do treino; o teste só é usado uma vez por seed.
- Tempos: mediana das 10 seeds, um núcleo (threadpool_limits(1), n_jobs=1), aquecimento descartado. Máquina: Ryzen 5 9600X.
- F1 macro: média do F1 das duas classes; não deixa a classe grande esconder a pequena. AUC: chance de uma pessoa de renda alta receber nota maior que uma de renda baixa; não depende do corte em 50%.
- Árvore: busca em critério × profundidade × folha mínima (30 combinações). Random Forest: 300 árvores, configuração padrão, como nas partes 2 e 3.
- A Random Forest fica abaixo da árvore nas 10 seeds: com folhas de 1 pessoa, ela decora o ruído dos perfis em conflito.

**Perguntas prováveis**

- **P:** Por que a Random Forest perdeu para uma árvore só?  
  **R:** Na configuração padrão, cada árvore cresce até separar todas as pessoas do treino. Com 8% das linhas em perfis que aparecem com as duas rendas, crescer até o fim é decorar ruído. A árvore ajustada para antes, com folhas de 5 a 20 pessoas.

- **P:** Por que 10 seeds?  
  **R:** Uma divisão só pode favorecer um modelo por sorte. Com 10, vemos a média, o desvio e em quantas seeds um modelo vence o outro.

# Bloco 2 · Paulo · slides 6 a 10: Como a SVM funciona: margem, kernel, C e gamma, padronização e custo

## Slide 6: A SVM busca a fronteira de maior margem

**Roteiro (o que falar)** · Paulo · 0:45

Agora, como a SVM funciona. Ela procura a fronteira que separa as classes com a maior margem, a faixa vazia mais larga possível entre elas. Os pontos que ficam na borda da margem, ou do lado errado, são os vetores de suporte: só eles definem a fronteira. O parâmetro C diz quanto custa cada erro no treino: C pequeno aceita erros e deixa a margem larga; C grande tenta acertar todos e estreita a margem. Nesta base, a SVM usa cerca de 8.764 vetores de suporte, 36% do treino.

**Para estudar** (apoio; não faz parte da fala)

- A SVM não calcula probabilidade. Para cada pessoa, calcula a distância com sinal até a fronteira (decision_function): positiva, >50K; negativa, ≤50K. A AUC usa essa distância como nota.
- Na seed 0, 30% das pessoas do teste caem dentro da margem (distância entre −1 e +1).
- A classe pequena aparece muito entre os vetores de suporte: metade deles é >50K, embora seja 25% do treino, porque boa parte dela fica perto da fronteira.
- Com C = 0,01, 48% do treino vira vetor de suporte; com C = 100, 34%.
- Probabilidade só com probability=True, que faz uma calibração extra (Platt) com validação cruzada interna e deixa o treino cerca de 5 vezes mais lento; não usamos.

**Perguntas prováveis**

- **P:** Por que maximizar a margem?  
  **R:** Entre todas as fronteiras que separam o treino, a de margem maior fica mais longe dos dois grupos, e uma pessoa nova um pouco diferente das do treino tem menos chance de cair do lado errado.

- **P:** Se só os vetores de suporte importam, o resto do treino é inútil?  
  **R:** Para a fronteira final, sim: tirar um ponto que não é vetor de suporte não muda nada. Mas não se sabe antes quais serão vetores de suporte; o treino precisa de todos para descobrir.

## Slide 7: O kernel permite curvar a fronteira

**Roteiro (o que falar)** · Paulo · 0:30

O kernel permite curvar a fronteira. O linear traça uma reta; o polinomial combina atributos, como idade vezes horas; e o RBF curva a fronteira em torno dos pontos, com o gamma definindo o alcance de cada um. Sem ajuste, todos ficam entre 84,5 e 85,1%. E a LinearSVC chega à mesma reta 63 vezes mais rápido que a SVC linear.

**Para estudar** (apoio; não faz parte da fala)

- Medição na seed 0 do notebook 04, C = 1, gamma padrão (‘scale’, cerca de 0,10 nesta base).
- Kernel: uma função que mede a semelhança entre duas pessoas. A SVM com kernel equivale a traçar uma reta num espaço transformado, sem calcular esse espaço (o ‘truque do kernel’).
- RBF: semelhança = exp(−gamma × distância²). Gamma grande: cada ponto só influencia a vizinhança, fronteira cheia de curvas. Gamma pequeno: influência larga, fronteira suave.
- Polinomial com coef0 = 1: o grau 2 inclui os termos lineares e os produtos de pares de atributos.
- LinearSVC (liblinear) e SVC linear (libsvm) chegam à mesma fronteira por algoritmos diferentes; a LinearSVC cresce com n, a SVC com n². Por isso a comparação usa a LinearSVC.

**Perguntas prováveis**

- **P:** O RBF é um polinômio de grau infinito?  
  **R:** Matematicamente, o RBF corresponde a um espaço transformado de dimensão infinita, e a sua expansão em série tem termos de todos os graus. Na prática, o que importa é que ele mede semelhança pela distância.

## Slide 8: C e gamma formam um platô na diagonal

**Roteiro (o que falar)** · Paulo · 0:40

Este mapa mostra a acurácia na validação para cada par de C e gamma. A melhor combinação é C igual a 1 e gamma 0,3, com 85,45%, mas 13 das 35 combinações ficam a meio ponto dela: é um platô na diagonal. Gamma menor pede C maior. Nos cantos, o modelo falha: com os dois pequenos, cai no chute; com gamma 1, decora o treino.

**Para estudar** (apoio; não faz parte da fala)

- Seed 0, validação cruzada de 5 partes no treino: 5 valores de C × 7 de gamma, 35 combinações, 175 treinos. O mapa levou 41 minutos, dos quais só 17 de treino; o resto foi avaliação.
- Gamma = 1 com C = 1: 90,5% no treino e 83,5% na validação. É sobreajuste: a fronteira contorna as pessoas do treino uma a uma.
- Por que a diagonal: gamma pequeno deixa a fronteira suave; C grande cobra mais pelos erros e compensa. As duas combinações levam a fronteiras parecidas.
- A grade das 10 seeds (C ∈ {0,1; 1; 10; 100} × gamma ∈ {0,01; 0,03; 0,1; 0,3}) saiu deste mapa: cobre o platô e deixa de fora os cantos ruins.

**Perguntas prováveis**

- **P:** O melhor ponto está na borda da grade (gamma = 0,3). Não deveria testar valores maiores?  
  **R:** O mapa já testou gamma = 1, e ele piora em qualquer C. A borda da grade das 10 seeds não esconde um valor melhor.

## Slide 9: Sem padronização, o RBF perde 4 pontos

**Roteiro (o que falar)** · Paulo · 0:35

A padronização é obrigatória para o RBF. Sem ela, a acurácia cai de 85,0 para 80,6%. O RBF mede distâncias, e o ganho de capital vai até 99 mil: sem padronizar, ele domina todos os outros atributos. Já a SVM linear não muda, porque dá um peso a cada atributo, e um atributo de escala grande só recebe um peso pequeno.

**Para estudar** (apoio; não faz parte da fala)

- Padronizar: (valor − média) ÷ desvio padrão, com média e desvio só do treino, dentro do Pipeline. O one-hot (0/1) continua nos dois casos.
- Sem padronização, o F1 da classe >50K cai de 67,6 para 50,8%, os vetores de suporte sobem para 16.995 (70% do treino) e o treino leva 31 s.
- É o mesmo recado da rede neural na parte 3: lá, sem padronização, a rede ficava abaixo do chute.

**Perguntas prováveis**

- **P:** E a árvore, precisa de padronização?  
  **R:** Não. A árvore compara um atributo por vez com um limite, e mudar a escala só muda o valor do limite.

## Slide 10: O custo da SVM com kernel cresce rápido

**Roteiro (o que falar)** · Paulo · 0:45

O custo da SVM com kernel cresce rápido. No gráfico, em escala log, a inclinação da SVC é 1,9: dobrar o treino quadruplica o tempo. A LinearSVC tem inclinação 1,1, cresce junto com os dados. Com as 24 mil pessoas, a SVC treina em 5,8 segundos e a LinearSVC em 0,07. E a previsão também pesa: a SVC compara cada pessoa com todos os vetores de suporte.

> Passagem para Bernan: “Com o modelo entendido, o que a busca escolheu e como ficou o resultado?”

**Para estudar** (apoio; não faz parte da fala)

- Medição na seed 0 (notebook 04), treinos com 1.000 a 24.111 pessoas; inclinação ajustada de 4.000 pessoas para cima (nos tamanhos pequenos, um custo fixo pesa mais que os dados).
- Pela regra do quadrado, a mesma SVC levaria cerca de 100 s com 100 mil pessoas e quase 3 horas com 1 milhão. Numa base assim, usa-se a LinearSVC ou uma aproximação do kernel.
- Previsão das 6.028 pessoas do teste (mediana de 10 seeds): SVM RBF 2,0 s, SVM linear 4,5 ms. A linear guarda só um peso por coluna.
- Por que n²: a SVC trabalha com a semelhança entre pares de pessoas, e o número de pares cresce com o quadrado.

**Perguntas prováveis**

- **P:** Dá para acelerar a SVC usando mais núcleos?  
  **R:** O libsvm treina num núcleo só. A busca em grade pode rodar combinações em paralelo, mas cada treino continua com o mesmo custo. Medimos tudo num núcleo para comparar os modelos de forma justa.

# Bloco 3 · Bernan · slides 11 a 15: O que a busca escolheu, resultado, AUC, rede neural e conclusão

## Slide 11: O que testamos e o que a busca escolheu

**Roteiro (o que falar)** · Bernan · 0:35

Esta tabela mostra as réguas de cada modelo: os valores que a busca testou e o que ela escolheu nas dez seeds. A SVM é estável: a linear escolheu C igual a 0,1 em sete seeds, o RBF escolheu C igual a 1 em nove, e a polinomial ficou no grau 2. Já a árvore e a rede variam com a seed, porque várias configurações empatam na validação.

**Para estudar** (apoio; não faz parte da fala)

- SVM RBF: gamma 0,3 em 5 seeds, 0,1 em 4; na seed restante, C = 10 e gamma = 0,03, também no platô (gamma menor, C maior).
- Árvore: 8 combinações diferentes em 10 seeds; profundidade de 8 para cima (em 2 seeds, sem limite, mas com folha mínima de 5 ou 20).
- Rede: 10 combinações diferentes em 10 seeds; o early stopping parou entre 33 e 86 épocas.
- Total de treinos por seed na busca: SVM linear 25, RBF 80, polinomial 30, árvore 150, rede 120.

**Perguntas prováveis**

- **P:** Por que a rede escolhe uma configuração diferente em cada seed?  
  **R:** Várias arquiteturas chegam ao mesmo resultado na validação, e a diferença entre elas é menor que a variação de uma divisão para outra. A escolha muda com o sorteio, mas o resultado no teste fica parecido.

## Slide 12: A SVM RBF tem a melhor acurácia, por pouco

**Roteiro (o que falar)** · Bernan · 0:45

Nas dez seeds, a SVM RBF tem a melhor acurácia, 85,4%, e o melhor F1 macro entre as SVMs, 79,0%. Ela vence a SVM linear e a Random Forest nas dez seeds. Mas contra a árvore ajustada é empate: vence em 6 de dez, por 0,2 ponto. E a SVM linear dá o mesmo resultado da regressão logística. A meta foi cumprida, mas por pouco: curvar a fronteira rende menos de um ponto.

**Para estudar** (apoio; não faz parte da fala)

- SVM RBF − SVM linear: +0,57 ponto de acurácia (10 de 10 seeds), +0,82 de F1 macro.
- SVM RBF − Random Forest: +1,14 ponto (10 de 10).
- SVM linear − regressão logística: +0,02 ponto. As duas traçam uma reta nas mesmas 80 colunas; muda só a função que minimizam (hinge contra logística).
- Desvios entre seeds: cerca de 0,4 ponto. Diferenças abaixo disso só valem se aparecem em quase todas as seeds.
- Todos os modelos sem pesos erram cerca de duas vezes mais por falso negativo (cerca de 590) que por falso positivo (cerca de 300).

**Perguntas prováveis**

- **P:** 0,2 ponto sobre a árvore é uma vitória?  
  **R:** Não. A diferença varia cerca de 0,4 ponto de uma seed para outra, e a SVM vence em só 6 de 10. É empate. Contra a SVM linear e a Random Forest, sim: vence nas 10.

- **P:** Por que nenhum modelo chega perto de 97%?  
  **R:** Os 97,1% são um limite teórico: só seriam alcançados se o modelo acertasse todas as pessoas com perfil único. Os atributos do censo não explicam a renda tão bem; falta informação, não modelo.

## Slide 13: Pela AUC, a ordem se inverte

**Roteiro (o que falar)** · Bernan · 0:45

Pela AUC, a ordem se inverte. A SVM RBF tem 88,9%, abaixo da SVM linear e da polinomial, com 90,2%, e perde para a linear nas dez seeds. O motivo é o critério da busca: ela escolhe pela acurácia e prefere gamma alto, que acerta o lado da fronteira, mas ordena mal as pessoas longe dela. Nas seeds com gamma 0,3, a AUC foi 88,0%; com 0,1, 89,7%.

**Para estudar** (apoio; não faz parte da fala)

- Acurácia pergunta: ‘acertou o lado da fronteira?’. AUC pergunta: ‘quem tem renda alta ficou na frente de quem não tem?’. Um modelo pode ser bom numa e pior na outra.
- Com gamma alto, cada vetor de suporte só influencia a vizinhança. Longe deles, a nota de quase todo mundo cai para o mesmo valor, e a ordem entre essas pessoas se perde.
- A acurácia no teste nem melhora com gamma 0,3 (85,2% contra 85,5% com 0,1): a busca preferiu 0,3 por décimos na validação que não se repetiram no teste.
- Se o objetivo fosse ordenar (escolher as mil pessoas com mais chance), a busca deveria usar a AUC como critério, e provavelmente escolheria gamma menor.
- A rede neural tem a melhor AUC de todos: 90,8%.

**Perguntas prováveis**

- **P:** Qual métrica deveria escolher o modelo?  
  **R:** Depende do uso. Para decidir sim ou não com o corte padrão, a acurácia ou o F1. Para ordenar pessoas por chance, a AUC. O importante é escolher o critério antes, porque otimizar um pode piorar o outro.

## Slide 14: A rede alcança a SVM a uma fração do custo

**Roteiro (o que falar)** · Bernan · 0:40

Por fim, a rede neural da parte anterior, com a mesma grade e o mesmo protocolo. Na acurácia, a SVM RBF fica à frente em 8 das dez seeds, por 0,2 ponto. No F1 macro, empatam. Na AUC, a rede vence nas dez. E custa muito menos: a busca leva menos de dois minutos por seed, contra oito, e a previsão é 361 vezes mais rápida.

**Para estudar** (apoio; não faz parte da fala)

- Rede: MLP com ReLU e Adam, early stopping com paciência 30, grade de 6 arquiteturas × 2 alphas × 2 taxas (24 combinações), a mesma da parte 3.
- A rede minimiza a perda logística, ou seja, é treinada para estimar probabilidade, e por isso ordena bem em toda a faixa. A SVM é treinada só para acertar o lado da fronteira.
- Depois de treinada, a rede prevê com algumas multiplicações de matrizes (5,6 ms para o teste). A SVM RBF compara cada pessoa com cerca de 8.764 vetores de suporte.
- A rede erra menos por falso negativo (533, contra 587 da SVM RBF) e um pouco mais por falso positivo (362, contra 294).
- A rede varia mais entre seeds (desvio de 0,6 ponto na acurácia, contra 0,4 da SVM).

**Perguntas prováveis**

- **P:** Então a rede é melhor que a SVM?  
  **R:** Depende do critério. Pela acurácia, a SVM RBF vence por pouco; pela AUC e pelo custo, a rede. Nesta base, as duas chegam ao mesmo nível, e a rede chega mais barato.

## Slide 15: Conclusões

**Roteiro (o que falar)** · Bernan · 0:35

Para concluir. A SVM RBF teve a melhor acurácia, 85,4%, mas a vantagem sobre uma reta é menor que um ponto. O modelo final depende do critério: pela acurácia, a SVM RBF; pela AUC, pelo F1 macro e pelo custo, a rede neural. Da SVM, ficam três lições: padronizar é obrigatório no RBF, C e gamma têm uma faixa boa e não um ponto ótimo, e o custo cresce com o quadrado dos dados. Obrigado.

> Bernan conduz as perguntas.

**Para estudar** (apoio; não faz parte da fala)

- Pesos por classe (class_weight=‘balanced’), testados no notebook 05: os falsos negativos caem de 587 para 221 e os falsos positivos sobem de 294 para 929; a acurácia cai para 80,9%. Útil se perder uma pessoa de renda alta custar mais que um alarme falso.
- Repositório: github.com/pumba-dev/machine-learning-practice, pasta renda/.

**Perguntas prováveis**

- **P:** Dá para reduzir os falsos negativos da SVM?  
  **R:** Sim, com pesos por classe: a classe pequena passa a valer mais no treino. Os falsos negativos caem de 587 para 221, mas os falsos positivos triplicam. É uma troca, e a melhor versão depende do custo de cada erro.

- **P:** Quando vale a pena usar SVM com kernel?  
  **R:** Em bases de até algumas dezenas de milhares de linhas, com fronteira curva e atributos padronizados. Acima disso, o custo de n² pesa e a SVM linear ou uma rede costumam ser melhor escolha.
