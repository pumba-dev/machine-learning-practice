# Roteiro da segunda apresentação (10 min)

Cada slide traz o roteiro (o que falar), um material de estudo e perguntas prováveis. O estudo e as perguntas servem para dominar o assunto e não fazem parte da fala. As mesmas notas estão no .pptx.

# Bloco 1 · Thiago · slides 1 a 3: Onde paramos e os cinco modelos

## Slide 1: Árvore de decisão, Random Tree e conjuntos de árvores na classificação de alvos proteicos

**Roteiro (o que falar)** · Thiago · 0:20

Bom dia, professor e colegas. Eu sou o Thiago e, com o Paulo e o Bernan, vou apresentar a segunda parte do trabalho. Na primeira, usamos uma árvore de decisão para prever a qual proteína uma molécula está associada. Agora comparamos essa árvore com a Random Tree e com conjuntos de árvores, para ver quanto se ganha e o que se perde.

**Para estudar** (apoio; não faz parte da fala)

- Disciplina: PPGCC010 – Aprendizagem de Máquina (UFPI, 2026.2), Prof. Vinicius Ponte Machado.
- Quatro modelos no mesmo cenário: árvore de decisão, Random Tree (padrão e ajustada), Random Forest e gradient boosting (padrão e ajustados).
- Tudo no relatório atualizado (Seções 5.4, 6.6 e 6.7) e nos notebooks 04 a 07 do repositório.

**Perguntas prováveis**

- **P:** O que mudou desde a primeira apresentação?  
  **R:** Os dados, os atributos e a divisão são os mesmos. Entraram modelos novos e um experimento que mostra por que a Random Tree perde sozinha e ganha dentro da Random Forest.

## Slide 2: Na primeira parte, a árvore de decisão chegou a 89,4%

**Roteiro (o que falar)** · Thiago · 1:15

Um resumo rápido da primeira parte. São 27.476 moléculas do ChEMBL, cada uma associada a uma de quatro proteínas. Cada molécula vira 17 números: 5 descritores físico-químicos e 12 contagens tiradas do SMILES. E avaliamos com divisão agrupada: moléculas com os mesmos descritores, que chamamos de gêmeas, ficam sempre do mesmo lado, para o teste não premiar quem decora. Assim, a árvore de decisão acertou 89,4%, na média de 10 seeds. A pergunta de hoje é: uma árvore só é o melhor que dá para fazer?

**Para estudar** (apoio; não faz parte da fala)

- Acurácia da árvore: 89,4 ± 0,4% (10 seeds, divisão agrupada, 17 atributos). Piso (sempre EGFR): 29,3%.
- Gêmeas: 4.777 moléculas repetem os 5 descritores de outra; na divisão aleatória, 25,8% do teste tem uma gêmea no treino. A divisão agrupada sorteia grupos inteiros.
- Os 6 cenários da primeira parte (3 conjuntos de atributos × 2 divisões) continuam na Random Tree; os conjuntos foram avaliados só no cenário principal (17 atributos, divisão agrupada).

**Perguntas prováveis**

- **P:** Por que não repetir todos os modelos nos 6 cenários?  
  **R:** A Random Tree, que é uma árvore única, foi avaliada nos 6. Para os conjuntos, o cenário principal basta para a comparação e o custo da busca é bem maior.

## Slide 3: Quatro modelos feitos da mesma peça: a árvore

**Roteiro (o que falar)** · Thiago · 1:25

Os quatro modelos são feitos da mesma peça, a árvore, e mudam em duas perguntas: quantas árvores e quais atributos cada nó pode olhar. A árvore de decisão é uma árvore só, e em cada nó escolhe o melhor corte entre todos os atributos. A Random Tree também é uma árvore só, mas em cada nó sorteia alguns atributos e escolhe o melhor corte só entre eles. A Random Forest junta 300 Random Trees, cada uma treinada numa amostra sorteada do treino, e faz a votação. E o gradient boosting também usa muitas árvores, mas em sequência: cada árvore nova corrige o erro das anteriores.

> Passagem para Paulo: “Cinco modelos, a mesma peça. Mas como comparar de forma justa?”

**Para estudar** (apoio; não faz parte da fala)

