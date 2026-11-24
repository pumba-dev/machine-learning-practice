# Roteiro da quinta apresentação (10 min)

Cada slide traz o roteiro (o que falar), um material de estudo e perguntas prováveis. O estudo e as perguntas servem para dominar o assunto e não fazem parte da fala. As mesmas notas estão no .pptx.

# Bloco 1 · Thiago · slides 1 a 5: O problema e o preparo dos dados

## Slide 1: K-means na base de renda

**Roteiro (o que falar)** · Thiago · 0:25

Bom dia, professor e colegas. Eu sou o Thiago e, com o Paulo e o Bernan, vou apresentar a quinta parte do trabalho. A base é a mesma da SVM, as pessoas do censo americano, mas a pergunta muda: em vez de prever a renda, queremos descobrir que grupos de pessoas existem nessa base. O algoritmo é o K-means, o primeiro método não supervisionado do trabalho.

**Para estudar** (apoio; não faz parte da fala)

- Disciplina: PPGCC010 – Aprendizagem de Máquina (UFPI, 2026.2), Prof. Vinicius Ponte Machado.
- Tudo no repositório, pasta renda/: notebook 07_kmeans, módulo src/clusters.py, resultados em renda/resultados/clusters_*.csv.
- Biblioteca: scikit-learn (KMeans, silhouette_score, davies_bouldin_score, adjusted_rand_score, PCA).
- O professor pediu K-means; o agrupamento hierárquico (Ward) ficou de fora por decisão do grupo.

**Perguntas prováveis**

- **P:** Por que usar a mesma base da SVM?  
  **R:** Porque já conhecemos bem os atributos e a renda. Assim dá para conferir, no fim, se os grupos encontrados sem a renda têm relação com ela, e comparar com o que os classificadores alcançaram.

## Slide 2: Agora o modelo não vê a resposta

**Roteiro (o que falar)** · Thiago · 0:35

Até agora, todos os modelos eram supervisionados: recebiam os atributos e a resposta, a renda, e aprendiam a prever. O K-means é não supervisionado: recebe só os atributos e procura grupos de pessoas parecidas entre si. Usamos as mesmas 30.139 pessoas e os mesmos 10 atributos da SVM. Não há divisão em treino e teste, porque não há resposta a acertar. A renda entra só no final, para conferir se os grupos têm alguma relação com ela.

**Para estudar** (apoio; não faz parte da fala)

- Supervisionado: aprende uma função atributos → rótulo. Não supervisionado: descobre estrutura só nos atributos (grupos, direções de variação, anomalias).
- Sem treino e teste: o agrupamento é feito na base inteira. Não há vazamento, porque a renda nunca entra no ajuste.
- Atributos: idade, anos de estudo, ganho e perda de capital, horas por semana; classe de trabalho, estado civil, ocupação, relacionamento, país.

**Perguntas prováveis**

- **P:** Se não há resposta, como saber se o resultado é bom?  
  **R:** Com métricas internas, que olham só os atributos: compacidade e separação dos grupos (inércia, silhueta, Davies-Bouldin) e estabilidade entre seeds. A renda serve como conferência externa no fim.

## Slide 3: Como o K-means funciona

**Roteiro (o que falar)** · Thiago · 0:40

O K-means funciona em quatro passos. Primeiro, escolhe k pontos como centros iniciais. Segundo, cada pessoa vai para o centro mais próximo. Terceiro, cada centro passa a ser a média das pessoas do seu grupo. E repete os passos dois e três até os grupos pararem de mudar. O objetivo é deixar os grupos compactos: a soma das distâncias de cada pessoa ao seu centro, a inércia, deve ser a menor possível. Como o resultado depende do sorteio inicial, rodamos dez inicializações e ficamos com a melhor.

**Para estudar** (apoio; não faz parte da fala)

