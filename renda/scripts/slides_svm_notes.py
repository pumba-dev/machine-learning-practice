"""Roteiro e material de estudo da quarta apresentação (SVM na base de renda).

Mesmo formato de emprestimos/scripts/slides_rn_notes.py: para cada slide, `tempo` e `fala` (o que dizer),
`estudo` (apoio para quem apresenta; não faz parte da fala) e `perguntas` (perguntas prováveis, com resposta
curta).

Os números saem de report/results/svm_dados.json, gerado por svm_data.py a partir dos resultados dos
notebooks da pasta renda/.
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
    b, m, c, mapa = d["base"], d["modelos"], d["comparacoes"], d["mapa"]
    k, pad, tempo, g = d["seed0"]["kernels"], d["seed0"]["padronizacao"], d["tempo_por_tamanho"], d["gamma_rbf"]
    acc = {nome: comma(info["acuracia"]) for nome, info in m.items()}
    auc = {nome: comma(info["auc"]) for nome, info in m.items()}
    f1 = {nome: comma(info["f1"]) for nome, info in m.items()}
    rbf, rede, lin = m["SVM RBF"], m["rede neural"], m["SVM linear"]
    pct_vetores = 100 * rbf["vetores"] / d["seed0"]["treino"]
    melhor = mapa["melhor"]
    svc, lsvc = tempo["SVC RBF"], tempo["LinearSVC"]
    razao_lsvc = k["SVC linear"]["treino_s"] / k["LinearSVC"]["treino_s"]
    accs_k = [k[nome]["acuracia"] for nome in ("LinearSVC", "SVC linear", "SVC polinomial grau 2",
                                               "SVC polinomial grau 3", "SVC RBF")]
    razao_prev = rbf["previsao_ms"] / rede["previsao_ms"]

    notes = []

    # 1 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:25",
        "fala": "Bom dia, professor e colegas. Eu sou o Thiago e, com o Paulo e o Bernan, vou apresentar a quarta "
                "parte do trabalho. Mais uma vez a base muda: agora são pessoas do censo americano, e a pergunta é se "
                "a renda passa de 50 mil dólares por ano. O modelo estudado é a SVM, a máquina de vetores de suporte, "
                "comparada com os modelos das partes anteriores, inclusive a rede neural.",
        "estudo": [
            "Disciplina: PPGCC010 – Aprendizagem de Máquina (UFPI, 2026.2), Prof. Vinicius Ponte Machado.",
            "Tudo no repositório, pasta renda/: notebooks 01 a 06, resultados em renda/resultados/.",
            "Biblioteca: scikit-learn (SVC, LinearSVC, MLPClassifier), a mesma das partes anteriores.",
            "Por que uma base nova: a de empréstimos era pequena (4.269 pedidos) e quase resolvida por um corte no "
            "score. A Adult tem atributos de texto, valores ausentes e tamanho suficiente para o custo da SVM aparecer.",
        ],
        "perguntas": [
            ("Por que não usar a SVM na base de empréstimos?",
             "Lá uma regra de um corte já acertava 95,5% e a árvore 98%: sobrava pouco para a SVM mostrar. A Adult é "
             "maior, tem atributos categóricos e nenhuma regra simples resolve, então as diferenças entre fronteiras "
             "retas e curvas e o custo da SVM aparecem."),
        ],
    })

    # 2 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:40",
        "fala": f"A base é a Adult, do repositório da UCI, extraída do censo dos Estados Unidos de 1994. Depois da "
                f"curadoria, ficam {thousands(b['linhas'])} pessoas e 10 atributos: cinco numéricos, como idade, anos de "
                f"estudo e horas por semana, e cinco de texto, como estado civil e ocupação. O rótulo diz se a pessoa "
                f"ganha mais de 50 mil por ano: {comma(b['positivos'])}% ganham. Então responder sempre ‘não’ já acerta "
                f"{comma(b['piso'])}%; esse é o piso.",
        "estudo": [
            f"Base bruta: {thousands(b['brutas'])} linhas, {comma(b['positivos_brutos'])}% acima de 50 mil. Kaggle "
            "(uciml/adult-census-income), cópia da Adult da UCI (CC BY 4.0). Arquivo conferido pelo hash SHA-256 no "
            "notebook 01.",
            "Numéricos: idade, anos de estudo (education.num, de 1 a 16), ganho de capital, perda de capital, horas "
            "por semana.",
            "Categóricos: classe de trabalho (7), estado civil (7), ocupação (14), relacionamento (6), país de "
            "origem (41).",
            f"A SVM só trabalha com números: cada categoria vira uma coluna 0/1 (one-hot). São {b['colunas_modelo']} "
            "colunas no total, metade delas só de país (91% nasceram nos EUA).",
            "O valor de 50 mil dólares é de 1994; corrigido pela inflação, seria perto de 100 mil hoje.",
        ],
        "perguntas": [
            ("O que é one-hot?",
             "Uma coluna por categoria, com 1 na categoria da pessoa e 0 nas outras. ‘Estado civil’ com 7 valores "
             "vira 7 colunas. Assim o modelo não supõe uma ordem que não existe, como ‘casado > divorciado’."),
            ("Por que não usar a escolaridade em texto?",
             "Porque ela é a mesma informação de anos de estudo: cada nível corresponde a exatamente um número. "
             "Usamos o número, que já tem ordem."),
        ],
    })

    # 3 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:40",
        "fala": f"A curadoria tirou três coisas. Primeiro, {b['duplicadas']} linhas repetidas. Depois, "
                f"{thousands(b['com_ausente'])} linhas com valor ausente, marcado com interrogação, quase todas em classe "
                f"de trabalho e ocupação. Sobram {thousands(b['linhas'])} pessoas, o que ainda é bastante. E tiramos dois "
                f"atributos: o fnlwgt, que é um peso amostral do censo, quantas pessoas cada linha representa, e não uma "
                f"característica da pessoa; e a escolaridade em texto, que repete os anos de estudo.",
        "estudo": [
            f"As linhas com ‘?’ eram 7% da base. Nelas, {comma(b['positivos_com_ausente'])}% ganham mais de 50 mil, "
            f"contra {comma(b['positivos'])}% no resto: removê-las tira mais gente de renda baixa, mas a proporção "
            "quase não muda.",
            "Classe de trabalho e ocupação faltam juntas em 1.836 linhas. As 7 linhas com só a ocupação ausente são "
            "de quem nunca trabalhou (classe ‘Never-worked’): não há ocupação a informar.",
            f"fnlwgt: correlação de {comma(b['correlacao_fnlwgt'], 3)} com a renda. Serve para estimar totais do país, "
            "não para prever a renda de uma pessoa.",
            "Raça e sexo também ficaram fora dos atributos do modelo; o relatório explica a decisão. Os dados "
            "continuam no arquivo, mas nenhum modelo os usa.",
        ],
        "perguntas": [
            ("Por que não preencher os ausentes em vez de remover?",
             "Eram 7% das linhas, e ainda sobram 30 mil pessoas. Preencher a ocupação de alguém com a mais comum "
             "inventaria uma informação justamente num dos atributos mais importantes."),
            ("Raça e sexo entraram no modelo?",
             "Não. Ficaram fora dos atributos por decisão do grupo, explicada no relatório. O modelo usa só os 10 "
             "atributos do slide anterior."),
        ],
    })

    # 4 ------------------------------------------------------------------------------------------
    ec = b["estado_civil"]
    notes.append({
        "tempo": "0:45",
        "fala": f"O que torna a base difícil é que nenhum atributo decide sozinho. O mais forte é o estado civil: entre os "
                f"casados, {comma(ec['casado(a)'], 0)}% ganham mais de 50 mil; entre quem nunca casou, "
                f"{comma(ec['nunca casou'], 0)}%. Mas nem os casados passam da metade. A regra de um corte faz essa "
                f"pergunta e responde ‘não’ dos dois lados, então fica nos mesmos {comma(b['piso'])}% do chute. Na base "
                f"de empréstimos, essa regra acertava 95%. E há um limite: {b['perfis_conflito']} perfis idênticos "
                f"aparecem com as duas rendas, então nenhum modelo passa de {comma(b['teto'])}%.",
        "estudo": [
            f"Perfis em conflito: {b['perfis_conflito']} combinações dos 10 atributos aparecem com as duas rendas, em "
            f"{thousands(b['linhas_conflito'])} linhas (8%). Em cada perfil, o melhor possível é responder a renda mais "
            f"comum, e erra-se o resto: {b['erros_irredutiveis']} erros no mínimo, ou {comma(100 - b['teto'])}% da base.",
            "São pessoas diferentes com os mesmos dados (não duplicatas: a linha completa, com fnlwgt, era diferente).",
            "Na análise exploratória, a melhor regra de duas perguntas (casado com 13 anos de estudo ou mais, ou não "
            "casado com ganho de capital alto) acerta 82,4%.",
            f"A AUC da regra de um corte é {auc['regra de um corte']}%, bem acima de 50%: a pergunta ordena bem as "
            "pessoas, mas o corte em 50% não muda a resposta.",
        ],
        "perguntas": [
            ("Se a regra pergunta algo útil, por que acerta o mesmo que o chute?",
             "Porque nos dois lados a maioria ganha até 50 mil (55% dos casados, 93% dos demais). Cada lado responde "
             "a sua maioria, e as duas maiorias são ‘não’."),
            ("Como pode haver erro inevitável?",
             "Duas pessoas com exatamente os mesmos 10 atributos podem ter rendas diferentes. Qualquer modelo dá a "
             "mesma resposta para as duas, e erra pelo menos uma."),
        ],
    })

    # 5 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:35",
        "fala": f"O protocolo é o mesmo da parte anterior: dez divisões diferentes, 80% para treino e 20% para teste, "
                f"busca de hiperparâmetros com validação cruzada só no treino, e tempo medido num único núcleo. Como há "
                f"três pessoas abaixo para cada uma acima, olhamos também o F1 macro e a AUC. As réguas são estas: a "
                f"regressão logística, a árvore ajustada e a Random Forest ficam entre {acc['random forest']} e "
                f"{acc['árvore de decisão']}% de acurácia. A meta da SVM é passar de 85% e de 78% de F1 macro.",
        "estudo": [
            "Validação cruzada estratificada de 5 partes dentro do treino; o teste só é usado uma vez por seed.",
            "Tempos: mediana das 10 seeds, um núcleo (threadpool_limits(1), n_jobs=1), aquecimento descartado. "
            "Máquina: Ryzen 5 9600X.",
            "F1 macro: média do F1 das duas classes; não deixa a classe grande esconder a pequena. AUC: chance de uma "
            "pessoa de renda alta receber nota maior que uma de renda baixa; não depende do corte em 50%.",
            "Árvore: busca em critério × profundidade × folha mínima (30 combinações). Random Forest: 300 árvores, "
            "configuração padrão, como nas partes 2 e 3.",
            f"A Random Forest fica abaixo da árvore nas 10 seeds: com folhas de 1 pessoa, ela decora o ruído dos "
            f"perfis em conflito.",
        ],
        "perguntas": [
            ("Por que a Random Forest perdeu para uma árvore só?",
             "Na configuração padrão, cada árvore cresce até separar todas as pessoas do treino. Com 8% das linhas em "
             "perfis que aparecem com as duas rendas, crescer até o fim é decorar ruído. A árvore ajustada para antes, "
             "com folhas de 5 a 20 pessoas."),
            ("Por que 10 seeds?",
             "Uma divisão só pode favorecer um modelo por sorte. Com 10, vemos a média, o desvio e em quantas seeds um "
             "modelo vence o outro."),
        ],
    })

    # 6 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:45",
        "fala": "Agora, como a SVM funciona. Imagine uma rua entre dois bairros: a SVM procura a rua mais larga "
                "possível que separa as classes. Essa largura é a margem. As pessoas na calçada, encostadas na rua, são "
                "os vetores de suporte: só elas definem por onde a rua passa. E o parâmetro C é a tolerância a erro: "
                "C pequeno aceita alguns erros e mantém a rua larga; C grande exige acertar todos e estreita a rua.",
        "estudo": [
            f"Nesta base, a SVM RBF usa cerca de {thousands(rbf['vetores'])} vetores de suporte, "
            f"{comma(pct_vetores, 0)}% do treino. Cada pessoa nova é comparada com todos eles, e por isso a previsão "
            "é lenta (slide 10).",
            "Analogia: a fronteira é uma rua entre dois bairros; a margem é a largura da rua; os vetores de suporte "
            "são as casas na calçada. Tirar uma casa do fundo do bairro não muda a rua; tirar uma da calçada, muda.",
            "A SVM não calcula probabilidade. Para cada pessoa, calcula a distância com sinal até a fronteira "
            "(decision_function): positiva, >50K; negativa, ≤50K. A AUC usa essa distância como nota.",
            "Na seed 0, 30% das pessoas do teste caem dentro da margem (distância entre −1 e +1).",
            "A classe pequena aparece muito entre os vetores de suporte: metade deles é >50K, embora seja 25% do "
            "treino, porque boa parte dela fica perto da fronteira.",
            "Com C = 0,01, 48% do treino vira vetor de suporte; com C = 100, 34%.",
            "Probabilidade só com probability=True, que faz uma calibração extra (Platt) com validação cruzada interna e "
            "deixa o treino cerca de 5 vezes mais lento; não usamos.",
        ],
        "perguntas": [
            ("Por que maximizar a margem?",
             "Entre todas as fronteiras que separam o treino, a de margem maior fica mais longe dos dois grupos, e uma "
             "pessoa nova um pouco diferente das do treino tem menos chance de cair do lado errado."),
            ("Se só os vetores de suporte importam, o resto do treino é inútil?",
             "Para a fronteira final, sim: tirar um ponto que não é vetor de suporte não muda nada. Mas não se sabe "
             "antes quais serão vetores de suporte; o treino precisa de todos para descobrir."),
        ],
    })

    # 7 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:30",
        "fala": "E se uma reta não separa as classes? O kernel curva a fronteira. O linear traça uma reta; o "
                "polinomial combina atributos, como idade vezes horas; e o RBF curva a fronteira em torno dos pontos, "
                "com o gamma definindo o alcance de cada um: gamma pequeno dá uma fronteira suave, gamma grande, cheia "
                f"de curvas. Sem ajuste, todos ficam entre {comma(min(accs_k))} e {comma(max(accs_k))}%: a curva ganha "
                "pouco sobre a reta.",
        "estudo": [
            "Medição na seed 0 do notebook 04, C = 1, gamma padrão (‘scale’, cerca de 0,10 nesta base).",
            "Kernel: uma função que mede a semelhança entre duas pessoas. A SVM com kernel equivale a traçar uma reta "
            "num espaço transformado, sem calcular esse espaço (o ‘truque do kernel’).",
            "RBF: semelhança = exp(−gamma × distância²). Gamma grande: cada ponto só influencia a vizinhança, fronteira "
            "cheia de curvas. Gamma pequeno: influência larga, fronteira suave.",
            "Polinomial com coef0 = 1: o grau 2 inclui os termos lineares e os produtos de pares de atributos.",
            "LinearSVC (liblinear) e SVC linear (libsvm) chegam à mesma fronteira por algoritmos diferentes; a LinearSVC "
            f"cresce com n, a SVC com n², e na seed 0 a LinearSVC treina {comma(razao_lsvc, 0)} vezes mais rápido. Por "
            "isso a comparação usa a LinearSVC (esse número aparece no slide 10).",
            "Exemplo para explicar o kernel: numa só dimensão, com as pessoas de renda baixa no meio e as de renda alta "
            "nas pontas, nenhum corte separa; criando uma segunda coordenada x², uma reta separa. O kernel faz isso sem "
            "calcular as coordenadas novas.",
        ],
        "perguntas": [
            ("O RBF é um polinômio de grau infinito?",
             "Matematicamente, o RBF corresponde a um espaço transformado de dimensão infinita, e a sua expansão em "
             "série tem termos de todos os graus. Na prática, o que importa é que ele mede semelhança pela distância."),
        ],
    })

    # 8 ------------------------------------------------------------------------------------------
    perto, total = mapa["perto_do_melhor"], mapa["combinacoes"]
    g1 = mapa["gamma1_C1"]
    notes.append({
        "tempo": "0:40",
        "fala": f"Este mapa mostra a acurácia na validação para cada par de C e gamma; quanto mais escuro, melhor. A "
                f"melhor combinação é C igual a {comma(melhor['C'], 0)} e gamma {comma(melhor['gamma'])}, com "
                f"{comma(melhor['acuracia'], 2)}%, mas {perto} das {total} combinações ficam a meio ponto dela: muitas "
                f"servem, num platô na diagonal. Gamma menor pede C maior. Só os cantos falham: com os dois pequenos, o "
                f"modelo cai no chute; com gamma 1, ele decora o treino.",
        "estudo": [
            "Seed 0, validação cruzada de 5 partes no treino: 5 valores de C × 7 de gamma, 35 combinações, 175 "
            "treinos. O mapa levou 41 minutos, dos quais só 17 de treino; o resto foi avaliação.",
            f"Gamma = 1 com C = 1: {comma(g1['treino'])}% no treino e {comma(g1['validacao'])}% na validação. É sobreajuste: "
            "a fronteira contorna as pessoas do treino uma a uma.",
            "Por que a diagonal: gamma pequeno deixa a fronteira suave; C grande cobra mais pelos erros e compensa. As "
            "duas combinações levam a fronteiras parecidas.",
            "A grade das 10 seeds (C ∈ {0,1; 1; 10; 100} × gamma ∈ {0,01; 0,03; 0,1; 0,3}) saiu deste mapa: cobre o "
            "platô e deixa de fora os cantos ruins.",
        ],
        "perguntas": [
            ("O melhor ponto está na borda da grade (gamma = 0,3). Não deveria testar valores maiores?",
             "O mapa já testou gamma = 1, e ele piora em qualquer C. A borda da grade das 10 seeds não esconde um "
             "valor melhor."),
        ],
    })

    # 9 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:35",
        "fala": "A padronização é obrigatória para o RBF. Ele mede a distância entre as pessoas, e o ganho de capital vai "
                "até 99 mil, enquanto a idade vai até 90: sem padronizar, o capital domina a conta. A acurácia cai de "
                f"{comma(pad['RBF com']['acuracia'])} para {comma(pad['RBF sem']['acuracia'])}%. A SVM linear não muda, "
                "porque dá um peso a cada atributo e compensa a escala.",
        "estudo": [
            "Padronizar: (valor − média) ÷ desvio padrão, com média e desvio só do treino, dentro do Pipeline. O "
            "one-hot (0/1) continua nos dois casos.",
            f"Sem padronização, o F1 da classe >50K cai de {comma(pad['RBF com']['f1_pos'])} para "
            f"{comma(pad['RBF sem']['f1_pos'])}%, os vetores de suporte sobem para {thousands(pad['RBF sem']['vetores'])} "
            f"(70% do treino) e o treino leva {comma(pad['RBF sem']['treino_s'], 0)} s.",
            "É o mesmo recado da rede neural na parte 3: lá, sem padronização, a rede ficava abaixo do chute.",
        ],
        "perguntas": [
            ("E a árvore, precisa de padronização?",
             "Não. A árvore compara um atributo por vez com um limite, e mudar a escala só muda o valor do limite."),
        ],
    })

    # 10 -----------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:45",
        "fala": f"O custo da SVM com kernel cresce rápido: dobrar o treino quadruplica o tempo. Com as 24 mil pessoas, "
                f"a SVC treina em {comma(svc['tempo_s'][-1])} segundos e a LinearSVC, que chega à mesma reta da SVC "
                f"linear, em {comma(lsvc['tempo_s'][-1], 2)}. A previsão também pesa: a SVC compara cada pessoa com todos "
                f"os vetores de suporte, e leva {comma(rbf['previsao_ms'] / 1000)} segundos para prever o teste, contra "
                f"{comma(lin['previsao_ms'])} milissegundos da SVM linear.",
        "estudo": [
            "Medição na seed 0 (notebook 04), treinos com 1.000 a 24.111 pessoas; inclinação ajustada de 4.000 pessoas "
            "para cima (nos tamanhos pequenos, um custo fixo pesa mais que os dados).",
            f"Num gráfico log-log (Figura do relatório), a inclinação diz como o tempo cresce: {comma(svc['inclinacao'])} "
            f"na SVC RBF (dobrar o treino quadruplica o tempo) e {comma(lsvc['inclinacao'])} na LinearSVC (cresce junto "
            "com os dados). Não está no slide para não precisar explicar escala logarítmica.",
            "Pela regra do quadrado, a mesma SVC levaria cerca de 100 s com 100 mil pessoas e quase 3 horas com 1 "
            "milhão. Numa base assim, usa-se a LinearSVC ou uma aproximação do kernel.",
            f"Previsão das 6.028 pessoas do teste (mediana de 10 seeds): SVM RBF {comma(rbf['previsao_ms'] / 1000)} s, SVM "
            f"linear {comma(lin['previsao_ms'])} ms. A linear guarda só um peso por coluna.",
            "Por que n²: a SVC trabalha com a semelhança entre pares de pessoas, e o número de pares cresce com o "
            "quadrado.",
        ],
        "perguntas": [
            ("Dá para acelerar a SVC usando mais núcleos?",
             "O libsvm treina num núcleo só. A busca em grade pode rodar combinações em paralelo, mas cada treino "
             "continua com o mesmo custo. Medimos tudo num núcleo para comparar os modelos de forma justa."),
        ],
    })

    # 11 -----------------------------------------------------------------------------------------
    e = d["escolhas"]
    notes.append({
        "tempo": "0:35",
        "fala": "Esta tabela mostra as réguas de cada modelo: os valores que a busca testou e o que ela escolheu nas dez "
                "seeds. A SVM é estável: a linear escolheu C igual a 0,1 em sete seeds, o RBF escolheu C igual a 1 em "
                "nove, e a polinomial ficou no grau 2. Já a árvore e a rede variam com a seed, porque várias "
                "configurações empatam na validação.",
        "estudo": [
            "SVM RBF: gamma 0,3 em 5 seeds, 0,1 em 4; na seed restante, C = 10 e gamma = 0,03, também no platô "
            "(gamma menor, C maior).",
            f"Árvore: {e['árvore de decisão']['combinacoes']} combinações diferentes em 10 seeds; profundidade de "
            f"{e['árvore de decisão']['profundidade_min']} para cima (em {e['árvore de decisão']['sem_limite']} seeds, sem "
            "limite, mas com folha mínima de 5 ou 20).",
            f"Rede: 10 combinações diferentes em 10 seeds; o early stopping parou entre {rede['epocas'][0]} e "
            f"{rede['epocas'][1]} épocas.",
            "Total de treinos por seed na busca: SVM linear 25, RBF 80, polinomial 30, árvore 150, rede 120.",
        ],
        "perguntas": [
            ("Por que a rede escolhe uma configuração diferente em cada seed?",
             "Várias arquiteturas chegam ao mesmo resultado na validação, e a diferença entre elas é menor que a "
             "variação de uma divisão para outra. A escolha muda com o sorteio, mas o resultado no teste fica parecido."),
        ],
    })

    # 12 -----------------------------------------------------------------------------------------
    cl, crf, car = c["SVM RBF × SVM linear"], c["SVM RBF × random forest"], c["SVM RBF × árvore de decisão"]
    notes.append({
        "tempo": "0:45",
        "fala": f"Nas dez seeds, a SVM RBF tem a melhor acurácia, {acc['SVM RBF']}%, e o melhor F1 macro entre as SVMs, "
                f"{f1['SVM RBF']}%. Ela vence a SVM linear e a Random Forest nas dez seeds. Mas contra a árvore ajustada "
                f"é empate: vence em {car['acuracia']['seeds']} de dez, por {comma(car['acuracia']['pontos'])} ponto. E "
                f"a SVM linear dá o mesmo resultado da regressão logística. A meta foi cumprida, mas por pouco: curvar a "
                f"fronteira rende menos de um ponto.",
        "estudo": [
            f"SVM RBF − SVM linear: {signed(cl['acuracia']['pontos'], 2)} ponto de acurácia ({cl['acuracia']['seeds']} de "
            f"10 seeds), {signed(cl['f1']['pontos'], 2)} de F1 macro.",
            f"SVM RBF − Random Forest: {signed(crf['acuracia']['pontos'], 2)} ponto ({crf['acuracia']['seeds']} de 10).",
            f"SVM linear − regressão logística: {signed(c['SVM linear × regressão logística']['acuracia']['pontos'], 2)} "
            "ponto. As duas traçam uma reta nas mesmas 80 colunas; muda só a função que minimizam (hinge contra "
            "logística).",
            f"Desvios entre seeds: cerca de 0,4 ponto. Diferenças abaixo disso só valem se aparecem em quase todas as "
            "seeds.",
            "Todos os modelos sem pesos erram cerca de duas vezes mais por falso negativo (cerca de 590) que por falso "
            "positivo (cerca de 300).",
        ],
        "perguntas": [
            ("0,2 ponto sobre a árvore é uma vitória?",
             f"Não. A diferença varia cerca de 0,4 ponto de uma seed para outra, e a SVM vence em só "
             f"{car['acuracia']['seeds']} de 10. É empate. Contra a SVM linear e a Random Forest, sim: vence nas 10."),
            ("Por que nenhum modelo chega perto de 97%?",
             "Os 97,1% são um limite teórico: só seriam alcançados se o modelo acertasse todas as pessoas com perfil "
             "único. Os atributos do censo não explicam a renda tão bem; falta informação, não modelo."),
        ],
    })

    # 13 -----------------------------------------------------------------------------------------
    g03, g01 = g["0.3"], g["0.1"]
    notes.append({
        "tempo": "0:45",
        "fala": f"Pela AUC, a ordem se inverte. A SVM RBF tem {auc['SVM RBF']}%, abaixo da SVM linear e da polinomial, "
                f"com {auc['SVM linear']}%, e perde para a linear nas dez seeds. O motivo é o critério da busca: ela "
                f"escolhe pela acurácia e prefere gamma alto, que acerta o lado da fronteira, mas ordena mal as pessoas "
                f"longe dela. Nas seeds com gamma 0,3, a AUC foi {comma(g03['auc'])}%; com 0,1, {comma(g01['auc'])}%.",
        "estudo": [
            "Acurácia pergunta: ‘acertou o lado da fronteira?’. AUC pergunta: ‘quem tem renda alta ficou na frente de "
            "quem não tem?’. Um modelo pode ser bom numa e pior na outra.",
            "Com gamma alto, cada vetor de suporte só influencia a vizinhança. Longe deles, a nota de quase todo mundo "
            "cai para o mesmo valor, e a ordem entre essas pessoas se perde.",
            f"A acurácia no teste nem melhora com gamma 0,3 ({comma(g03['acuracia'])}% contra {comma(g01['acuracia'])}% "
            "com 0,1): a busca preferiu 0,3 por décimos na validação que não se repetiram no teste.",
            "Se o objetivo fosse ordenar (escolher as mil pessoas com mais chance), a busca deveria usar a AUC como "
            "critério, e provavelmente escolheria gamma menor.",
            f"A rede neural tem a melhor AUC de todos: {auc['rede neural']}%.",
        ],
        "perguntas": [
            ("Qual métrica deveria escolher o modelo?",
             "Depende do uso. Para decidir sim ou não com o corte padrão, a acurácia ou o F1. Para ordenar pessoas por "
             "chance, a AUC. O importante é escolher o critério antes, porque otimizar um pode piorar o outro."),
        ],
    })

    # 14 -----------------------------------------------------------------------------------------
    cr = c["rede neural × SVM RBF"]
    notes.append({
        "tempo": "0:40",
        "fala": f"Por fim, a rede neural da parte anterior, com a mesma grade e o mesmo protocolo. Na acurácia, a SVM RBF "
                f"fica à frente em {10 - cr['acuracia']['seeds']} das dez seeds, por {comma(-cr['acuracia']['pontos'])} "
                f"ponto. No F1 macro, empatam. Na AUC, a rede vence nas dez. E custa muito menos: a busca leva menos de "
                f"dois minutos por seed, contra oito, e a previsão é {comma(razao_prev, 0)} vezes mais rápida.",
        "estudo": [
            "Rede: MLP com ReLU e Adam, early stopping com paciência 30, grade de 6 arquiteturas × 2 alphas × 2 taxas "
            "(24 combinações), a mesma da parte 3.",
            "A rede minimiza a perda logística, ou seja, é treinada para estimar probabilidade, e por isso ordena bem "
            "em toda a faixa. A SVM é treinada só para acertar o lado da fronteira.",
            f"Depois de treinada, a rede prevê com algumas multiplicações de matrizes ({comma(rede['previsao_ms'])} ms "
            f"para o teste). A SVM RBF compara cada pessoa com cerca de {thousands(rbf['vetores'])} vetores de suporte.",
            f"A rede erra menos por falso negativo ({comma(rede['fn'], 0)}, contra {comma(rbf['fn'], 0)} da SVM RBF) e "
            f"um pouco mais por falso positivo ({comma(rede['fp'], 0)}, contra {comma(rbf['fp'], 0)}).",
            f"A rede varia mais entre seeds (desvio de {comma(rede['desvio'])} ponto na acurácia, contra "
            f"{comma(rbf['desvio'])} da SVM).",
        ],
        "perguntas": [
            ("Então a rede é melhor que a SVM?",
             "Depende do critério. Pela acurácia, a SVM RBF vence por pouco; pela AUC e pelo custo, a rede. Nesta base, "
             "as duas chegam ao mesmo nível, e a rede chega mais barato."),
        ],
    })

    # 15 -----------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:35",
        "fala": f"Para concluir. A SVM RBF teve a melhor acurácia, {acc['SVM RBF']}%, mas a vantagem sobre uma reta é "
                f"menor que um ponto. O modelo final depende do critério: pela acurácia, a SVM RBF; pela AUC, pelo F1 "
                f"macro e pelo custo, a rede neural. Da SVM, ficam três lições: padronizar é obrigatório no RBF, C e "
                f"gamma têm uma faixa boa e não um ponto ótimo, e o custo cresce com o quadrado dos dados. Obrigado.",
        "estudo": [
            "Pesos por classe (class_weight=‘balanced’), testados no notebook 05: os falsos negativos caem de 587 para "
            "221 e os falsos positivos sobem de 294 para 929; a acurácia cai para 80,9%. Útil se perder uma pessoa de "
            "renda alta custar mais que um alarme falso.",
            "Repositório: github.com/pumba-dev/machine-learning-practice, pasta renda/.",
        ],
        "perguntas": [
            ("Dá para reduzir os falsos negativos da SVM?",
             "Sim, com pesos por classe: a classe pequena passa a valer mais no treino. Os falsos negativos caem de 587 "
             "para 221, mas os falsos positivos triplicam. É uma troca, e a melhor versão depende do custo de cada erro."),
            ("Quando vale a pena usar SVM com kernel?",
             "Em bases de até algumas dezenas de milhares de linhas, com fronteira curva e atributos padronizados. Acima "
             "disso, o custo de n² pesa e a SVM linear ou uma rede costumam ser melhor escolha."),
        ],
    })
    return notes