- Random Tree: sorteia K atributos por nó, sem poda; K padrão = int(log2(n)) + 1, que dá K = 5 com 17 atributos. No scikit-learn: DecisionTreeClassifier(max_features=K).
- Random Forest (Breiman, 2001): cada árvore vê uma amostra bootstrap (com reposição, do mesmo tamanho do treino; cerca de um terço das linhas fica de fora) e sorteia atributos em cada nó (padrão do scikit-learn: K = raiz de n, 4 com 17 atributos). Previsão = média dos votos.
- Gradient boosting (Friedman, 2001): soma de árvores pequenas; cada nova árvore é ajustada ao erro (gradiente da perda) das anteriores, multiplicada pela taxa de aprendizado. Versão por histogramas (HistGradientBoostingClassifier, inspirada no LightGBM): agrupa cada atributo em até 255 faixas.

**Perguntas prováveis**

- **P:** Random Tree e Random Forest são a mesma coisa?  
  **R:** Não. A Random Tree é uma árvore só, com sorteio de atributos. A Random Forest são muitas dessas árvores, cada uma numa amostra bootstrap, votando.

# Bloco 2 · Paulo · slides 4 a 6: Como comparamos, o resultado e a Random Tree

## Slide 4: Mesma régua para todos os modelos

**Roteiro (o que falar)** · Paulo · 1:00

Para a comparação ser justa, todos os modelos passam pela mesma régua: o mesmo treino e o mesmo teste com divisão agrupada, a mesma busca de hiperparâmetros com validação cruzada que também respeita as gêmeas, e tudo repetido com 10 seeds. Cada modelo tem a sua busca: 72 combinações para a árvore, 54 para a Random Tree, e buscas leves para a floresta e o boosting.

**Para estudar** (apoio; não faz parte da fala)

- Grids: árvore 72 combinações (critério, profundidade, folha mínima, poda α); Random Tree 54 (critério, fração sorteada 0,25/0,5/0,75, profundidade, folha mínima), nos 6 cenários; Random Forest 6 (fração sorteada 0,15/raiz/0,5 × folha mínima 1/3, 300 árvores); gradient boosting 9 (taxa 0,1/0,2/0,3 × folhas 31/63/127, 300 iterações), no cenário principal.
- Out-of-bag: cada árvore é testada nas linhas que ficaram fora da sua amostra; essas linhas podem ter gêmeas dentro da amostra, então a estimativa vaza. Parada antecipada do boosting: separa 10% aleatórios do treino.
- Validação cruzada agrupada: StratifiedGroupKFold com 5 partes, grupos = tupla dos 5 descritores.
- Slide 7: árvore, Random Tree e Random Forest com a mesma árvore base, sem poda, só mudando K e o número de árvores.

**Perguntas prováveis**

- **P:** A busca da floresta e do boosting não foi pequena demais?  
  **R:** Foi leve de propósito. Na floresta, as melhores combinações ficam dentro de 0,4 ponto de validação; no boosting, deslocamos o grid quando o ótimo caiu no canto. O teto pode estar um pouco subestimado.

- **P:** Por que não usar a estimativa out-of-bag da floresta ou a parada antecipada do boosting?  
  **R:** Os dois sorteiam uma validação aleatória dentro do treino e deixariam gêmeas dos dois lados, o que infla a estimativa. Por isso ficaram desligados, e toda escolha usa a validação cruzada agrupada.

- **P:** Por que 10 seeds?  
  **R:** Uma seed só pode dar sorte ou azar. Com 10, dá para ver se a diferença entre dois modelos é maior que a variação do sorteio.

## Slide 5: Conjuntos ganham de 5% a 7%; a Random Tree perde para a árvore

**Roteiro (o que falar)** · Paulo · 1:15

E o resultado. O gráfico mostra a acurácia média de 10 seeds, com o eixo começando em 80%. Os modelos formam dois grupos. Embaixo, as árvores únicas: a árvore de decisão com 89,4% e a Random Tree abaixo dela, 89,0% ajustada e 87,6% com os valores padrão. Em cima, a Random Forest e o gradient boosting, com o boosting ajustado no topo, 96,6%. Todos os conjuntos superam a árvore nas 10 seeds, por 5,4% a 7,2%. A Random Tree sozinha perde.