- Inércia: soma, para todas as pessoas, da distância euclidiana ao quadrado até o centro do seu grupo.
- k-means++: o primeiro centro é uma pessoa sorteada; os seguintes são sorteados com mais chance para pessoas longe dos centros já escolhidos. Espalha os centros e evita começos ruins.
- n_init = 10: o algoritmo roda 10 vezes, com 10 sorteios de centros, e devolve a de menor inércia.
- Seed: fixa o gerador dos sorteios; a mesma seed dá sempre as mesmas 10 inicializações.
- Custo: proporcional a pessoas × k × colunas × iterações; cresce linearmente com o número de pessoas.
- Limite: o algoritmo sempre converge, mas para um mínimo local, não necessariamente o melhor possível.

**Perguntas prováveis**

- **P:** O K-means sempre acha a melhor divisão?  
  **R:** Não. Ele sempre converge, mas para um mínimo local, que depende dos centros iniciais. Por isso as 10 inicializações; mais adiante mostramos o que acontece com uma só.

- **P:** Quem escolhe o k?  
  **R:** Nós. O K-means não descobre o número de grupos; testamos k de 2 a 10 e escolhemos com métricas e com a leitura dos grupos.

## Slide 4: A distância decide tudo

**Roteiro (o que falar)** · Thiago · 0:40

Como tudo depende da distância, o preparo dos dados é decisivo. São 80 colunas: os cinco numéricos com padronização, média zero e desvio um, e os cinco atributos de texto em one-hot, uma coluna de zero ou um por categoria. Isso cria um efeito curioso: duas pessoas com ocupações diferentes diferem em duas colunas, e ficam tão distantes quanto duas pessoas com 19 anos de diferença de idade. Em média, os atributos de texto respondem por 37% da distância; o país quase nada, porque quase todos são dos Estados Unidos.

**Para estudar** (apoio; não faz parte da fala)

- Padronização (z-score): (valor − média) / desvio padrão. Não é o mesmo que normalização (min-max), que leva os valores para o intervalo de 0 a 1 e depende só do mínimo e do máximo.
- One-hot: classe de trabalho 7 colunas, estado civil 7, ocupação 14, relacionamento 6, país 41: 75 colunas.
- Numa troca de categoria, uma coluna vai de 1 a 0 e outra de 0 a 1: distância ao quadrado 1² + 1² = 2, igual a √2 ≈ 1,41 desvio num numérico. Na idade (desvio de 13,1 anos), 18,6 anos.
- Peso médio de um atributo: 2 × variância das suas colunas. Numérico padronizado: 2. Categórico: 2 × (1 − Σp²), a chance de duas pessoas sorteadas terem categorias diferentes, vezes 2.
- Partes da distância média: ocupação 11,3%, relacionamento 9,2%, estado civil 8,3%, classe de trabalho 5,6%, país 2,1%; cada numérico 12,7%.

**Perguntas prováveis**

- **P:** Padronização é o mesmo que normalização?  
  **R:** Não. Padronização deixa cada atributo com média 0 e desvio 1; normalização (min-max) leva os valores para o intervalo de 0 a 1 e depende só do mínimo e do máximo. Usamos padronização.

- **P:** Por que não dar outro peso aos atributos de texto?  
  **R:** Daria para reescalar as colunas one-hot, mas toda escolha muda o que é ‘parecido’. Mantivemos o one-hot puro, o mesmo da SVM, e mostramos o peso de cada atributo para ajudar a ler os grupos.

## Slide 5: O capital pede log e ainda forma grupos

**Roteiro (o que falar)** · Thiago · 0:45

O ganho e a perda de capital são zero para quase todo mundo e enormes para poucos. Sem nenhum ajuste, as 148 pessoas com ganho de 99.999 dólares, o teto do censo, ficam a 13 desvios da média e formam um grupo só delas. Aplicamos o logaritmo antes da padronização, e esse grupo desaparece. Mas surge outro efeito: ter ou não ter capital vira o maior salto da base. Quem tem ganho, cerca de 2.510 pessoas, e quem tem perda, 1.427, formam grupos próprios. Ou seja, dois grupos ficam com os 13% que têm capital, e os outros grupos dividem o resto.

