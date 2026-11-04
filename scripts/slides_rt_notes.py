"""Roteiro e material de estudo da segunda apresentação (árvore, Random Tree e conjuntos de árvores).

Mesmo formato de slides_notes.py: para cada slide, `tempo` e `fala` (o que dizer), `estudo` (apoio para
quem apresenta; não faz parte da fala) e `perguntas` (perguntas prováveis, com resposta curta).

Os números saem de slides/data/slides_rt_data.json (10 seeds do multiseed.csv e seed 42), gerado por
slides_rt_data.py com as mesmas funções dos notebooks 03 a 07.
"""


def comma(value, digits=1):
    return f"{value:.{digits}f}".replace(".", ",")


def signed(value, digits=1):
    """Diferença em pontos com sinal: +1,2 ou −0,4."""
    text = comma(abs(value), digits)
    return f"+{text}" if value >= 0 else f"−{text}"


def thousands(value):
    return f"{value:,}".replace(",", ".")


def build_notes(d):
    models = d["multiseed"]["modelos"]
    s42 = d["seed42"]
    rt = s42["random_tree"]
    forest, boosting = s42["ajuste"]["random_forest"], s42["ajuste"]["gradient_boosting"]
    three = s42["tres_arvores"]
    conf = s42["confianca"]
    grids = s42["grids"]

    acc = {name: comma(info["acuracia"]) for name, info in models.items()}
    sd = {name: comma(info["desvio"]) for name, info in models.items()}
    gain = {name: info.get("ganho_pontos") for name, info in models.items()}
    tree = acc["Árvore de decisão"]
    dt_single, rt_single, forest_300 = three["arvore"], three["random_tree"], three["random_forest"]
    total_gain = forest_300["acuracia"] - dt_single["acuracia"]
    curve = s42["curva_floresta"]
    rt_seeds, dt_seeds = rt["sementes"]["Random Tree"], rt["sementes"]["Árvore de decisão"]
    scenarios = d["multiseed"]["rt_cenarios"]
    losses = sum(s["diferenca_pontos"] < 0 for s in scenarios)
    worst = min(scenarios, key=lambda s: s["diferenca_pontos"])
    tie = max(scenarios, key=lambda s: s["diferenca_pontos"])
    rf_conf, gb_conf, dt_conf = conf["Random Forest"], conf["Gradient boosting"], conf["Árvore de decisão"]
    f1 = {name: info.get("f1_classes", {}) for name, info in models.items()}

    notes = []

    # 1 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:20",
        "fala": "Bom dia, professor e colegas. Eu sou o Thiago e, com o Paulo e o Bernan, vou apresentar a segunda "
                "parte do trabalho. Na primeira, usamos uma árvore de decisão para prever a qual proteína uma molécula "
                "está associada. Agora comparamos essa árvore com a Random Tree e com conjuntos de árvores, para ver "
                "quanto se ganha e o que se perde.",
        "estudo": [
            "Disciplina: PPGCC010 – Aprendizagem de Máquina (UFPI, 2026.2), Prof. Vinicius Ponte Machado.",
            "Quatro modelos no mesmo cenário: árvore de decisão, Random Tree (padrão do Weka e ajustada), Random "
            "Forest e gradient boosting (padrão e ajustados).",
            "Tudo no relatório atualizado (Seções 5.4, 6.6 e 6.7) e nos notebooks 04 a 07 do repositório.",
        ],
        "perguntas": [
            ("O que mudou desde a primeira apresentação?",
             "Os dados, os atributos e a divisão são os mesmos. Entraram modelos novos e um experimento que mostra por que "
             "a Random Tree perde sozinha e ganha dentro da Random Forest."),
        ],
    })

    # 2 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:15",
        "fala": f"Um resumo rápido da primeira parte. São {thousands(d['moleculas'])} moléculas do ChEMBL, cada uma "
                f"associada a uma de quatro proteínas. Cada molécula vira 17 números: 5 descritores físico-químicos e "
                f"12 contagens tiradas do SMILES. E avaliamos com divisão agrupada: moléculas com os mesmos descritores, "
                f"que chamamos de gêmeas, ficam sempre do mesmo lado, para o teste não premiar quem decora. Assim, a "
                f"árvore de decisão acertou {tree}%, na média de 10 seeds. A pergunta de hoje é: uma árvore só é o "
                f"melhor que dá para fazer?",
        "estudo": [
            f"Acurácia da árvore: {tree} ± {sd['Árvore de decisão']}% (10 seeds, divisão agrupada, 17 atributos). "
            f"Piso (sempre EGFR): {acc['Classe majoritária']}%.",
            "Gêmeas: 4.777 moléculas repetem os 5 descritores de outra; na divisão aleatória, 25,8% do teste tem uma "
            "gêmea no treino. A divisão agrupada sorteia grupos inteiros.",
            "Os 6 cenários da primeira parte (3 conjuntos de atributos × 2 divisões) continuam na Random Tree; os "
            "conjuntos foram avaliados só no cenário principal (17 atributos, divisão agrupada).",
        ],
        "perguntas": [
            ("Por que não repetir todos os modelos nos 6 cenários?",
             "A Random Tree, que é uma árvore única, foi avaliada nos 6. Para os conjuntos, o cenário principal basta "
             "para a comparação e o custo da busca é bem maior."),
        ],
    })

    # 3 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:25",
        "fala": "Os quatro modelos são feitos da mesma peça, a árvore, e mudam em duas perguntas: quantas árvores e "
                "quais atributos cada nó pode olhar. A árvore de decisão é uma árvore só, e em cada nó escolhe o melhor "
                "corte entre todos os atributos. A Random Tree, do Weka, também é uma árvore só, mas em cada nó sorteia "
                "alguns atributos e escolhe o melhor corte só entre eles. A Random Forest junta 300 Random Trees, cada "
                "uma treinada numa amostra sorteada do treino, e faz a votação. E o gradient boosting também usa muitas árvores, mas em sequência: cada árvore "
                "nova corrige o erro das anteriores.",
        "estudo": [
            f"Random Tree do Weka: sorteia K atributos por nó, sem poda; K padrão = int(log2(n)) + 1, que dá "
            f"K = {rt['k_weka']} com 17 atributos. No scikit-learn: DecisionTreeClassifier(max_features=K).",
            "Random Forest (Breiman, 2001): cada árvore vê uma amostra bootstrap (com reposição, do mesmo tamanho do "
            "treino; cerca de um terço das linhas fica de fora) e sorteia atributos em cada nó (padrão do scikit-learn: "
            "K = raiz de n, 4 com 17 atributos). Previsão = média dos votos.",
            "Gradient boosting (Friedman, 2001): soma de árvores pequenas; cada nova árvore é ajustada ao erro "
            "(gradiente da perda) das anteriores, multiplicada pela taxa de aprendizado. Versão por histogramas "
            "(HistGradientBoostingClassifier, inspirada no LightGBM): agrupa cada atributo em até 255 faixas.",
        ],
        "perguntas": [
            ("Random Tree e Random Forest são a mesma coisa?",
             "Não. A Random Tree é uma árvore só, com sorteio de atributos. A Random Forest são muitas dessas árvores, "
             "cada uma numa amostra bootstrap, votando."),
            ("Por que usar o scikit-learn e não o próprio Weka?",
             "Para manter o mesmo pipeline, a mesma divisão e a mesma validação dos outros modelos. O algoritmo é o "
             "mesmo: sortear K atributos por nó, sem poda."),
        ],
    })

    # 4 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:00",
        "fala": f"Para a comparação ser justa, todos os modelos passam pela mesma régua: o mesmo treino e o mesmo teste "
                f"com divisão agrupada, a mesma busca de hiperparâmetros com validação cruzada que também respeita as "
                f"gêmeas, e tudo repetido com 10 seeds. Cada modelo tem a sua busca: {grids['Árvore de decisão']} "
                f"combinações para a árvore, {grids['Random Tree']} para a Random Tree, e buscas leves para a floresta e "
                f"o boosting. Um detalhe: desligamos dois atalhos desses conjuntos, a estimativa out-of-bag e a parada "
                f"antecipada, porque os dois sorteiam uma validação aleatória e deixariam gêmeas dos dois lados.",
        "estudo": [
            f"Grids: árvore {grids['Árvore de decisão']} combinações (critério, profundidade, folha mínima, poda α); "
            f"Random Tree {grids['Random Tree']} (critério, fração sorteada 0,25/0,5/0,75, profundidade, folha mínima), "
            f"nos 6 cenários; Random Forest {grids['Random Forest']} (fração sorteada 0,15/raiz/0,5 × folha mínima 1/3, "
            f"300 árvores); gradient boosting {grids['Gradient boosting']} (taxa 0,1/0,2/0,3 × folhas 31/63/127, "
            f"300 iterações), no cenário principal.",
            "Out-of-bag: cada árvore é testada nas linhas que ficaram fora da sua amostra; essas linhas podem ter gêmeas "
            "dentro da amostra, então a estimativa vaza. Parada antecipada do boosting: separa 10% aleatórios do treino.",
            "Validação cruzada agrupada: StratifiedGroupKFold com 5 partes, grupos = tupla dos 5 descritores.",
            "Slide 7: árvore, Random Tree e Random Forest com a mesma árvore base, sem poda, só mudando K e o número "
            "de árvores.",
        ],
        "perguntas": [
            ("A busca da floresta e do boosting não foi pequena demais?",
             "Foi leve de propósito. Na floresta, as melhores combinações ficam dentro de 0,4 ponto de validação; no "
             "boosting, deslocamos o grid quando o ótimo caiu no canto. O teto pode estar um pouco subestimado."),
            ("Por que 10 seeds?",
             "Uma seed só pode dar sorte ou azar. Com 10, dá para ver se a diferença entre dois modelos é maior que a "
             "variação do sorteio."),
        ],
    })

    # 5 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:15",
        "fala": f"E o resultado. O gráfico mostra a acurácia média de 10 seeds, com o eixo começando em 80%. Os modelos "
                f"formam dois grupos. Embaixo, as árvores únicas: a árvore de decisão com {tree}% e a Random Tree abaixo "
                f"dela, {acc['Random Tree (ajustada)']}% ajustada e {acc['Random Tree (padrão Weka)']}% no padrão do "
                f"Weka. Em cima, a Random Forest e o gradient boosting, com o boosting ajustado no topo, "
                f"{acc['Gradient boosting (ajustado)']}%. Todos os conjuntos superam a árvore nas 10 seeds, por "
                f"{comma(gain['Gradient boosting (padrão)'])} a {comma(gain['Gradient boosting (ajustado)'])} pontos. "
                f"A Random Tree sozinha perde.",
        "estudo": [
            "Médias ± desvio (10 seeds): " + "; ".join(
                f"{name} {acc[name]} ± {sd[name]}%" for name in models if name != "Classe majoritária") + ".",
            "Ganho sobre a árvore, seed a seed (pontos): " + "; ".join(
                f"{name} {signed(gain[name])}" for name in models
                if gain.get(name) is not None and name != "Classe majoritária") + ".",
            f"Random Tree contra a árvore: a do padrão do Weka perde nas 10 seeds; a ajustada fica abaixo em "
            f"{10 - models['Random Tree (ajustada)']['seeds_com_ganho']} das 10.",
            "Desvio entre seeds: 0,3 a 0,4 ponto para quase todos; a Random Tree do Weka tem o maior (1,1 ponto).",
            f"F1 de HDAC1, a classe mais difícil: {comma(f1['Árvore de decisão']['HDAC1'])}% na árvore e "
            f"{comma(f1['Gradient boosting (ajustado)']['HDAC1'])}% no boosting ajustado; é a classe que mais ganha.",
        ],
        "perguntas": [
            ("Essas diferenças são significativas?",
             "Os grupos estão separados por 4 pontos ou mais, e o desvio entre seeds é de 0,3 a 0,4 ponto. Medido seed a "
             "seed, todo conjunto ganha da árvore nas 10. Dentro do grupo de cima, Random Forest e boosting padrão ficam "
             "perto um do outro."),
            ("Por que o eixo começa em 80%?",
             "Para as diferenças de 1 a 2 pontos aparecerem. O piso de sempre responder EGFR é 29,3%, bem abaixo."),
        ],
    })

    # 6 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:15",
        "fala": f"Olhando a Random Tree mais de perto. À esquerda, ela contra a árvore de decisão nos seis cenários da "
                f"primeira parte. Ela fica abaixo em {losses} dos 6, e perde mais com só os cinco descritores na divisão "
                f"agrupada, {signed(worst['diferenca_pontos'])} pontos: com cinco atributos, sortear três em cada nó "
                f"esconde quase metade das opções. À direita, outro problema: só trocando a semente, com os mesmos dados, "
                f"a Random Tree varia de {comma(rt_seeds['min'])}% a {comma(rt_seeds['max'])}%. A árvore com os mesmos "
                f"parâmetros varia bem menos. Sozinho, o sorteio de atributos só atrapalha: às vezes esconde o melhor "
                f"corte do nó.",
        "estudo": [
            "Random Tree ajustada × árvore, média de 10 seeds (pontos): " + "; ".join(
                f"{s['features']}, {s['split']}: {signed(s['diferenca_pontos'])} (RT melhor em {s['seeds_rt_melhor']} "
                f"seeds)" for s in scenarios) + ".",
            f"Único cenário sem perda: {tie['features']}, divisão {tie['split']} ({signed(tie['diferenca_pontos'], 2)} "
            f"ponto, empate).",
            f"Variação por semente (seed 42, 50 sementes, mesmo split): Random Tree de {comma(rt_seeds['min'])}% a "
            f"{comma(rt_seeds['max'])}% (desvio {comma(rt_seeds['std'], 2)} ponto); árvore de "
            f"{comma(dt_seeds['min'])}% a {comma(dt_seeds['max'])}% (desvio {comma(dt_seeds['std'], 2)}).",
            f"A busca puxa a Random Tree de volta para a árvore: escolhe sortear 75% dos atributos (K = "
            f"{rt['k_ajustada']} de 17) em 5 dos 6 cenários. Na curva por K (seed 42), a validação sobe até K = 5 e "
            f"fica num platô; o melhor ponto, K = {rt['melhor_k']}, está dentro do ruído. K = 17 é a própria árvore.",
            f"Seed 42 no teste: Random Tree do Weka {comma(rt['acuracia_weka'])}%, ajustada "
            f"{comma(rt['acuracia_ajustada'])}%, árvore {comma(s42['arvore']['acuracia'])}%.",
        ],
        "perguntas": [
            ("Então a Random Tree não serve para nada?",
             "Sozinha, aqui, não vale a troca: perde acurácia e estabilidade e não ganha legibilidade. O valor dela "
             "aparece em conjunto, que é o próximo slide."),
            ("E se escolher a melhor semente?",
             "Seria escolher pelo teste, o que é trapaça. Não há como saber de antemão qual semente vai dar sorte."),
        ],
    })

    # 7 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:10",
        "fala": f"Se a Random Tree perde sozinha, por que a Random Forest, que é feita delas, ganha? Aqui as três "
                f"usam a mesma árvore base. A árvore de decisão acerta {comma(dt_single['acuracia'])}%. Com o sorteio "
                f"de atributos, uma árvore só cai para {comma(rt_single['acuracia'])}%: o sorteio esconde o melhor "
                f"corte do nó. Mas 300 dessas Random Trees, cada uma treinada numa amostra diferente do treino, formam "
                f"a Random Forest, com {comma(forest_300['acuracia'])}%: {comma(total_gain)} pontos acima da árvore. "
                f"Num conjunto, o sorteio deixa as árvores diferentes entre si, elas erram em moléculas diferentes, e a "
                f"votação cancela os erros.",
        "estudo": [
            f"Seed 42, teste: árvore sem poda {comma(dt_single['acuracia'])}% (média de 10 sementes, desvio "
            f"{comma(dt_single['desvio'], 2)}); Random Tree com K = raiz de 17 {comma(rt_single['acuracia'])}% (desvio "
            f"{comma(rt_single['desvio'], 2)}, cinco vezes maior); Random Forest de 300 árvores "
            f"{comma(forest_300['acuracia'])}%.",
            "Por que o sorteio ajuda no conjunto: sem ele, as árvores veem os mesmos atributos e começam pelos mesmos "
            "cortes (TPSA, átomos aromáticos); os erros ficam correlacionados e a votação cancela menos. A variância da "
            "média de B árvores é ρσ² + (1 − ρ)σ²/B: o sorteio reduz a correlação ρ entre elas.",
            f"Curva por número de árvores (validação agrupada, seed 42): 1 árvore {comma(curve['1'])}%, 5 árvores "
            f"{comma(curve['5'])}%, 50 árvores {comma(curve['50'])}%, 300 árvores {comma(curve['300'])}%. A partir de "
            f"50 fica estável.",
            "Com 1 ou 2 árvores, a floresta fica abaixo da árvore de decisão: cada árvore vê só uma amostra bootstrap, "
            "sem cerca de um terço das linhas, e só parte dos atributos em cada nó.",
        ],
        "perguntas": [
            ("Por que a Random Tree aqui usa K = raiz de n e não o K do Weka?",
             "Para as três usarem a mesma árvore base da Random Forest padrão do scikit-learn; assim a única diferença "
             "entre elas é o sorteio e o número de árvores."),
            ("Esse resultado vale com outras seeds?",
             f"O slide usa a seed 42. A tabela de 10 seeds conta a mesma história: árvore {tree}%, Random Tree "
             f"{acc['Random Tree (ajustada)']}% e Random Forest {acc['Random Forest (padrão)']}%."),
        ],
    })

    # 8 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:50",
        "fala": f"Ajustar hiperparâmetros vale a pena? Depende do conjunto. Na Random Forest, não: a padrão e a ajustada "
                f"empatam, {acc['Random Forest (padrão)']} e {acc['Random Forest (ajustada)']}%. No gradient boosting, "
                f"sim: de {acc['Gradient boosting (padrão)']} para {acc['Gradient boosting (ajustado)']}%. Boa parte "
                f"desse ganho vem de deixar o boosting rodar 300 iterações sem parada antecipada. O gráfico mostra por "
                f"quê: o treino chega a 100% cedo, mas a validação continua subindo até cerca de 200 iterações.",
        "estudo": [
            f"Random Forest, seed 42: padrão {comma(forest['padrao'])}%, ajustada {comma(forest['ajustada'])}% "
            f"(max_features = {forest['params']['max_features']}, folha mínima {forest['params']['min_samples_leaf']}). "
            "Só a folha mínima importa: subir de 1 para 3 custa cerca de 1,4 ponto de validação.",
            f"Gradient boosting, seed 42: padrão {comma(boosting['padrao'])}%, ajustado {comma(boosting['ajustado'])}% "
            f"(taxa {boosting['params']['learning_rate']}, {boosting['params']['max_leaf_nodes']} folhas, 300 "
            "iterações, sem parada antecipada).",
            "Padrão do HistGradientBoostingClassifier: 100 iterações e, com mais de 10 mil linhas, parada antecipada "
            "com 10% do treino separados ao acaso (com gêmeas).",
            "Curva (validação agrupada, seed 42): " + "; ".join(
                f"{k} iterações {comma(v)}%" for k, v in boosting["curva_iteracoes"].items()) + ".",
            "Na floresta, a curva por número de árvores fica plana a partir de 50; árvores a mais não causam "
            "sobreajuste, só custam tempo.",
        ],
        "perguntas": [
            ("O boosting não está sobreajustado, com treino em 100%?",
             "A validação, que não é usada no treino, continua subindo depois disso. As árvores novas aumentam a margem "
             "entre as classes mesmo sem corrigir erros de treino."),
            ("Quanto tempo leva cada modelo?",
             "Não reportamos tempos: foram medidos com a máquina ocupada. Na ordem de grandeza, a árvore treina em "
             "décimos de segundo e os conjuntos em segundos a dezenas de segundos."),
        ],
    })

    # 9 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:50",
        "fala": f"Acurácia não é tudo. A árvore de decisão diz 100% de confiança em todas as previsões, mesmo errando "
                f"uma em cada dez. A Random Forest sabe quando está em dúvida: as previsões com confiança de até 70% são "
                f"{comma(rf_conf['previsoes_abaixo_70'], 0)}% do teste, mas concentram "
                f"{comma(rf_conf['erros_abaixo_70'], 0)}% dos erros. Dá para mandar só essas para revisão. O boosting "
                f"acerta mais, mas é confiante demais: {comma(gb_conf['erros_confianca_maxima'], 0)}% dos erros saem com "
                f"mais de 99,9% de confiança. E só a árvore de decisão tem regras que se pode ler.",
        "estudo": [
            f"Árvore (seed 42): {thousands(dt_conf['teste'])} previsões, todas com confiança de 100% (folhas puras), "
            f"{thousands(dt_conf['erros'])} erradas.",
            f"Random Forest: {thousands(rf_conf['erros'])} erros; {comma(rf_conf['previsoes_confianca_maxima'])}% das "
            f"previsões são unânimes; acima de 90% de confiança acerta {comma(rf_conf['acuracia_acima_90'])}%.",
            f"Gradient boosting: {thousands(gb_conf['erros'])} erros; {comma(gb_conf['previsoes_confianca_maxima'])}% "
            f"das previsões acima de 99,9% de confiança; essa faixa guarda "
            f"{comma(gb_conf['erros_confianca_maxima'])}% dos erros.",
            f"O par HDAC1 ↔ EGFR soma cerca de 30% dos erros em todos os modelos (árvore "
            f"{comma(dt_conf['par_hdac1_egfr'])}%, floresta {comma(rf_conf['par_hdac1_egfr'])}%, boosting "
            f"{comma(gb_conf['par_hdac1_egfr'])}%): vem da representação por contagens, que não vê como os átomos se "
            "ligam.",
            "A confiança da Random Forest é a fração de árvores que votam na classe; a do boosting é a soma de 300 "
            "árvores passada por softmax, o que empurra as probabilidades para os extremos.",
        ],
        "perguntas": [
            ("Dá para corrigir a confiança do boosting?",
             "Sim, com calibração (por exemplo, regressão isotônica numa validação agrupada). Está nos trabalhos futuros."),
            ("Por que a Random Forest não é legível, se é feita de árvores?",
             "São 300 árvores com cerca de 2 mil folhas cada, votando. Não existe um caminho de perguntas que explique "
             "uma previsão."),
        ],
    })

    # 10 -----------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:40",
        "fala": f"Para fechar. O gradient boosting ajustado é o mais preciso, {acc['Gradient boosting (ajustado)']}%. "
                f"A Random Forest, que junta 300 Random Trees, fica {comma(gain['Random Forest (padrão)'])} pontos acima "
                f"da árvore, enquanto uma Random Tree sozinha perde para ela: o sorteio de atributos só ajuda dentro do "
                f"conjunto. Na "
                f"prática: para acertar mais, o boosting; para saber quando duvidar, a Random Forest; para explicar, a "
                f"árvore. Obrigado, e estamos abertos a perguntas.",
        "estudo": [
            f"Números do slide: boosting ajustado {acc['Gradient boosting (ajustado)']} ± "
            f"{sd['Gradient boosting (ajustado)']}%; Random Forest padrão {signed(gain['Random Forest (padrão)'])} pontos "
            f"sobre a árvore (10 seeds); Random "
            f"Tree ajustada {signed(gain['Random Tree (ajustada)'])} ponto em relação à árvore (10 seeds).",
            "Limites: busca leve nos conjuntos e só no cenário principal; comparação árvore, Random Tree e Random Forest do slide 7 com uma seed; Random Tree "
            "reproduzida no scikit-learn, sem rodar o Weka; os limites da primeira parte continuam (agrupamento só de "
            "descritores idênticos, 4 classes fixas, sem validação externa).",
            "Trabalhos futuros: representações estruturais (fingerprints) para a confusão HDAC1 ↔ EGFR; divisão por "
            "esqueleto molecular; calibrar o boosting.",
        ],
        "perguntas": [
            ("Qual modelo vocês recomendariam?",
             "Depende do uso. Para triagem com revisão humana, a Random Forest, pela confiança útil. Para acurácia pura, "
             "o boosting ajustado. Para explicar a um químico, a árvore."),
            ("O ganho dos conjuntos resolve a confusão HDAC1 ↔ EGFR?",
             "Reduz os erros, mas o par continua com cerca de 30% deles. O limite está na representação, não no modelo."),
        ],
    })
    return notes
