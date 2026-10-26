"""Roteiro e material de estudo de cada slide, para as notas do apresentador e o slides/notas.md.

Cada slide tem três partes:
    tempo, fala   o que dizer em voz alta, com o tempo previsto (o roteiro propriamente dito);
    estudo        fatos de apoio, para quem apresenta dominar o assunto; não faz parte da fala;
    perguntas     perguntas prováveis da plateia, com uma resposta curta.

Os números que vêm dos resultados (10 seeds, seed 42) saem de slides/data/slides_data.json, pelos
mesmos cálculos do relatório. Os fatos sobre a base vêm do DATASET.md e dos notebooks 01 a 03.
"""


def comma(value, digits=1):
    return f"{value:.{digits}f}".replace(".", ",")


def thousands(value):
    return f"{value:,}".replace(",", ".")


def number(text):
    """'89,4' -> 89.4"""
    return float(text.replace(",", "."))


def build_notes(d):
    m = d["multiseed"]["macros"]
    ref = d["multiseed"]["referencia"]
    ex = d["exemplo"]
    counts = ex["contagens"]
    desc = ex["descritores"]
    tree = d["arvore"]
    err = d["erros"]
    single = d["descritor_sozinho"]
    ordered = sorted(single.items(), key=lambda item: item[1], reverse=True)
    matrix = d["matriz_confusao"]["valores"]
    totals = [sum(row) for row in matrix]
    pp = number(m["accGrupAmbos"]) - number(m["accGrupDesc"])
    rf_pp = ref["Random Forest (300 árvores)"] - ref["Árvore de decisão"]
    left, right = tree["esquerda"], tree["direita"]
    piso = comma(d["piso"])

    notes = []

    # 1 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:15",
        "fala": "Bom dia, professor e colegas. Eu sou o Thiago e, com o Paulo e o Bernan, vou apresentar como "
                "usamos uma árvore de decisão para descobrir a qual proteína uma molécula está associada, e como "
                "avaliamos o resultado sem nos enganar.",
        "estudo": [
            "Disciplina: PPGCC010 – Aprendizagem de Máquina (UFPI, 2026.2), Prof. Vinicius Ponte Machado. O relatório "
            "segue o formato de artigo da SBC e tem 10 páginas.",
            "ChEMBL: banco aberto e curado de moléculas e das suas medições de potência contra proteínas, mantido pelo "
            "EMBL-EBI (Gaulton et al., 2012; Zdrazil et al., 2024). Usamos a versão ChEMBL_37, extraída em 24/10/2026 "
            "pela API REST (Davies et al., 2015).",
            "Alvo é a proteína com a qual a molécula interage. Aqui os 4 alvos são as 4 classes do problema.",
            f"Em uma frase, o trabalho é: calcular números de cada molécula, prever com uma árvore de decisão qual das "
            f"4 proteínas ela está associada e medir isso de forma honesta. Resultado: {m['accGrupAmbos']}% de acurácia "
            f"na divisão agrupada (média de 10 seeds).",
            "Código, notebooks e dados: github.com/pumba-dev/machine-learning-practice (o DATASET.md descreve a base e "
            "traz o hash SHA-256 de cada arquivo).",
        ],
        "perguntas": [
            ("Isso é um trabalho de biologia?",
             "Não. É classificação supervisionada multiclasse com atributos numéricos. A química só aparece na origem "
             "dos números."),
            ("Por que escolheram esse tema?",
             "Partimos de um conjunto do Kaggle sobre atividade biológica de moléculas e percebemos que o arquivo "
             "estava quebrado; reconstruir a base do ChEMBL virou parte do trabalho."),
        ],
    })

    # 2 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:15",
        "fala": f"Nosso problema é de classificação: dada uma molécula, prever a qual de quatro proteínas ela está "
                f"associada, EGFR, BACE1, DRD2 ou HDAC1. Reunimos {thousands(d['total_moleculas'])} moléculas, e as "
                f"classes são equilibradas, como mostram os cartões à esquerda. Isso importa para o piso de comparação: "
                f"um modelo que responde sempre EGFR, a classe mais frequente, já acerta {piso}%. Qualquer resultado só "
                f"vale se passar bem desse número. À direita, os três desafios do trabalho. Primeiro, a base de partida, "
                f"do Kaggle, estava quebrada. Segundo, os cinco descritores da base separam pouco as classes: um "
                f"descritor sozinho acerta no máximo {comma(ordered[0][1])}%. Terceiro, e mais sutil, {m['gemeas']}% das "
                f"moléculas de teste têm uma gêmea no treino, outra molécula com exatamente os mesmos descritores, o que "
                f"pode inflar o resultado. Vamos passar por cada um.",
        "estudo": [
            f"Tarefa: classificação supervisionada multiclasse, 4 classes, {thousands(d['total_moleculas'])} moléculas "
            f"na base e 27.476 na modelagem (as outras 238 não têm descritores).",
            f"Piso: responder sempre a classe majoritária (EGFR) dá {piso}% de acurácia e 11,3% de F1 macro. Acurácia é "
            f"uma métrica aceitável porque as classes são equilibradas (de 20,2% a 29,3%); também reportamos F1 macro, "
            f"a média simples do F1 das 4 classes.",
            "'Associada a um alvo' quer dizer pChEMBL ≥ 6 contra ele. pChEMBL = −log10 da concentração molar em que a "
            "molécula tem efeito: 6 equivale a 1 µM, 9 equivale a 1 nM. Quanto maior, mais potente.",
            "Os 4 alvos, só para você saber responder (não precisa falar): EGFR, receptor do fator de crescimento "
            "epidérmico, uma quinase estudada em câncer de pulmão; BACE1, beta-secretase 1, uma protease estudada em "
            "Alzheimer; DRD2, receptor de dopamina D2, alvo de antipsicóticos; HDAC1, histona desacetilase 1, enzima de "
            "regulação epigenética estudada em oncologia.",
            "Por que árvore de decisão: as regras são legíveis (perguntas de sim ou não sobre os atributos), não exige "
            "normalizar atributos e é o modelo da disciplina. Random Forest e gradient boosting entram só como teto.",
            "Os três desafios são o fio do trabalho: base quebrada (slide 3), descritores fracos (slides 4 e 5) e "
            "vazamento por gêmeas (slide 6).",
        ],
        "perguntas": [
            ("Por que só 4 alvos?",
             "É uma versão controlada do problema, inspirada no conjunto do Kaggle, que descrevia esses 4 alvos. Mais "
             "alvos é trabalho futuro."),
            ("Por que não usaram uma rede neural?",
             "O foco é a árvore de decisão pela interpretabilidade. Os modelos mais fortes aparecem só como referência "
             "de teto."),
        ],
    })

    # 3 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:00",
        "fala": "Começando pela base. Partimos de um arquivo do Kaggle que não batia com a própria descrição: 1.333 "
                "linhas em vez de 8.711, nenhuma molécula de EGFR e 95,5% das linhas de DRD2. Não dava para treinar com "
                "isso, então reconstruímos a base direto do ChEMBL, na versão 37. O funil à direita mostra o caminho. "
                "Partimos de 58.736 medições de ligação. Tiramos duplicatas e registros sem SMILES. Agrupamos por par "
                "molécula e alvo, pela mediana. Mantivemos os pares com pChEMBL de pelo menos 6, uma medida de potência. "
                "E removemos 42 moléculas associadas a mais de um alvo, porque cada molécula precisa de uma única "
                "classe. Para modelar, saem ainda 238 moléculas sem descritores. Ficamos com 27.476.",
        "estudo": [
            "Arquivo do Kaggle (versão 17, atualizada em 28/09/2026): 1.333 linhas contra as 8.711 descritas; 3 alvos em "
            "vez de 4, sem nenhuma linha de EGFR; DRD2 com 95,5%, HDAC1 com 4,4% e BACE1 com 2 linhas. A página também "
            "trazia um identificador errado para BACE1 (CHEMBL1987 é outra proteína; o correto é CHEMBL4822). As versões "
            "anteriores exigem login para baixar.",
            "Consulta à API: ensaios de ligação (assay_type = B), valor exato (relação '=') e pChEMBL preenchido, para "
            "os 4 alvos: 58.736 medições.",
            "Qualidade: 7.328 registros marcados pelo ChEMBL como duplicata potencial e 49 sem SMILES; o filtro de "
            "validade de dados não removeu nenhum. Restam 51.359.",
            "Agregação: mediana do pChEMBL por par molécula-alvo (37.424 pares; em média 1,37 medições por par, no "
            "máximo 119). A mediana é robusta a medições discrepantes do mesmo par.",
            "Limiar de potência: pChEMBL ≥ 6 (27.798 pares). O notebook 01 mostra que com limiar 5 quase tudo vira "
            "associado e com limiar 7 cada alvo perde metade ou mais das moléculas.",
            "Moléculas com mais de um alvo: 42 (35 EGFR e HDAC1, 4 DRD2 e EGFR, 3 BACE1 e EGFR); saem porque a molécula "
            "precisa de um rótulo único. Sobram 27.714.",
            "238 moléculas (0,86%) sem LogP, HBA, HBD e TPSA, quase todas moléculas muito grandes, para as quais o "
            "ChEMBL não calcula esses descritores. Saem só na modelagem, sem imputar valores.",
            "Conferência com o Kaggle: nas 525 moléculas presentes nos dois, 99,6% têm o mesmo rótulo e 99,4% os mesmos "
            "descritores.",
        ],
        "perguntas": [
            ("Por que pChEMBL ≥ 6?",
             "É o limiar usual (1 µM). Com 5 quase tudo entra e com 7 cada alvo perde metade ou mais das moléculas."),
            ("Por que tirar as moléculas com mais de um alvo?",
             "Cada molécula precisa de uma única classe. Eram só 42, então o custo é pequeno."),
            ("A reconstrução é reproduzível?",
             "Sim. O download fica em cache, o DATASET.md traz o SHA-256 dos arquivos e o notebook 01 refaz o processo."),
        ],
    })

    # 4 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:00",
        "fala": f"Antes de usar a base, é preciso entender o que o modelo enxerga. A base traz cinco descritores por "
                f"molécula, calculados pelo ChEMBL a partir da estrutura dela. Aqui estão os valores de uma molécula "
                f"real, a {ex['id']}. A massa molecular é a soma das massas dos átomos: mede o tamanho da molécula. O "
                f"LogP mede quanto ela prefere gordura a água. HBA e HBD contam os átomos aceptores e doadores de "
                f"ligação de hidrogênio: aqui, {comma(desc['HBA'], 0)} e {comma(desc['HBD'], 0)}. E a TPSA é a área "
                f"ocupada pelos átomos polares. Para o modelo, essa molécula é só uma linha com cinco números: ele não "
                f"vê a estrutura, nem o nome.",
        "estudo": [
            "Massa molecular, em dáltons: soma das massas atômicas. Na base, mediana 453,6, mínimo 127,1 e máximo "
            "3.771,3 (182 moléculas passam de 1.000).",
            "LogP: coeficiente de partição octanol/água, calculado pelo ChEMBL (ALogP, estimado a partir da estrutura, "
            "não medido em laboratório). Valor alto significa mais afinidade por gordura que por água. Mediana 3,98; "
            "faixa de −3,83 a 14,00.",
            "HBA e HBD: contagens de aceptores (em geral átomos de N e O) e de doadores (hidrogênios ligados a N ou O) "
            "de ligação de hidrogênio. Medianas 6 (0 a 18) e 2 (0 a 13).",
            "TPSA, área de superfície polar topológica, em Å²: soma de contribuições de fragmentos polares (Ertl et al., "
            "2000). Mediana 89,6; faixa de 3,2 a 404,9.",
            "Massa molecular, LogP, HBD e HBA são as quatro propriedades da regra dos cinco de Lipinski, por isso são "
            "descritores clássicos. A TPSA é um quinto descritor, também de polaridade.",
            "Leitura por alvo (medianas): DRD2 tem TPSA baixa (54,5) e HBD 1; EGFR tem as moléculas mais pesadas (497,6) "
            "e LogP 4,6; HDAC1 tem o maior HBD (3); BACE1 e HDAC1 se sobrepõem em massa, TPSA e HBA.",
            "TPSA, HBA e HBD são correlacionadas (Spearman 0,72 entre TPSA e HBA; 0,69 entre TPSA e HBD). A árvore "
            "tolera isso, mas a importância se divide entre elas.",
            "4.777 linhas (17%) repetem exatamente os 5 valores de outra linha, sempre da mesma classe: isômeros e "
            "análogos próximos. É o gancho do slide 6.",
        ],
        "perguntas": [
            ("Por que não normalizaram os atributos?",
             "Árvores só comparam um atributo com um limiar; mudar a escala não muda as divisões."),
            ("O pChEMBL não seria um bom atributo?",
             "Não: ele é o resultado do ensaio contra o próprio alvo, então vazaria o rótulo. Os descritores, ao "
             "contrário, são propriedades da molécula."),
            ("Os descritores são medidos ou calculados?",
             "Calculados pelo ChEMBL a partir da estrutura da molécula parental; são as mesmas colunas do arquivo do "
             "Kaggle (99,4% iguais nas 525 moléculas em comum)."),
        ],
    })

    # 5 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:00",
        "fala": f"Obrigado, Thiago. Será que esses cinco números bastam? Fizemos um experimento: para cada descritor, "
                f"treinamos uma árvore de decisão de profundidade 3 que enxerga só aquele descritor e medimos a "
                f"acurácia por validação cruzada. O melhor, o HBD, chega a {comma(ordered[0][1])}%, contra o piso de "
                f"{piso}%. Nenhum separa os alvos sozinho. Então criamos 12 atributos novos a partir do SMILES, o texto "
                f"que descreve a estrutura da molécula, só contando caracteres. Na molécula do exemplo, são "
                f"{counts['smiles_len']} caracteres, {counts['n_N']} átomos de nitrogênio, {counts['n_O']} de oxigênio, "
                f"{counts['n_rings']} anéis e {counts['n_aromatic']} átomos aromáticos. É uma representação simples, "
                f"mas, como vamos ver, carrega bastante informação.",
        "estudo": [
            f"Experimento do descritor isolado: árvore de profundidade 3, validação cruzada de 5 partes, um descritor por "
            f"vez. HBD {comma(single['HBD'])}%, TPSA {comma(single['TPSA'])}%, HBA {comma(single['HBA'])}%, LogP "
            f"{comma(single['LogP'])}%, massa molecular {comma(single['Molecular Weight'])}%; piso {piso}%. É um "
            f"diagnóstico, não o modelo final.",
            "SMILES (Weininger, 1988): a molécula escrita como texto. Letras são átomos (minúscula indica átomo "
            "aromático), dígitos fecham anéis, parênteses abrem ramificações, '=' é ligação dupla, '#' é tripla, '+' e "
            "'-' são cargas e '@' e '/' marcam estereoquímica.",
            "Os 12 atributos: comprimento da cadeia; número de átomos de N, de O e de S; de halogênios (F, Cl, Br, I); de "
            "anéis (dígitos de fechamento divididos por 2); de ramificações; de átomos aromáticos; de ligações duplas e "
            "de triplas; de cargas; e de marcas de estereoquímica.",
            f"Leitura da molécula de exemplo ({ex['classe']}): {counts['smiles_len']} caracteres; N = {counts['n_N']}, "
            f"O = {counts['n_O']}, S = {counts['n_S']}; halogênios = {counts['n_halogen']}; anéis = {counts['n_rings']}; "
            f"ramificações = {counts['n_branch']}; aromáticos = {counts['n_aromatic']}; ligações duplas = "
            f"{counts['n_double']}; triplas = {counts['n_triple']}; cargas = {counts['n_charge']}; estereoquímica = "
            f"{counts['n_stereo']}.",
            "Limite: contar caracteres diz quantos átomos de cada tipo existem, mas não como eles se ligam; não enxerga "
            "subestruturas.",
            f"Adiantando o resultado: só as 12 contagens dão {m['accGrupSmiles']}%, mais que os 5 descritores "
            f"({m['accGrupDesc']}%); juntos, {m['accGrupAmbos']}% (divisão agrupada, média de 10 seeds).",
        ],
        "perguntas": [
            ("Por que não usaram uma biblioteca de química?",
             "Foi uma decisão do projeto: ficar só com as propriedades do ChEMBL e contagens simples. Representações "
             "estruturais exigiriam essa biblioteca e são o próximo passo."),
            ("Usar o SMILES não é vazamento?",
             "Não: o SMILES é entrada, não rótulo. O risco é outro: moléculas parecidas no treino e no teste. O "
             "agrupamento por descritores idênticos não cobre isso, e declaramos como limitação."),
            ("Como contam os halogênios?",
             "F, Cl, Br e I. Cl e Br são tratados como um símbolo só para o 'C' de Cl não ser contado como carbono."),
        ],
    })

    # 6 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:30",
        "fala": f"Agora o cuidado central do trabalho: como avaliar. Muitas moléculas diferentes têm exatamente os mesmos "
                f"cinco descritores, e para o modelo elas são o mesmo ponto. Na divisão aleatória, à esquerda, uma dessas "
                f"gêmeas pode cair no treino e a outra no teste, e acertar o teste vira só lembrar o treino. É o que o "
                f"desenho mostra: as linhas tracejadas atravessam a fronteira. Medimos que {m['gemeas']}% das moléculas "
                f"de teste têm gêmea no treino. Na divisão agrupada, à direita, todas as gêmeas ficam do mesmo lado, e o "
                f"teste exige generalizar. Comparamos então três conjuntos de atributos, só descritores, só SMILES e os "
                f"dois juntos, com as duas divisões. São seis cenários, e repetimos tudo com dez seeds, para a conclusão "
                f"não depender de um sorteio de sorte. Um detalhe: a validação que escolhe os hiperparâmetros também "
                f"respeita os grupos.",
        "estudo": [
            "Vazamento de dados é quando informação do conjunto de teste chega ao treino; é uma causa conhecida de "
            "resultados superestimados (Kapoor e Narayanan, 2023).",
            f"Números: das 27.476 moléculas, 22.699 têm uma tupla de descritores distinta e 4.777 repetem a de outra "
            f"molécula; o maior grupo tem 12; nenhum grupo mistura classes. Na divisão aleatória, {m['gemeas']} ± "
            f"{m['sdGemeas']}% do teste tem gêmea no treino (10 seeds; na seed 42, 25,4%).",
            "Por que isso infla o resultado: a árvore sem limite de profundidade decora o treino. Como a gêmea é o mesmo "
            "ponto e tem a mesma classe, acertá-la não exige generalizar.",
            "Como é a divisão agrupada: validação cruzada de 5 partes, estratificada por classe e sem separar grupos "
            "(StratifiedGroupKFold, do scikit-learn); uma parte (20%) é o teste. As duas divisões têm 21.980 moléculas "
            "de treino e 5.496 de teste e preservam a proporção das classes.",
            "A validação cruzada interna, que escolhe os hiperparâmetros, também é agrupada. Com dobras comuns ela ficaria "
            "cerca de 5 pontos otimista, segundo o comentário no código.",
            "Busca em grade, 72 combinações: critério (Gini ou entropia), profundidade máxima (8, 12, 16 ou sem limite), "
            "mínimo por folha (1, 5 ou 20) e poda α (0, 1e-4 ou 3e-4). Em todos os cenários venceram a entropia, sem "
            "limite de profundidade e folha mínima 1; a poda só entrou com os descritores sozinhos.",
            "Os 6 cenários são os 3 conjuntos de atributos (descritores, SMILES, ambos) vezes as 2 divisões. As 10 seeds "
            "(0 a 9) mudam as divisões, as partes da validação e a semente dos modelos; a base é a mesma.",
            "Limite: o agrupamento só vê descritores idênticos. Moléculas muito parecidas (da mesma série química) "
            "continuam espalhadas entre treino e teste. Dividir por esqueleto molecular seria mais exigente e precisa de "
            "biblioteca de química.",
            "O desenho do slide é um esquema, não são dados reais.",
        ],
        "perguntas": [
            (f"Por que {m['gemeas']}% e não 20%?",
             "20% é o tamanho do teste. O número do slide é a fração dessas moléculas de teste cuja tupla de descritores "
             "também aparece no treino."),
            ("Isso não é só overfitting?",
             "A árvore sem poda ajusta 100% do treino nos dois casos. O problema é de avaliação: na divisão aleatória o "
             "teste não é independente do treino."),
            ("Por que 10 seeds?",
             "Um único sorteio pode ser favorável por acaso. As seeds mudam as divisões e as partes da validação; a base "
             "continua a mesma, então o desvio não mede incerteza para dados novos."),
        ],
    })

    # 7 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:00",
        "fala": f"O resultado principal está neste gráfico, em média de dez seeds. Na divisão agrupada, os descritores "
                f"sozinhos dão {m['accGrupDesc']}% de acurácia. Juntando as contagens de SMILES, chegamos a "
                f"{m['accGrupAmbos']}%: um ganho relativo de {m['ganhoAmbos']}%. Repare no efeito da divisão aleatória, "
                f"as colunas cinza. Ela superestima o resultado em {m['gapDesc']}% quando só há descritores, porque a "
                f"árvore decora as gêmeas. Com os atributos de SMILES, o excesso cai para {m['gapSmiles']}%, porque "
                f"moléculas com os mesmos descritores têm SMILES diferentes. O desvio padrão fica abaixo de "
                f"{comma(d['multiseed']['dp_maximo'])}%, então a diferença é bem maior que a variação entre seeds.",
        "estudo": [
            f"Descritores: {m['accAleatDesc']}% na aleatória e {m['accGrupDesc']} ± {m['sdGrupDesc']}% na agrupada. "
            f"Só SMILES: {m['accAleatSmiles']}% e {m['accGrupSmiles']} ± {m['sdGrupSmiles']}%. Ambos: "
            f"{m['accAleatAmbos']}% e {m['accGrupAmbos']} ± {m['sdGrupAmbos']}%.",
            f"Ganho relativo = (B − A) / A, calculado por seed e depois com a média. De {m['accGrupDesc']}% para "
            f"{m['accGrupAmbos']}% são {comma(pp)} pontos percentuais, ou {m['ganhoAmbos']}% em relação a "
            f"{m['accGrupDesc']}%. O artigo usa o relativo; só as contagens de SMILES já dão {m['ganhoSmiles']}% sobre os "
            f"descritores.",
            f"Superestimativa da divisão aleatória, também relativa: {m['gapDesc']} ± {m['sdGapDesc']}% com descritores, "
            f"{m['gapSmiles']}% com SMILES e {m['gapAmbos']}% com ambos.",
            "Por que a superestimativa quase some com SMILES: duas moléculas com os mesmos descritores têm SMILES "
            "diferentes, então as contagens não são copiadas junto e decorar vale menos.",
            f"F1 macro é a média simples do F1 das 4 classes; com classes equilibradas fica perto da acurácia "
            f"({m['fscoreGrupAmbos']}% no cenário com os 17 atributos). Por classe: EGFR {m['fscoreEGFR']}%, BACE1 "
            f"{m['fscoreBACEone']}%, DRD2 {m['fscoreDRDtwo']}%, HDAC1 {m['fscoreHDACone']}%.",
            f"Na seed 42, usada nas figuras e nos notebooks, a árvore acerta 89,7%, dentro da faixa de {m['faixaMin']}% a "
            f"{m['faixaMax']}% das 10 seeds.",
        ],
        "perguntas": [
            ("Fizeram teste estatístico?",
             f"Não. Usamos média e desvio padrão entre seeds. O ganho de {comma(pp)} pontos percentuais é muito maior que "
             f"o desvio ({comma(d['multiseed']['dp_maximo'])}% no máximo)."),
            ("Por que ganho relativo e não em pontos?",
             f"É escolha de apresentação, e os dois dizem o mesmo: {comma(pp)} pontos percentuais equivalem a "
             f"{m['ganhoAmbos']}% sobre {m['accGrupDesc']}%."),
            ("Qual conjunto de atributos vocês escolheram?",
             "Os 17 atributos juntos com divisão agrupada: é o cenário honesto, com o melhor desempenho."),
        ],
    })

    # 8 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:00",
        "fala": f"Obrigado, Paulo. Para saber se {m['accGrupAmbos']}% é bom, comparamos com um piso e um teto. A "
                f"Random Forest chega a {m['accRF']}% e o gradient boosting a {m['accHGB']}%: a Random Forest supera a "
                f"nossa árvore em {m['ganhoRF']}%. Então por que ficar com a árvore? Porque só ela tem regras legíveis. À "
                f"direita, a primeira pergunta é: a TPSA é no máximo {comma(tree['raiz']['limiar'])}? Se sim, "
                f"{comma(left['fatia_classe'] * 100, 0)}% das moléculas são {left['classe']}. A árvore completa tem "
                f"{thousands(tree['folhas'])} folhas, e a TPSA e o número de átomos aromáticos são os atributos mais "
                f"importantes. Ou seja, dá para explicar por que uma molécula foi classificada como DRD2, o que um "
                f"conjunto de árvores não oferece.",
        "estudo": [
            f"Random Forest com 300 árvores ({m['accRF']} ± {m['sdRF']}%) e gradient boosting baseado em histogramas "
            f"({m['accHGB']} ± {m['sdHGB']}%), ambos sem ajuste de hiperparâmetros, na mesma divisão agrupada e com os 17 "
            f"atributos. Servem de teto de referência.",
            f"Diferença: {comma(rf_pp)} pontos percentuais, ou {m['ganhoRF']}% em termos relativos. Piso: {piso}%.",
            f"A árvore escolhida (seed 42) tem {thousands(tree['folhas'])} folhas e 24 níveis. Sobreajuste: o treino chega a "
            f"100% na profundidade 25 e a validação estaciona perto de 87% a partir da 16.",
            "Poda por custo-complexidade: com α = 1e-4 a árvore cai de 2.054 para 899 folhas sem perder acurácia de "
            "validação (87,0% para 87,2%); a partir de 1e-3 a poda custa acurácia e com α = 1e-2 sobram 8 folhas e 66,5%. "
            "Na busca em grade, a poda só venceu com os descritores sozinhos.",
            f"Raiz: TPSA ≤ {comma(tree['raiz']['limiar'])}. Ramo 'sim': {comma(left['fatia'] * 100)}% das moléculas, "
            f"{comma(left['fatia_classe'] * 100, 0)}% são {left['classe']}. Ramo 'não': "
            f"{comma(right['fatia'] * 100)}% das moléculas; a classe mais comum é {right['classe']}, com só "
            f"{comma(right['fatia_classe'] * 100, 0)}% (mistura). Depois vêm átomos aromáticos (≤ 14 no ramo 'sim', ≤ 12 "
            f"no 'não'), HBD, anéis, comprimento do SMILES e halogênios.",
            "Importância dos atributos (seed 42), por duas medidas: por impureza, medida no treino, e por permutação, a "
            "queda de acurácia no teste ao embaralhar o atributo. TPSA e átomos aromáticos lideram nas duas (queda perto "
            "de 0,26 na permutação), seguidos de HBD (perto de 0,17) e de contagens de SMILES (átomos de N, halogênios, "
            "estereoquímica, anéis) acima de LogP e HBA.",
        ],
        "perguntas": [
            ("Por que não podaram a árvore?",
             "A busca em grade incluía poda (α de 0, 1e-4 e 3e-4) e, com os atributos de SMILES, a melhor foi sem poda. "
             "A poda reduz folhas sem perder acurácia, mas escolhemos pela validação."),
            ("Vale perder cerca de 6% por causa da interpretabilidade?",
             "Depende do uso. A árvore explica cada previsão com um caminho de perguntas; os conjuntos de árvores não têm "
             "regras legíveis."),
            ("A Random Forest sem ajuste não é injusta com ela?",
             "Pode estar subestimando o teto, e dizemos isso nas limitações. Ela serve só de referência."),
        ],
    })

    # 9 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:00",
        "fala": f"Onde a árvore erra? A matriz de confusão, na seed 42, mostra que o maior erro é entre HDAC1 e EGFR: "
                f"{comma(err['par_hdac1_egfr'])}% de todos os erros. Olhamos exemplos desses erros e alguns têm um mesmo "
                f"grupo de átomos, o C(=O)NO, que contagens de caracteres não conseguem distinguir. Outro ponto "
                f"importante: sem poda, toda folha da árvore é pura, então ela diz ter "
                f"{comma(err['previsoes_com_confianca_100'], 0)}% de confiança nas {thousands(err['teste'])} previsões do "
                f"teste, embora {comma(err['percentual_erro'])}% estejam erradas. A confiança dela, portanto, não "
                f"distingue acerto de erro. Isso aponta para os próximos passos.",
        "estudo": [
            f"Matriz (seed 42): acertos EGFR {thousands(matrix[0][0])} de {thousands(totals[0])}, BACE1 "
            f"{thousands(matrix[1][1])} de {thousands(totals[1])}, DRD2 {thousands(matrix[2][2])} de "
            f"{thousands(totals[2])}, HDAC1 {thousands(matrix[3][3])} de {thousands(totals[3])}. Erros: {err['total']} "
            f"de {thousands(err['teste'])} ({comma(err['percentual_erro'])}%).",
            f"Maiores confusões: HDAC1 lido como EGFR (88, 15,5% dos erros), EGFR como HDAC1 (75, 13,2%), DRD2 como EGFR "
            f"(63, 11,1%), BACE1 como EGFR (52, 9,2%). HDAC1 e EGFR juntos somam {comma(err['par_hdac1_egfr'])}%; 7,9% "
            f"das moléculas de HDAC1 viram EGFR.",
            "Os erros não se concentram numa região: acertos e erros têm medianas quase iguais nos 17 atributos. Só o "
            "número de átomos de O (+1) e de halogênios (−1) se deslocam meio intervalo interquartil.",
            "C(=O)NO é o grupo hidroxamato, típico de inibidores de HDAC. Entre 6 exemplos de HDAC1 lidos como EGFR, 2 o "
            "têm. As contagens dizem quantos átomos de O e N existem, mas não como estão ligados.",
            "Confiança: sem poda toda folha é pura, então a probabilidade de classe que a árvore reporta (a pureza da "
            "folha) é sempre 100%. Por isso ela não distingue acerto de erro. Probabilidade calibrada exigiria poda ou um "
            "conjunto de árvores.",
            "Curva de aprendizado: a acurácia de validação sobe de 61,5% (879 linhas) a 87,0% (17.584) e não achata, "
            "então mais dados provavelmente ajudariam.",
        ],
        "perguntas": [
            ("Como reduzir o erro entre HDAC1 e EGFR?",
             "Com uma representação que enxergue subestruturas, como representações estruturais da molécula, e com mais "
             "dados."),
            ("Se a árvore diz 100% de confiança, como confiar nela?",
             "Não se deve confiar nessa probabilidade: ela é a pureza da folha. Para priorizar moléculas seria preciso "
             "calibrar, com poda ou com um conjunto de árvores."),
            ("O erro é maior em alguma classe?",
             f"HDAC1 é a mais difícil (F1 {m['fscoreHDACone']}%); BACE1 é a mais fácil ({m['fscoreBACEone']}%)."),
        ],
    })

    # 10 -----------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:00",
        "fala": f"Resumindo. Com avaliação honesta, a árvore chega a {m['accGrupAmbos']}% de acurácia. Contar o SMILES dá "
                f"um ganho relativo de {m['ganhoAmbos']}% sobre só os descritores. E a divisão aleatória superestimaria o "
                f"resultado entre {m['gapMin']}% e {m['gapMax']}%. Os limites: o agrupamento cobre só descritores "
                f"idênticos, não famílias de moléculas parecidas; o modelo sempre escolhe uma entre quatro classes; e não "
                f"há validação externa. Como próximos passos: representações estruturais da molécula, divisão por "
                f"esqueleto molecular, mais dados e probabilidades calibradas. O código e os dados estão no repositório. "
                f"Obrigado, e estamos abertos a perguntas.",
        "estudo": [
            f"Contribuições: (1) uma base reconstruída do ChEMBL_37 com {thousands(d['total_moleculas'])} moléculas de "
            f"quatro alvos; (2) 12 atributos obtidos só contando caracteres do SMILES, com ganho relativo de "
            f"{m['ganhoAmbos']}%; (3) avaliação com divisão agrupada e 10 seeds, que mede a superestimativa da divisão "
            f"aleatória e situa a árvore entre o piso ({piso}%) e o teto (Random Forest, {m['accRF']}%).",
            "Limites em detalhe: o agrupamento só considera descritores idênticos; o modelo é de conjunto fechado de 4 "
            "classes, sem a opção 'nenhuma das quatro'; as 10 seeds variam o sorteio mas não os dados, então o desvio não "
            "mede incerteza para dados novos; não há validação externa; Random Forest e gradient boosting estão sem "
            "ajuste; 238 moléculas sem descritores foram descartadas; as probabilidades da árvore não são calibradas.",
            "Próximos passos: representações estruturais da molécula (calculadas com biblioteca de química) enxergariam "
            "subestruturas como o C(=O)NO; divisão por esqueleto molecular daria uma estimativa menos otimista; mais "
            "dados (outros alvos ou limiar de pChEMBL mais baixo), já que a curva de aprendizado ainda sobe; e poda ou "
            "conjunto de árvores para probabilidades calibradas.",
            "Reprodutibilidade: seeds de 0 a 9, notebooks 01 a 03, hash SHA-256 de cada arquivo no DATASET.md; dados "
            "derivados do ChEMBL sob a licença CC BY-SA 3.0.",
        ],
        "perguntas": [
            ("Qual a principal contribuição?",
             f"Mostrar, com um protocolo reproduzível, que contar o SMILES dá {m['ganhoAmbos']}% de ganho relativo e que a "
             f"divisão aleatória superestima o resultado em {m['gapMin']}% a {m['gapMax']}%."),
            ("Dá para usar isso na prática?",
             "Ainda não: são só 4 classes fixas, a estimativa ainda é otimista para moléculas novas e não há validação "
             "externa."),
            ("Por que acurácia e F1 macro, e não AUC?",
             "O problema é multiclasse e as classes são equilibradas; acurácia e F1 macro resumem bem. A matriz de "
             "confusão mostra onde erra."),
        ],
    })
    return notes