> Passagem para Paulo: “Com os dados preparados, quantos grupos pedir ao K-means?”

**Para estudar** (apoio; não faz parte da fala)

- Com ganho de capital: 8,4% das pessoas; com perda: 4,7%.
- Log usado: log(1 + x), porque log(0) não existe. 99.999 → 11,5; 15.024 → 9,6; 7.688 → 8,9; 0 → 0.
- Sem log (k = 4, seed 42): grupos de 16.888, 11.709, 1.394 (perda de capital) e 148 (ganho de 99.999, 100% acima de 50 mil).
- Com log: grupos de 15.496, 10.706, 2.510 (todos com ganho, 63,5% acima de 50 mil) e 1.427 (todos com perda, 51,6%).
- Por que o salto: com log, quem tem zero fica em -0,30 desvio e quem tem algum ganho fica perto de +3; a diferença ao quadrado passa de 10, mais que qualquer troca de categoria (2).
- Alternativas avaliadas e não usadas: capital como ‘tem / não tem’ (0 ou 1) ou fora do agrupamento.

**Perguntas prováveis**

- **P:** O log não deveria ter resolvido o problema do capital?  
  **R:** Resolveu o dos extremos: o grupo das 148 pessoas com 99.999 sumiu. Mas comprimir os valores aproxima quem tem capital entre si e mantém o salto em relação a quem tem zero. Os grupos do capital que aparecem são reais e têm sentido: concentram a renda alta.

# Bloco 2 · Paulo · slides 6 a 10: A escolha do k: métricas internas e estabilidade

## Slide 6: Três métricas para escolher o k

**Roteiro (o que falar)** · Paulo · 0:40

Obrigado, Thiago. O K-means não escolhe o número de grupos; somos nós que escolhemos o k. Testamos de 2 a 10, e para cada k usamos três métricas que olham só os atributos, nunca a renda. A inércia mede a compacidade e sempre cai quando k aumenta, então procuramos o cotovelo, o ponto em que ela para de cair rápido. A silhueta pergunta se cada pessoa está mais perto do próprio grupo do que do vizinho: quanto maior, melhor. E o Davies-Bouldin mede a sobreposição entre grupos: quanto menor, melhor.

**Para estudar** (apoio; não faz parte da fala)

- Silhueta de uma pessoa: (b − a) / máx(a, b), com a = distância média ao próprio grupo e b = distância média ao grupo vizinho mais próximo. Vai de −1 a 1; a métrica é a média.
- A silhueta compara todos os pares (custo de ordem n²): calculada numa amostra fixa de 10 mil pessoas, a mesma em todos os ajustes.
- Davies-Bouldin: para cada grupo, o pior caso de (espalhamento do grupo + espalhamento do vizinho) / distância entre os centros; a métrica é a média. Mínimo 0.
- Cada k foi rodado com as 10 seeds (0 a 9), cada uma com 10 inicializações: 90 ajustes.

**Perguntas prováveis**

- **P:** Por que não escolher o k com a menor inércia?  
  **R:** Porque a inércia sempre cai com k: com uma pessoa por grupo, ela é zero. O que interessa é onde ela deixa de cair rápido, o cotovelo.

## Slide 7: As métricas internas não apontam um k claro

**Roteiro (o que falar)** · Paulo · 0:40

E as métricas não apontam um k claro. Silhueta e Davies-Bouldin preferem k igual a 2, mas esse k só separa quem tem ganho de capital do resto: é a fronteira mais nítida da base, e diz pouco sobre as pessoas. De k igual a 4 em diante, as duas curvas ficam planas, com silhueta em torno de 0,17. Isso é baixo: indica que a base não tem grupos bem separados. Os grupos são regiões de uma nuvem contínua. Na inércia, o cotovelo fica entre 5 e 6.

**Para estudar** (apoio; não faz parte da fala)