**Para estudar** (apoio; não faz parte da fala)

- Médias ± desvio (10 seeds): Árvore de decisão 89,4 ± 0,4%; Random Tree (padrão) 87,6 ± 1,1%; Random Tree (ajustada) 89,0 ± 0,7%; Random Forest (padrão) 95,2 ± 0,3%; Random Forest (ajustada) 95,3 ± 0,3%; Gradient boosting (padrão) 94,8 ± 0,3%; Gradient boosting (ajustado) 96,6 ± 0,3%.
- Ganho sobre a árvore, seed a seed (pontos): Random Tree (padrão) −1,8; Random Tree (ajustada) −0,4; Random Forest (padrão) +5,8; Random Forest (ajustada) +5,8; Gradient boosting (padrão) +5,4; Gradient boosting (ajustado) +7,2.
- Random Tree contra a árvore: a padrão perde nas 10 seeds; a ajustada fica abaixo em 7 das 10.
- Desvio entre seeds: 0,3 a 0,4 ponto para quase todos; a Random Tree padrão tem o maior (1,1 ponto).
- F1 de HDAC1, a classe mais difícil: 86,6% na árvore e 95,4% no boosting ajustado; é a classe que mais ganha.

**Perguntas prováveis**

- **P:** Essas diferenças são significativas?  
  **R:** Os grupos estão separados por 4 pontos ou mais, e o desvio entre seeds é de 0,3 a 0,4 ponto. Medido seed a seed, todo conjunto ganha da árvore nas 10. Dentro do grupo de cima, Random Forest e boosting padrão ficam perto um do outro.

- **P:** Por que o eixo começa em 80%?  
  **R:** Para as diferenças de 1 a 2 pontos aparecerem. O piso de sempre responder EGFR é 29,3%, bem abaixo.

## Slide 6: A Random Tree perde em 5 de 6 cenários e varia com a semente

**Roteiro (o que falar)** · Paulo · 1:15

Olhando a Random Tree mais de perto. À esquerda, ela contra a árvore de decisão nos seis cenários da primeira parte. Ela fica abaixo em 5 dos 6, e perde mais com só os cinco descritores na divisão agrupada, −2,0%: com cinco atributos, sortear três em cada nó esconde quase metade das opções. À direita, outro problema: só trocando a semente, com os mesmos dados, a Random Tree varia de 87,8% a 89,8%. A árvore com os mesmos parâmetros varia bem menos. Sozinho, o sorteio de atributos só atrapalha: às vezes esconde o melhor corte do nó.

> Passagem para Bernan: “Se a Random Tree perde sozinha, por que a Random Forest, feita delas, ganha?”

**Para estudar** (apoio; não faz parte da fala)

- Random Tree ajustada × árvore, média de 10 seeds (pontos): descritores, agrupada: −2,0 (RT melhor em 0 seeds); descritores, aleatória: −0,7 (RT melhor em 1 seeds); descritores + SMILES, agrupada: −0,4 (RT melhor em 3 seeds); descritores + SMILES, aleatória: −0,3 (RT melhor em 2 seeds); só SMILES, agrupada: −0,2 (RT melhor em 4 seeds); só SMILES, aleatória: +0,0 (RT melhor em 6 seeds).
- Único cenário sem perda: só SMILES, divisão aleatória (+0,02 ponto, empate).
- Variação por semente (seed 42, 50 sementes, mesmo split): Random Tree de 87,8% a 89,8% (desvio 0,45 ponto); árvore de 88,7% a 89,4% (desvio 0,17).
- A busca puxa a Random Tree de volta para a árvore: escolhe sortear 75% dos atributos (K = 12 de 17) em 5 dos 6 cenários. Na curva por K (seed 42), a validação sobe até K = 5 e fica num platô; o melhor ponto, K = 13, está dentro do ruído. K = 17 é a própria árvore.
- Seed 42 no teste: Random Tree padrão 88,2%, ajustada 88,6%, árvore 89,7%.

**Perguntas prováveis**

- **P:** Então a Random Tree não serve para nada?  
  **R:** Sozinha, aqui, não vale a troca: perde acurácia e estabilidade e não ganha legibilidade. O valor dela aparece em conjunto, que é o próximo slide.

