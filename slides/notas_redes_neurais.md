# Roteiro da terceira apresentação (10 min)

Cada slide traz o roteiro (o que falar), um material de estudo e perguntas prováveis. O estudo e as perguntas servem para dominar o assunto e não fazem parte da fala. As mesmas notas estão no .pptx.

# Bloco 1 · Thiago · slides 1 a 3: A base e o degrau no score

## Slide 1: Redes neurais na aprovação de empréstimos

**Roteiro (o que falar)** · Thiago · 0:20

Bom dia, professor e colegas. Eu sou o Thiago e, com o Paulo e o Bernan, vou apresentar a terceira parte do trabalho. A base mudou: em vez de moléculas, pedidos de empréstimo. E o modelo também: agora é uma rede neural, que comparamos com a árvore de decisão e com modelos mais simples, inclusive no tempo de execução.

**Para estudar** (apoio; não faz parte da fala)

- Disciplina: PPGCC010 – Aprendizagem de Máquina (UFPI, 2026.2), Prof. Vinicius Ponte Machado.
- Tudo no relatório atualizado (Seção 7) e nos notebooks 01 a 04 da pasta emprestimos/ do repositório.
- Biblioteca: scikit-learn (MLPClassifier), a mesma das partes anteriores.

**Perguntas prováveis**

- **P:** Por que scikit-learn e não PyTorch ou TensorFlow?  
  **R:** A base é pequena e tabular, e a rede tem poucas camadas. O MLPClassifier do scikit-learn basta e permite usar o mesmo protocolo (divisão, validação cruzada, busca em grade) dos outros modelos.

## Slide 2: 4.269 pedidos de empréstimo, 11 atributos

**Roteiro (o que falar)** · Thiago · 0:55

A base vem do Kaggle: 4.269 pedidos de empréstimo, cada um com 11 atributos. Há dados de quem pede, como dependentes, escolaridade e se é autônomo; de dinheiro, como renda, valor pedido e quatro tipos de patrimônio; o prazo; e o score de crédito, de 300 a 900. O rótulo diz se o pedido foi aprovado: 62,2% foram. Então responder sempre ‘aprovado’ já acerta 62,2%, e esse é o piso. A curadoria foi curta: não há valores ausentes nem linhas repetidas. O único problema foram 28 pedidos com patrimônio residencial negativo, que trocamos por zero.

**Para estudar** (apoio; não faz parte da fala)

- Kaggle: ‘Loan-Approval-Prediction-Dataset’, de architsharma01 (versão 1, 2023, licença MIT). O arquivo é conferido pelo hash SHA-256 no notebook 01.
- Os 28 negativos eram todos −100.000. A aprovação nessas linhas (57%) é parecida com a geral (62,2%), então parece erro de digitação; mantivemos as linhas e trocamos o valor por 0, que já aparece em outros 45 pedidos.
- Nomes e textos vinham com espaço no início (‘ Approved’); removemos. Os textos viraram 0/1 (Graduate = 1, Yes = 1, Approved = 1).
- A página não diz a moeda. O score é do CIBIL, o birô de crédito da Índia, então devem ser rúpias. Para os modelos, a moeda não importa.
- Base provavelmente sintética: score e renda quase uniformes (quartis do score 453, 600, 748, contra 450, 600 e 750 de uma uniforme de 300 a 900); escolaridade e autônomo quase 50/50.

**Perguntas prováveis**

- **P:** Por que não apagar as linhas com valor negativo?  
  **R:** Porque o resto da linha parece normal e a taxa de aprovação delas é parecida com a geral. Trocar só o valor impossível preserva os outros 10 atributos e o rótulo.

- **P:** A base é real?  
  **R:** Provavelmente não: as distribuições são quase uniformes e o rótulo segue uma regra quase exata, como mostra o próximo slide. Isso limita o alcance das conclusões, e o relatório discute isso.

## Slide 3: A aprovação salta em 550 de score

**Roteiro (o que falar)** · Thiago · 1:05