- Silhueta média por k: 2: 0,31; 5: 0,17; 6: 0,17; 8: 0,15. Acima de 0,5 indicaria grupos bem separados.
- Davies-Bouldin: 2: 1,27; de 3 a 10, entre 1,66 e 1,72.
- Quedas da inércia: 2→3 28.411; 3→4 24.702; 4→5 15.082; 5→6 8.492; depois, entre 4 e 6 mil.
- Em k = 2, 9 seeds separam quem tem ganho (2.533 pessoas) e uma separa quem tem perda (1.427).

**Perguntas prováveis**

- **P:** Silhueta de 0,17 não quer dizer que o agrupamento falhou?  
  **R:** Quer dizer que os grupos não são ilhas separadas: as pessoas variam de forma contínua. O K-means sempre divide; o que avaliamos é se a divisão é estável e interpretável, e ela é.

## Slide 8: As 10 seeds acham os mesmos grupos?

**Roteiro (o que falar)** · Paulo · 0:35

Como as métricas empatam, olhamos a estabilidade. Para cada k, as dez seeds geram dez partições, e comparamos todos os pares pelo ARI, que vale 1 quando duas partições põem as mesmas pessoas juntas e zero quando a concordância é a do acaso. Com k igual a 5, 6 e 8, as dez seeds chegam praticamente aos mesmos grupos, com ARI de 0,98 ou mais. Já k igual a 3 e 9 são instáveis: cada seed divide de um jeito.

**Para estudar** (apoio; não faz parte da fala)

- ARI (Adjusted Rand Index): conta os pares de pessoas que as duas partições põem juntas ou separadas, corrigido pelo acaso. Não depende do número dado a cada grupo.
- 45 pares de seeds por k (10 seeds, combinadas duas a duas).
- ARI médio: 3: 0,59; 5: 0,977; 6: 0,995; 7: 0,93; 8: 0,997; 9: 0,79.
- Um k instável sugere que o algoritmo corta uma região sem fronteira natural.

**Perguntas prováveis**

- **P:** O número de cada grupo muda entre seeds. O ARI não se confunde?  
  **R:** Não. O ARI olha só se cada par de pessoas está junto ou separado nas duas partições; os nomes dos grupos não importam.

## Slide 9: 10 inicializações compram estabilidade

**Roteiro (o que falar)** · Paulo · 0:35

Essa estabilidade vem das dez inicializações. Se cada seed fizer um sorteio só, cada uma para num mínimo local diferente: com k igual a 6, o ARI cai de 0,995 para 0,59, e a inércia piora em média 3%. Com dez inicializações, o ajuste leva menos de um segundo, 0,9 segundo nas 30 mil pessoas. É um custo pequeno para ter sempre a mesma resposta.

**Para estudar** (apoio; não faz parte da fala)

- Com 1 inicialização, o ARI médio fica entre 0,56 e 0,86 para k de 2 a 10.
- Tempo por ajuste (k = 6, mediana, um núcleo): 0,89 s com 10 inicializações, 0,12 s com uma.
- Estudo inteiro: 180 ajustes (9 k × 10 seeds, com 10 inicializações e com uma), cerca de 4 minutos.

**Perguntas prováveis**

- **P:** Então basta aumentar o número de inicializações?  
  **R:** Até certo ponto: 10 já bastam para que as seeds concordem nos k estáveis. Nos k instáveis (3 e 9), o problema é a falta de fronteira nos dados, e mais inicializações não resolvem.

## Slide 10: Escolhemos k = 6

**Roteiro (o que falar)** · Paulo · 0:40

Juntando tudo, escolhemos k igual a 6. O cotovelo da inércia fica entre 5 e 6; silhueta e Davies-Bouldin estão planas, então não desempatam; a estabilidade é quase perfeita, com ARI de 0,995; e, como dois grupos ficam com o capital, k igual a 6 deixa quatro grupos para quem não tem capital, com perfis bem distintos.

> Passagem para Bernan: “Com k = 6, quem são esses grupos?”

**Para estudar** (apoio; não faz parte da fala)