- **P:** E se escolher a melhor semente?  
  **R:** Seria escolher pelo teste, o que é trapaça. Não há como saber de antemão qual semente vai dar sorte.

# Bloco 3 · Bernan · slides 7 a 10: De onde vem o ganho, ajuste, confiança e conclusão

## Slide 7: Sozinha, a Random Tree perde; 300 delas formam a Random Forest

**Roteiro (o que falar)** · Bernan · 1:10

Se a Random Tree perde sozinha, por que a Random Forest, que é feita delas, ganha? Aqui as três usam a mesma árvore base. A árvore de decisão acerta 88,5%. Com o sorteio de atributos, uma árvore só cai para 86,6%: o sorteio esconde o melhor corte do nó. Mas 300 dessas Random Trees, cada uma treinada numa amostra diferente do treino, formam a Random Forest, com 95,2%: 6,7% acima da árvore. Num conjunto, o sorteio deixa as árvores diferentes entre si, elas erram em moléculas diferentes, e a votação cancela os erros.

**Para estudar** (apoio; não faz parte da fala)

- Seed 42, teste: árvore sem poda 88,5% (média de 10 sementes, desvio 0,16); Random Tree com K = raiz de 17 86,6% (desvio 0,87, cinco vezes maior); Random Forest de 300 árvores 95,2%.
- Por que o sorteio ajuda no conjunto: sem ele, as árvores veem os mesmos atributos e começam pelos mesmos cortes (TPSA, átomos aromáticos); os erros ficam correlacionados e a votação cancela menos. A variância da média de B árvores é ρσ² + (1 − ρ)σ²/B: o sorteio reduz a correlação ρ entre elas.
- Curva por número de árvores (validação agrupada, seed 42): 1 árvore 84,2%, 5 árvores 91,2%, 50 árvores 94,2%, 300 árvores 94,3%. A partir de 50 fica estável.
- Com 1 ou 2 árvores, a floresta fica abaixo da árvore de decisão: cada árvore vê só uma amostra bootstrap, sem cerca de um terço das linhas, e só parte dos atributos em cada nó.

**Perguntas prováveis**

- **P:** Por que a Random Tree aqui usa K = raiz de n e não o K padrão?  
  **R:** Para as três usarem a mesma árvore base da Random Forest padrão do scikit-learn; assim a única diferença entre elas é o sorteio e o número de árvores.

- **P:** Esse resultado vale com outras seeds?  
  **R:** O slide usa a seed 42. A tabela de 10 seeds conta a mesma história: árvore 89,4%, Random Tree 89,0% e Random Forest 95,2%.

## Slide 8: Ajustar rende no boosting, não na floresta

**Roteiro (o que falar)** · Bernan · 0:50

Ajustar hiperparâmetros vale a pena? Depende do conjunto. Na Random Forest, não: a padrão e a ajustada empatam, 95,2 e 95,3%. No gradient boosting, sim: de 94,8 para 96,6%. Boa parte desse ganho vem de deixar o boosting rodar 300 iterações sem parada antecipada. O gráfico mostra por quê: o treino chega a 100% cedo, mas a validação continua subindo até cerca de 200 iterações.

**Para estudar** (apoio; não faz parte da fala)

- Random Forest, seed 42: padrão 95,2%, ajustada 94,9% (max_features = 0.15, folha mínima 1). Só a folha mínima importa: subir de 1 para 3 custa cerca de 1,4 ponto de validação.
- Gradient boosting, seed 42: padrão 94,7%, ajustado 96,5% (taxa 0.2, 63 folhas, 300 iterações, sem parada antecipada).
- Padrão do HistGradientBoostingClassifier: 100 iterações e, com mais de 10 mil linhas, parada antecipada com 10% do treino separados ao acaso (com gêmeas).
- Curva (validação agrupada, seed 42): 1 iterações 81,9%; 5 iterações 88,7%; 10 iterações 91,2%; 25 iterações 94,0%; 50 iterações 95,4%; 100 iterações 96,1%; 150 iterações 96,2%; 200 iterações 96,3%; 250 iterações 96,2%; 300 iterações 96,2%.
- Na floresta, a curva por número de árvores fica plana a partir de 50; árvores a mais não causam sobreajuste, só custam tempo.

**Perguntas prováveis**