A análise exploratória mostrou que um atributo decide quase tudo: o score de crédito. O gráfico mostra a taxa de aprovação por faixa de score. Abaixo de 550, só cerca de 10% dos pedidos são aprovados; a partir de 550, praticamente todos. Não é uma rampa, é um degrau. A regra ‘aprovar se o score for pelo menos 550’ acerta 95,4% da base. E os poucos aprovados abaixo de 550 têm todos prazo curto, de 2 ou 4 anos. Ou seja, os rótulos seguem quase uma regra explícita. Isso vai ser importante para entender o resultado da rede.

> Passagem para Paulo: “Se uma regra simples já acerta 95%, o que uma rede neural acrescenta?”

**Para estudar** (apoio; não faz parte da fala)

- Correlação com a aprovação: score 0,77; prazo −0,11; os outros nove atributos perto de zero.
- Renda × valor do empréstimo: 0,93; renda × bens de luxo: 0,93. Os valores em dinheiro são redundantes entre si.
- Abaixo de 550: aprovação de 48% com prazo de 2 anos, 57% com 4 anos e 0% com 6 anos ou mais.
- Nos modelos, a ‘regra de um corte’ é uma árvore de profundidade 1: ela escolhe sozinha o atributo e o limiar no treino. Escolheu o score e 549,5 nas 10 seeds, sem olhar o teste.

**Perguntas prováveis**

- **P:** Se uma regra já acerta 95%, para que um modelo?  
  **R:** Para medir se o modelo descobre a regra e a exceção dos prazos curtos sozinho. A regra de um corte é a régua mínima: um modelo que fique abaixo dela não aprendeu nada útil.

- **P:** O 550 não foi escolhido olhando o teste?  
  **R:** Não. Nos modelos, o limiar é aprendido só com o treino de cada seed (deu 549,5 em todas). O 550 deste slide é da análise exploratória, para descrever a base.

# Bloco 2 · Paulo · slides 4 a 6: A rede neural: padronização, épocas e paciência

## Slide 4: A rede neural: neurônios em camadas

**Roteiro (o que falar)** · Paulo · 1:10

Antes do resultado, como funciona a rede. Cada neurônio faz uma conta simples: multiplica cada entrada por um peso, soma tudo e passa o resultado por uma função de ativação. Nas camadas ocultas, usamos a ReLU, que deixa passar os positivos e zera os negativos. Na saída, um neurônio com sigmoide dá um número entre 0 e 1: a probabilidade de aprovação. Se for acima de 50%, a rede diz ‘aprovado’. Os pesos começam sorteados. No treino, a rede vê os pedidos, mede o erro e ajusta cada peso um pouco na direção que reduz o erro. Uma passada completa por todo o treino é uma época. Um detalhe: uma rede com um único neurônio sigmoide é exatamente a regressão logística, que também comparamos.

**Para estudar** (apoio; não faz parte da fala)

- Neurônio: z = w1·x1 + … + w11·x11 + b; saída = ativação(z). ReLU(z) = max(0, z). Sigmoide(z) = 1/(1 + e^−z).
- Perda: entropia cruzada, que pune muito uma probabilidade alta dada à classe errada.
- Retropropagação (backpropagation): calcula quanto cada peso contribuiu para o erro, da saída para trás. Otimizador Adam: ajusta o tamanho do passo de cada peso sozinho. Taxa de aprendizado: o tamanho base do passo.
- A arquitetura do diagrama (32 e 16 neurônios) foi a mais escolhida pela busca em grade (7 das 10 seeds).
- Neurônios (validação cruzada, seed 42): 1 neurônio → 93,4%; 4 numa camada → 97,2%; 8 em duas camadas → 98,0%; 64 numa camada → 95,4%. Mais neurônios não ajudam.

**Perguntas prováveis**

- **P:** Por que ReLU e não sigmoide nas camadas ocultas?  
  **R:** A ReLU é simples de calcular e não ‘satura’ para valores positivos, o que facilita o treino. A sigmoide fica só na saída, onde precisamos de uma probabilidade.

- **P:** Quantos pesos tem essa rede?  
  **R:** 11×32 + 32 = 384 na primeira camada, 32×16 + 16 = 528 na segunda e 16 + 1 = 17 na saída: 929 no total.

## Slide 5: Sem padronização, a rede não aprende

**Roteiro (o que falar)** · Paulo · 0:55