- k = 5 (ARI 0,977): só três grupos sem capital; junta os mais velhos sem cônjuge com os casados em ofícios manuais.
- k = 8 (ARI 0,997): seis grupos sem capital, alguns difíceis de distinguir (por exemplo, jovens de meio período e quem trabalha 66 h por semana).
- A escolha do k combina métricas e interpretação: não existe um k ‘correto’ em agrupamento.
- Partição descrita: seed 42, fora das seeds 0 a 9; coincide com as 10 seeds (ARI de 0,977 a 0,999).

**Perguntas prováveis**

- **P:** Por que não k = 2, que tem a melhor silhueta?  
  **R:** Porque k = 2 só separa quem tem ganho de capital. É a divisão mais nítida, mas descreve 8% das pessoas e deixa as outras 92% num grupo só.

# Bloco 3 · Bernan · slides 11 a 15: Os grupos, a renda e as conclusões

## Slide 11: Seis perfis de pessoas

**Roteiro (o que falar)** · Bernan · 0:45

Obrigado, Paulo. Estes são os seis grupos, numerados do menor para o maior percentual de renda alta. Os jovens solteiros, com 26 anos em média, muitos morando com os pais. Os mais velhos sem cônjuge, com 53 anos, divorciados e viúvos. Os casados em ofícios manuais, que trabalham 48 horas por semana. Os profissionais com muito estudo, 13,3 anos em média. E os dois grupos do capital, perda e ganho. Os quatro primeiros se separam pela fase da vida e pelo tipo de trabalho; os dois últimos, pelo capital.

**Para estudar** (apoio; não faz parte da fala)

- Grupo 1: 8.439 pessoas; Never-married (82%); Own-child (45%); 34 h/semana.
- Grupo 2: 5.443; 8,5 anos de estudo; casados só 37%, divorciados 34%, viúvos 11%.
- Grupo 3: 6.538; Married-civ-spouse (90%); Husband (84%); Craft-repair (26%).
- Grupo 4: 5.791; Prof-specialty (40%), mais 25% de gerentes; 45 h/semana.
- Grupo 5: 1.427; todos com perda de capital (média de 1.868 dólares).
- Grupo 6: 2.501; todos com ganho de capital (média de 13.157 dólares).
- Os nomes são nossos, tirados do perfil; o K-means só devolve números.

**Perguntas prováveis**

- **P:** Os nomes dos grupos vêm do algoritmo?  
  **R:** Não. O K-means devolve só um número por pessoa. Os nomes resumem o perfil médio de cada grupo, e há pessoas diferentes desse perfil dentro dele.

## Slide 12: Os grupos seguem a renda sem tê-la visto

**Roteiro (o que falar)** · Bernan · 0:35

Só agora olhamos a renda. O K-means nunca a viu, e mesmo assim os grupos se ordenam por ela: 1,1% dos jovens solteiros ganham mais de 50 mil, contra 44,8% dos profissionais com muito estudo e 63,8% de quem tem ganho de capital. Na base inteira, são 24,9%. Os atributos que formam os grupos, como idade, estudo, estado civil e capital, são os mesmos que explicam a renda.

**Para estudar** (apoio; não faz parte da fala)

- % acima de 50 mil por grupo: 1: 1,1%; 2: 12,6%; 3: 27,5%; 4: 44,8%; 5: 51,6%; 6: 63,8%.
- A ordem dos números dos grupos foi feita depois, pelo % de renda alta, só para facilitar a leitura.

**Perguntas prováveis**

- **P:** Se a renda não entrou, como os grupos ficaram ordenados por ela?  
  **R:** Porque a renda depende dos mesmos atributos que definem os grupos: idade, estudo, estado civil, ocupação e capital. Pessoas parecidas nesses atributos tendem a ter rendas parecidas.

## Slide 13: Os grupos descrevem, não preveem

**Roteiro (o que falar)** · Bernan · 0:45