- **P:** O boosting não está sobreajustado, com treino em 100%?  
  **R:** A validação, que não é usada no treino, continua subindo depois disso. As árvores novas aumentam a margem entre as classes mesmo sem corrigir erros de treino.

- **P:** Quanto tempo leva cada modelo?  
  **R:** Não reportamos tempos: foram medidos com a máquina ocupada. Na ordem de grandeza, a árvore treina em décimos de segundo e os conjuntos em segundos a dezenas de segundos.

## Slide 9: Só a Random Forest sabe quando está em dúvida

**Roteiro (o que falar)** · Bernan · 0:50

Acurácia não é tudo. Confiança é a probabilidade que o modelo dá para a classe que ele prevê: se 210 das 300 árvores da floresta votam EGFR, a confiança é de 70%. A árvore de decisão diz 100% de confiança em todas as previsões, mesmo errando uma em cada dez. A Random Forest sabe quando está em dúvida: as previsões com confiança de até 70% são 20% do teste, mas concentram 91% dos erros. Dá para mandar só essas para revisão. O boosting acerta mais, mas é confiante demais: 21% dos erros saem com mais de 99,9% de confiança. E só a árvore de decisão tem regras que se pode ler.

**Para estudar** (apoio; não faz parte da fala)

- Árvore (seed 42): 5.496 previsões, todas com confiança de 100% (folhas puras), 568 erradas.
- Random Forest: 279 erros; 5,1% das previsões são unânimes; acima de 90% de confiança acerta 100,0%.
- Gradient boosting: 191 erros; 89,2% das previsões acima de 99,9% de confiança; essa faixa guarda 20,9% dos erros.
- O par HDAC1 ↔ EGFR soma cerca de 30% dos erros em todos os modelos (árvore 28,7%, floresta 30,8%, boosting 30,4%): vem da representação por contagens, que não vê como os átomos se ligam.
- A confiança da Random Forest é a fração de árvores que votam na classe; a do boosting é a soma de 300 árvores passada por softmax, o que empurra as probabilidades para os extremos.

**Perguntas prováveis**

- **P:** Dá para corrigir a confiança do boosting?  
  **R:** Sim, com calibração (por exemplo, regressão isotônica numa validação agrupada). Está nos trabalhos futuros.

- **P:** Por que a Random Forest não é legível, se é feita de árvores?  
  **R:** São 300 árvores com cerca de 2 mil folhas cada, votando. Não existe um caminho de perguntas que explique uma previsão.

## Slide 10: Conclusões

**Roteiro (o que falar)** · Bernan · 0:40

Para fechar. O gradient boosting ajustado é o mais preciso, 96,6%. A Random Forest, que junta 300 Random Trees, fica 5,8% acima da árvore, enquanto uma Random Tree sozinha perde para ela: o sorteio de atributos só ajuda dentro do conjunto. Na prática: para acertar mais, o boosting; para saber quando duvidar, a Random Forest; para explicar, a árvore. Obrigado, e estamos abertos a perguntas.

> Bernan conduz as perguntas.

**Para estudar** (apoio; não faz parte da fala)

- Números do slide: boosting ajustado 96,6 ± 0,3%; Random Forest padrão +5,8 pontos sobre a árvore (10 seeds); Random Tree ajustada −0,4 ponto em relação à árvore (10 seeds).
- Limites: busca leve nos conjuntos e só no cenário principal; comparação árvore, Random Tree e Random Forest do slide 7 com uma seed; os limites da primeira parte continuam (agrupamento só de descritores idênticos, 4 classes fixas, sem validação externa).
- Trabalhos futuros: representações estruturais (fingerprints) para a confusão HDAC1 ↔ EGFR; divisão por esqueleto molecular; calibrar o boosting.

**Perguntas prováveis**

- **P:** Qual modelo vocês recomendariam?  
  **R:** Depende do uso. Para triagem com revisão humana, a Random Forest, pela confiança útil. Para acurácia pura, o boosting ajustado. Para explicar a um químico, a árvore.

- **P:** O ganho dos conjuntos resolve a confusão HDAC1 ↔ EGFR?  
  **R:** Reduz os erros, mas o par continua com cerca de 30% deles. O limite está na representação, não no modelo.