O primeiro cuidado é a padronização. Os atributos têm escalas muito diferentes: dependentes vão de 0 a 5, e a renda chega a quase 10 milhões. Sem ajustar isso, a soma de cada neurônio fica dominada pelos valores em dinheiro, e o treino não funciona. A mesma rede, nas 10 seeds, acerta 59,5% sem padronização, abaixo até do piso de 62,2%. Com padronização, 93,9%. Padronizar é, para cada atributo, subtrair a média e dividir pelo desvio padrão: todos passam a ficar em torno de zero, na mesma escala. E a média e o desvio vêm só do treino, para o teste não vazar.

**Para estudar** (apoio; não faz parte da fala)

- Sem padronização: 59,5 ± 3,1%, AUC 51,0% (sorteio = 50%). Com: 93,9 ± 0,7%, AUC 98,1%. Rede de 16 neurônios, 10 seeds.
- Exemplo: renda de 5 milhões, média 5,06 milhões e desvio 2,8 milhões → (5,0 − 5,06) / 2,8 ≈ −0,02. Dependentes = 4, média 2,5 e desvio 1,7 → (4 − 2,5) / 1,7 ≈ 0,9. Depois disso, os dois são comparáveis.
- Por que importa: o passo do otimizador é parecido para todos os pesos; um passo que serve a um atributo de 0 a 5 é minúsculo para um de 0 a 40 milhões, e vice-versa (LeCun et al., 1998).
- No código, a padronização (StandardScaler) fica dentro de um Pipeline com a rede: em cada treino da validação cruzada, ela é recalculada só com aquele treino.
- A árvore não precisa disso: ela só compara cada atributo com um limiar, e mudar a escala não muda a ordem dos valores.

**Perguntas prováveis**

- **P:** Por que sem padronização fica abaixo do piso, e não no piso?  
  **R:** Porque ela não aprendeu nada útil, e errar mais que o piso é possível quando o modelo prevê ao acaso. A AUC de 51% confirma: ela não ordena os pedidos melhor que um sorteio. O desvio de 3 pontos entre seeds também mostra que o resultado é instável.

- **P:** Padronizar com a média de toda a base seria errado?  
  **R:** Seria um vazamento pequeno: o teste influenciaria a média. Por isso o Pipeline calcula a média e o desvio só no treino de cada divisão.

## Slide 6: Épocas e paciência: quando parar o treino

**Roteiro (o que falar)** · Paulo · 1:15

O segundo cuidado é quando parar o treino. A cada época a rede melhora no treino, mas a partir de um ponto passa a decorar o treino, e não a aprender. Por isso usamos parada antecipada: separamos 10% do treino como validação e paramos quando a validação passa um certo número de épocas sem melhorar. Esse número é a paciência. O gráfico mostra a acurácia de validação de uma rede com duas taxas de aprendizado. Com a taxa menor, a rede aprende devagar e fica um tempo parada perto de 92%. Com a paciência padrão do scikit-learn, de 10 épocas, o treino pararia na época 37, com 92,1%, quando a mesma rede chegaria a 96,5%. Por isso usamos paciência 30 e colocamos a taxa na busca em grade. A busca escolheu a taxa maior nas 10 seeds.

> Passagem para Bernan: “Com a rede ajustada, como ela se sai contra os outros modelos?”

**Para estudar** (apoio; não faz parte da fala)

- Época: uma passada completa pelos pedidos de treino. Paciência: quantas épocas seguidas sem melhora (de pelo menos 0,0001) a rede tolera antes de parar.
- Taxa 0,001: paciência 10 → para na época 37 (92,1%); paciência 30 → época 217 (95,5%); melhor das 400 épocas: 96,5%.
- Taxa 0,01: paciência 10 → época 54 (96,8%); paciência 30 → época 94 (97,1%); melhor: 97,4%.
- A perda de treino continua caindo enquanto a de validação se estabiliza: é o começo do sobreajuste (overfitting). A figura do relatório (Figura de épocas) mostra as duas perdas.
- Busca em grade: 24 combinações (6 arquiteturas × 2 regularizações L2 × 2 taxas), validação cruzada de 5 partes. Escolheu duas camadas em 9 das 10 seeds; a rede final treinou de 40 a 121 épocas.

**Perguntas prováveis**