Mas os grupos descrevem, não preveem. Se cada grupo chutasse a renda da sua maioria, acertaria 77,5% das pessoas; essa é a pureza. Responder ‘até 50 mil’ para todos já acerta 75,1%, só 2,4 pontos a menos, e a SVM acerta 85,4%. Nenhum grupo é puro: no grupo dos profissionais, a chance de renda alta é de 45%, quase cara ou coroa. O K-means junta pessoas parecidas em tudo; o classificador aprende com a renda o que importa para ela.

**Para estudar** (apoio; não faz parte da fala)

- Pureza: cada grupo responde a classe mais comum entre as suas pessoas; é a fração de acertos. Grupos 1 a 4 respondem ‘≤50K’; 5 e 6, ‘>50K’.
- ARI contra a renda: 0,09, perto do acaso. Com 6 grupos e 2 classes, o ARI não chegaria a 1 nem com grupos puros, por isso a pureza é a métrica mais fácil de ler.
- Pessoas de renda alta nos grupos 3 e 4, que respondem ‘≤50K’: cerca de 1.800 e 2.600.
- SVM RBF: 85,4% de acurácia média no teste (10 seeds), na mesma base.

**Perguntas prováveis**

- **P:** Então o K-means não serve para nada aqui?  
  **R:** Serve para descrever a população: mostra que perfis existem e onde a renda alta se concentra. Para prever a renda de uma pessoa, um classificador treinado com a renda é muito melhor.

- **P:** A pureza e a acurácia são comparáveis?  
  **R:** Aproximadamente: a pureza é a acurácia de um classificador que responde a classe da maioria do grupo, medida na base inteira. Serve como ordem de grandeza.

## Slide 14: Grupos são regiões de uma nuvem contínua

**Roteiro (o que falar)** · Bernan · 0:35

Este gráfico projeta as 80 colunas em duas dimensões, as duas direções em que a base mais varia. Os dois grupos do capital ficam isolados, um em cima e outro embaixo. Os outros quatro se encostam numa nuvem contínua, dos jovens solteiros, à esquerda, aos profissionais, à direita. Isso explica a silhueta baixa. A ressalva é que a projeção mostra só 33% da variação dos dados.

**Para estudar** (apoio; não faz parte da fala)

- PCA (análise de componentes principais): encontra as direções de maior variância e projeta os pontos nelas. Usada só para desenhar; o K-means agrupou nas 80 colunas.
- Componente 1: 19,5% da variância; componente 2: 13,5%.
- Amostra de 1.500 pessoas no slide, para o desenho não virar uma mancha; os centros usam todas.

**Perguntas prováveis**

- **P:** Grupos que se sobrepõem no gráfico não estão errados?  
  **R:** Não necessariamente: o gráfico mostra só duas direções, 33% da variação. Nas outras, os grupos podem estar separados. Mas a sobreposição combina com a silhueta baixa.

## Slide 15: Conclusões

**Roteiro (o que falar)** · Bernan · 0:40

Para concluir. O K-means encontrou seis perfis de pessoas, estáveis entre seeds, que se ordenam pela renda sem nunca a ter visto. A base não tem grupos nítidos: são regiões de uma nuvem contínua, e o capital domina a distância, mesmo com logaritmo. Os grupos servem para descrever a população; para prever a renda, um classificador é muito melhor. E o custo é baixo: menos de um segundo por ajuste, crescendo linearmente com o número de pessoas. Obrigado; ficamos à disposição para perguntas.

> Bernan conduz as perguntas.

**Para estudar** (apoio; não faz parte da fala)

- Lições: a distância decide tudo (escala, one-hot, log); métricas internas sozinhas não escolhem o k; estabilidade e interpretação completam a escolha.
- Trabalhos futuros: algoritmos para atributos mistos (k-prototypes), capital como ‘tem / não tem’, mistura de gaussianas, que dá a cada pessoa uma probabilidade de pertencer a cada grupo.

**Perguntas prováveis**

- **P:** O que vocês fariam diferente?  
  **R:** Testaríamos uma distância própria para dados mistos, como no k-prototypes, que trata as categorias sem one-hot, e o capital como ‘tem / não tem’, para que ele não ocupe dois grupos.