- **P:** A parada antecipada não desperdiça 10% do treino?  
  **R:** Um pouco, sim: a rede final ajusta os pesos com 90% do treino. Em troca, para sozinha no ponto certo, sem precisar fixar o número de épocas.

- **P:** Por que não treinar sempre 400 épocas?  
  **R:** Depois do melhor ponto a validação cai ou fica parada, e o tempo de treino cresce sem ganho. Na busca em grade, com 120 redes por seed, isso pesaria muito no tempo.

# Bloco 3 · Bernan · slides 7 a 10: Resultado, tempo, onde a rede erra e conclusão

## Slide 7: A rede supera a logística, mas não a árvore

**Roteiro (o que falar)** · Bernan · 1:05

Com a rede ajustada, comparamos seis modelos com a mesma régua das partes anteriores: 10 seeds, treino e teste estratificados, e busca de hiperparâmetros só dentro do treino. A rede acerta 96,4%. Ela supera a regressão logística nas 10 seeds, em 4,5 pontos: as camadas ocultas fazem diferença. Mas, contra a regra de um corte, a vantagem é de só 0,9 ponto, menor que a variação entre seeds. E a árvore de decisão, com 98,1%, vence a rede em todas as 10 seeds. A Random Forest empata com a árvore.

**Para estudar** (apoio; não faz parte da fala)

- Acurácias (10 seeds): classe majoritária 62,2%; regressão logística 91,9 ± 1,1%; regra de um corte 95,5 ± 0,6%; rede 96,4 ± 1,1%; árvore 98,1 ± 0,4%; Random Forest 98,3 ± 0,4%.
- Seed a seed (pontos de acurácia): rede − logística +4,5 (10/10); rede − regra +0,9 (8/10, 1 empate); rede − árvore −1,7 (0/10); rede − floresta −1,9 (1/10).
- AUC (ordena bem os pedidos?): rede 99,3%, árvore 98,7%, floresta 99,8%. A rede ordena melhor que a árvore; o que ela erra é o corte em 50%.
- A rede é a menos estável: desvio de 1,1 ponto, quase 3 vezes o da árvore (0,4).

**Perguntas prováveis**

- **P:** A diferença para a árvore não é ruído?  
  **R:** Não: a árvore vence nas 10 seeds, com diferença média de 1,7 ponto e desvio de 0,9. Já contra a regra, a vantagem da rede é menor que o desvio.

- **P:** Como a AUC da rede pode ser maior se ela acerta menos?  
  **R:** A AUC olha a ordem das probabilidades, não o corte. A rede põe quase sempre o aprovado acima do rejeitado, mas perto do degrau dá probabilidades intermediárias, e o corte em 50% erra alguns.

## Slide 8: A rede custa mais tempo, sobretudo na busca

**Roteiro (o que falar)** · Bernan · 0:55

Na apresentação anterior, o professor perguntou sobre o tempo de execução. Desta vez medimos: tudo num único núcleo, com uma rodada de aquecimento descartada e a mediana das 10 seeds. Treinar a rede final leva cerca de 0,2 segundo, umas 50 vezes a árvore, mas menos que a Random Forest. O custo maior está na busca de hiperparâmetros: 24 segundos por seed, contra menos de um segundo da árvore. Para prever, a rede e a árvore levam menos de um milissegundo, e a floresta, que consulta 300 árvores, uns 15.

**Para estudar** (apoio; não faz parte da fala)

- Máquina: AMD Ryzen 5 9600X (6 núcleos), 31 GB de memória, Windows 11, Python 3.14, scikit-learn 1.9.1.
- Um núcleo: n_jobs=1 e threadpool_limits(1), que limita também a álgebra linear do numpy. Assim a comparação é entre algoritmos, não entre quantos núcleos cada um usa.
- Busca medida à parte: depois da busca, o modelo final é treinado de novo com os hiperparâmetros escolhidos, e só esse treino entra na coluna ‘treino’.
- Busca da rede: 24 combinações × 5 partes = 120 redes, mais o treino final. Busca da árvore: 30 combinações × 5 = 150 árvores, ainda assim 36 vezes mais rápida.
- Medianas, e não médias, porque uma medição isolada com o computador ocupado puxaria a média. Os valores absolutos mudam de máquina para máquina; as razões entre modelos são mais estáveis.

**Perguntas prováveis**

- **P:** Com vários núcleos a rede não ficaria mais rápida?  
  **R:** A busca em grade, sim, porque as combinações são independentes; mas a da árvore também. Por isso medimos tudo num núcleo: a razão entre os modelos é o que interessa.

- **P:** O tempo da rede depende do número de épocas?  
  **R:** Sim. A rede final treinou de 40 a 121 épocas, conforme a seed; a parada antecipada também economiza tempo.

## Slide 9: Árvore desenha um degrau; a rede, uma rampa

**Roteiro (o que falar)** · Bernan · 1:05

Por que a rede perde para a árvore? Os gráficos mostram, para cada pedido de teste, a probabilidade de aprovação em função do score. Na árvore, os pontos ficam em 0 ou em 100%, com um salto em 550: ela representa o degrau com uma única pergunta. A rede desenha uma rampa: perto de 550 aparecem probabilidades intermediárias, e é ali que ela erra. Entre 550 e 599 pontos, a rede erra 9 pedidos, e a árvore, 1. A árvore tem outro ponto fraco: a exceção dos prazos curtos abaixo de 550, onde estão 12 dos seus 15 erros.

**Para estudar** (apoio; não faz parte da fala)

- Seed 42, 854 pedidos de teste. Erros por faixa de score (< 500 / 500–549 / 550–599 / ≥ 600; pedidos 275 / 70 / 73 / 436): rede 6 / 6 / 9 / 2; árvore 8 / 4 / 1 / 2.
- Entre 500 e 599 pontos, 24% das probabilidades da rede ficam entre 10% e 90%; na árvore, 1%.
- Exceção (score < 550 e prazo ≤ 4 anos): 52 pedidos de teste. Erros nela: árvore 12, rede 8.
- Redes tendem a aprender funções suaves; relações em degrau favorecem árvores em dados tabulares (Grinsztajn et al., 2022).

**Perguntas prováveis**

- **P:** Mais neurônios ou mais épocas resolveriam a rampa?  
  **R:** Em parte: a rampa pode ficar mais íngreme, mas a curva de neurônios mostrou que mais de 8 não ajuda, e treinar mais leva a decorar o treino. A árvore resolve com um corte.

- **P:** Mudar o corte de 50% ajudaria a rede?  
  **R:** Poderia reduzir alguns erros, já que a AUC é alta, mas o corte teria de ser escolhido na validação, não no teste. Não fizemos isso para manter o mesmo critério em todos os modelos.

## Slide 10: Conclusões

**Roteiro (o que falar)** · Bernan · 0:50

Para concluir: a rede neural funciona. Com padronização e parada antecipada, acerta 96,4% e supera a regressão logística. Mas, nesta base, não compensa: a árvore acerta mais, treina umas 50 vezes mais rápido e ainda dá regras legíveis. O motivo é a forma da regra que gerou os rótulos, um degrau no score, que a árvore captura com uma pergunta. Com dados reais, onde a relação costuma ser mais gradual, a rede poderia se sair melhor. Obrigado; ficamos à disposição para perguntas.

> Bernan conduz as perguntas.

**Para estudar** (apoio; não faz parte da fala)

- Lições sobre redes: padronizar sempre; a paciência e a taxa de aprendizado decidem quando a rede para; poucos neurônios bastam para uma base pequena; a busca de hiperparâmetros é o maior custo.
- Limitação principal: base provavelmente sintética; a conclusão vale para ela, não para crédito em geral.
- Trabalhos futuros: repetir em dados de crédito reais; separar a variação dos pesos iniciais da variação da divisão dos dados.

**Perguntas prováveis**

- **P:** Então redes neurais não servem para dados tabulares?  
  **R:** Servem, mas não são a escolha automática. Em bases pequenas e com relações em degrau, árvores e conjuntos de árvores costumam ganhar. A rede vale mais com muitos dados ou relações suaves e complexas.

- **P:** Qual modelo vocês usariam nesta base?  
  **R:** A árvore de decisão: 98,1%, empatada com a Random Forest, treino de milissegundos e regras que um analista de crédito consegue ler.
