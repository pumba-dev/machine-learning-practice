"""Roteiro e material de estudo da quinta apresentação (K-means na base de renda).

Mesmo formato de slides_svm_notes.py: para cada slide, `tempo` e `fala` (o que dizer), `estudo` (apoio para
quem apresenta; não faz parte da fala) e `perguntas` (perguntas prováveis, com resposta curta).

Os números saem de report/results/clusters_dados.json, gerado por clusters_data.py a partir dos resultados
do notebook 07.
"""


def comma(value, digits=1):
    return f"{value:.{digits}f}".replace(".", ",")


def thousands(value):
    return f"{value:,}".replace(",", ".")


def build_notes(d):
    b, lg, pk, e, gr, ref = d["base"], d["log"], d["por_k"], d["escolha"], d["grupos"], d["referencia"]
    k6, k5, k8, k2 = pk["6"], pk["5"], pk["8"], pk["2"]
    sem, com = lg["sem"]["grupos"], lg["com"]["grupos"]
    g = {item["grupo"]: item for item in gr}
    q = d["quedas_inercia"]
    acima_chute = e["pureza"] - e["chute"]

    notes = []

    # 1 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:25",
        "fala": "Bom dia, professor e colegas. Eu sou o Thiago e, com o Paulo e o Bernan, vou apresentar a quinta "
                "parte do trabalho. A base é a mesma da SVM, as pessoas do censo americano, mas a pergunta muda: em vez "
                "de prever a renda, queremos descobrir que grupos de pessoas existem nessa base. O algoritmo é o "
                "K-means, o primeiro método não supervisionado do trabalho.",
        "estudo": [
            "Disciplina: PPGCC010 – Aprendizagem de Máquina (UFPI, 2026.2), Prof. Vinicius Ponte Machado.",
            "Tudo no repositório, pasta renda/: notebook 07_kmeans, módulo src/clusters.py, resultados em "
            "renda/resultados/clusters_*.csv.",
            "Biblioteca: scikit-learn (KMeans, silhouette_score, davies_bouldin_score, adjusted_rand_score, PCA).",
            "O professor pediu K-means; o agrupamento hierárquico (Ward) ficou de fora por decisão do grupo.",
        ],
        "perguntas": [
            ("Por que usar a mesma base da SVM?",
             "Porque já conhecemos bem os atributos e a renda. Assim dá para conferir, no fim, se os grupos "
             "encontrados sem a renda têm relação com ela, e comparar com o que os classificadores alcançaram."),
        ],
    })

    # 2 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:35",
        "fala": "Até agora, todos os modelos eram supervisionados: recebiam os atributos e a resposta, a renda, e "
                "aprendiam a prever. O K-means é não supervisionado: recebe só os atributos e procura grupos de pessoas "
                f"parecidas entre si. Usamos as mesmas {thousands(b['linhas'])} pessoas e os mesmos 10 atributos da SVM. "
                "Não há divisão em treino e teste, porque não há resposta a acertar. A renda entra só no final, para "
                "conferir se os grupos têm alguma relação com ela.",
        "estudo": [
            "Supervisionado: aprende uma função atributos → rótulo. Não supervisionado: descobre estrutura só nos "
            "atributos (grupos, direções de variação, anomalias).",
            "Sem treino e teste: o agrupamento é feito na base inteira. Não há vazamento, porque a renda nunca entra "
            "no ajuste.",
            "Atributos: idade, anos de estudo, ganho e perda de capital, horas por semana; classe de trabalho, estado "
            "civil, ocupação, relacionamento, país.",
        ],
        "perguntas": [
            ("Se não há resposta, como saber se o resultado é bom?",
             "Com métricas internas, que olham só os atributos: compacidade e separação dos grupos (inércia, "
             "silhueta, Davies-Bouldin) e estabilidade entre seeds. A renda serve como conferência externa no fim."),
        ],
    })

    # 3 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:40",
        "fala": "O K-means funciona em quatro passos. Primeiro, escolhe k pontos como centros iniciais. Segundo, cada "
                "pessoa vai para o centro mais próximo. Terceiro, cada centro passa a ser a média das pessoas do seu "
                "grupo. E repete os passos dois e três até os grupos pararem de mudar. O objetivo é deixar os grupos "
                "compactos: a soma das distâncias de cada pessoa ao seu centro, a inércia, deve ser a menor possível. "
                "Como o resultado depende do sorteio inicial, rodamos dez inicializações e ficamos com a melhor.",
        "estudo": [
            "Inércia: soma, para todas as pessoas, da distância euclidiana ao quadrado até o centro do seu grupo.",
            "k-means++: o primeiro centro é uma pessoa sorteada; os seguintes são sorteados com mais chance para "
            "pessoas longe dos centros já escolhidos. Espalha os centros e evita começos ruins.",
            "n_init = 10: o algoritmo roda 10 vezes, com 10 sorteios de centros, e devolve a de menor inércia.",
            "Seed: fixa o gerador dos sorteios; a mesma seed dá sempre as mesmas 10 inicializações.",
            "Custo: proporcional a pessoas × k × colunas × iterações; cresce linearmente com o número de pessoas.",
            "Limite: o algoritmo sempre converge, mas para um mínimo local, não necessariamente o melhor possível.",
        ],
        "perguntas": [
            ("O K-means sempre acha a melhor divisão?",
             "Não. Ele sempre converge, mas para um mínimo local, que depende dos centros iniciais. Por isso as 10 "
             "inicializações; mais adiante mostramos o que acontece com uma só."),
            ("Quem escolhe o k?",
             "Nós. O K-means não descobre o número de grupos; testamos k de 2 a 10 e escolhemos com métricas e com a "
             "leitura dos grupos."),
        ],
    })

    # 4 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:40",
        "fala": f"Como tudo depende da distância, o preparo dos dados é decisivo. São {b['colunas']} colunas: os cinco "
                "numéricos com padronização, média zero e desvio um, e os cinco atributos de texto em one-hot, uma "
                "coluna de zero ou um por categoria. Isso cria um efeito curioso: duas pessoas com ocupações "
                "diferentes diferem em duas colunas, e ficam tão distantes quanto duas pessoas com "
                f"{comma(b['troca_em_anos'], 0)} anos de diferença de idade. Em média, os atributos de texto respondem "
                f"por {comma(b['parte_categoricos'], 0)}% da distância; o país quase nada, porque quase todos são dos "
                "Estados Unidos.",
        "estudo": [
            "Padronização (z-score): (valor − média) / desvio padrão. Não é o mesmo que normalização (min-max), que "
            "leva os valores para o intervalo de 0 a 1 e depende só do mínimo e do máximo.",
            "One-hot: classe de trabalho 7 colunas, estado civil 7, ocupação 14, relacionamento 6, país 41: 75 colunas.",
            "Numa troca de categoria, uma coluna vai de 1 a 0 e outra de 0 a 1: distância ao quadrado 1² + 1² = 2, "
            f"igual a √2 ≈ 1,41 desvio num numérico. Na idade (desvio de {comma(b['desvio_idade'])} anos), "
            f"{comma(b['troca_em_anos'])} anos.",
            "Peso médio de um atributo: 2 × variância das suas colunas. Numérico padronizado: 2. Categórico: 2 × "
            "(1 − Σp²), a chance de duas pessoas sorteadas terem categorias diferentes, vezes 2.",
            f"Partes da distância média: ocupação {comma(b['peso']['ocupação']['parte'])}%, relacionamento "
            f"{comma(b['peso']['relacionamento']['parte'])}%, estado civil {comma(b['peso']['estado civil']['parte'])}%, "
            f"classe de trabalho {comma(b['peso']['classe de trabalho']['parte'])}%, país "
            f"{comma(b['peso']['país de origem']['parte'])}%; cada numérico {comma(b['peso']['idade']['parte'])}%.",
        ],
        "perguntas": [
            ("Padronização é o mesmo que normalização?",
             "Não. Padronização deixa cada atributo com média 0 e desvio 1; normalização (min-max) leva os valores "
             "para o intervalo de 0 a 1 e depende só do mínimo e do máximo. Usamos padronização."),
            ("Por que não dar outro peso aos atributos de texto?",
             "Daria para reescalar as colunas one-hot, mas toda escolha muda o que é ‘parecido’. Mantivemos o one-hot "
             "puro, o mesmo da SVM, e mostramos o peso de cada atributo para ajudar a ler os grupos."),
        ],
    })

    # 5 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:45",
        "fala": "O ganho e a perda de capital são zero para quase todo mundo e enormes para poucos. Sem nenhum ajuste, "
                f"as {b['ganho_teto']} pessoas com ganho de 99.999 dólares, o teto do censo, ficam a "
                f"{comma(lg['sem']['ganho_max_desvios'], 0)} desvios da média e formam um grupo só delas. Aplicamos o "
                "logaritmo antes da padronização, e esse grupo desaparece. Mas surge outro efeito: ter ou não ter "
                f"capital vira o maior salto da base. Quem tem ganho, cerca de {thousands(com[2]['pessoas'])} pessoas, "
                f"e quem tem perda, {thousands(com[3]['pessoas'])}, formam grupos próprios. Ou seja, dois grupos ficam "
                f"com os {comma(b['com_capital'], 0)}% que têm capital, e os outros grupos dividem o resto.",
        "estudo": [
            f"Com ganho de capital: {comma(b['com_ganho'])}% das pessoas; com perda: {comma(b['com_perda'])}%.",
            "Log usado: log(1 + x), porque log(0) não existe. 99.999 → 11,5; 15.024 → 9,6; 7.688 → 8,9; 0 → 0.",
            f"Sem log (k = 4, seed 42): grupos de {thousands(sem[0]['pessoas'])}, {thousands(sem[1]['pessoas'])}, "
            f"{thousands(sem[2]['pessoas'])} (perda de capital) e {sem[3]['pessoas']} (ganho de 99.999, "
            f"{comma(sem[3]['positivos'], 0)}% acima de 50 mil).",
            f"Com log: grupos de {thousands(com[0]['pessoas'])}, {thousands(com[1]['pessoas'])}, "
            f"{thousands(com[2]['pessoas'])} (todos com ganho, {comma(com[2]['positivos'])}% acima de 50 mil) e "
            f"{thousands(com[3]['pessoas'])} (todos com perda, {comma(com[3]['positivos'])}%).",
            f"Por que o salto: com log, quem tem zero fica em {comma(lg['com']['ganho_zero_desvios'], 2)} desvio e quem "
            "tem algum ganho fica perto de +3; a diferença ao quadrado passa de 10, mais que qualquer troca de "
            "categoria (2).",
            "Alternativas avaliadas e não usadas: capital como ‘tem / não tem’ (0 ou 1) ou fora do agrupamento.",
        ],
        "perguntas": [
            ("O log não deveria ter resolvido o problema do capital?",
             "Resolveu o dos extremos: o grupo das 148 pessoas com 99.999 sumiu. Mas comprimir os valores aproxima "
             "quem tem capital entre si e mantém o salto em relação a quem tem zero. Os grupos do capital que "
             "aparecem são reais e têm sentido: concentram a renda alta."),
        ],
    })

    # 6 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:40",
        "fala": "Obrigado, Thiago. O K-means não escolhe o número de grupos; somos nós que escolhemos o k. Testamos de "
                "2 a 10, e para cada k usamos três métricas que olham só os atributos, nunca a renda. A inércia mede a "
                "compacidade e sempre cai quando k aumenta, então procuramos o cotovelo, o ponto em que ela para de cair "
                "rápido. A silhueta pergunta se cada pessoa está mais perto do próprio grupo do que do vizinho: quanto "
                "maior, melhor. E o Davies-Bouldin mede a sobreposição entre grupos: quanto menor, melhor.",
        "estudo": [
            "Silhueta de uma pessoa: (b − a) / máx(a, b), com a = distância média ao próprio grupo e b = distância "
            "média ao grupo vizinho mais próximo. Vai de −1 a 1; a métrica é a média.",
            "A silhueta compara todos os pares (custo de ordem n²): calculada numa amostra fixa de 10 mil pessoas, a "
            "mesma em todos os ajustes.",
            "Davies-Bouldin: para cada grupo, o pior caso de (espalhamento do grupo + espalhamento do vizinho) / "
            "distância entre os centros; a métrica é a média. Mínimo 0.",
            "Cada k foi rodado com as 10 seeds (0 a 9), cada uma com 10 inicializações: 90 ajustes.",
        ],
        "perguntas": [
            ("Por que não escolher o k com a menor inércia?",
             "Porque a inércia sempre cai com k: com uma pessoa por grupo, ela é zero. O que interessa é onde ela "
             "deixa de cair rápido, o cotovelo."),
        ],
    })

    # 7 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:40",
        "fala": f"E as métricas não apontam um k claro. Silhueta e Davies-Bouldin preferem k igual a 2, mas esse k só "
                "separa quem tem ganho de capital do resto: é a fronteira mais nítida da base, e diz pouco sobre as "
                f"pessoas. De k igual a 4 em diante, as duas curvas ficam planas, com silhueta em torno de "
                f"{comma(k6['silhueta'], 2)}. Isso é baixo: indica que a base não tem grupos bem separados. Os grupos "
                "são regiões de uma nuvem contínua. Na inércia, o cotovelo fica entre 5 e 6.",
        "estudo": [
            f"Silhueta média por k: 2: {comma(k2['silhueta'], 2)}; 5: {comma(k5['silhueta'], 2)}; 6: "
            f"{comma(k6['silhueta'], 2)}; 8: {comma(k8['silhueta'], 2)}. Acima de 0,5 indicaria grupos bem separados.",
            f"Davies-Bouldin: 2: {comma(k2['db'], 2)}; de 3 a 10, entre 1,66 e 1,72.",
            f"Quedas da inércia: 2→3 {thousands(round(q['2-3']))}; 3→4 {thousands(round(q['3-4']))}; 4→5 "
            f"{thousands(round(q['4-5']))}; 5→6 {thousands(round(q['5-6']))}; depois, entre 4 e 6 mil.",
            "Em k = 2, 9 seeds separam quem tem ganho (2.533 pessoas) e uma separa quem tem perda (1.427).",
        ],
        "perguntas": [
            ("Silhueta de 0,17 não quer dizer que o agrupamento falhou?",
             "Quer dizer que os grupos não são ilhas separadas: as pessoas variam de forma contínua. O K-means sempre "
             "divide; o que avaliamos é se a divisão é estável e interpretável, e ela é."),
        ],
    })

    # 8 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:35",
        "fala": "Como as métricas empatam, olhamos a estabilidade. Para cada k, as dez seeds geram dez partições, e "
                "comparamos todos os pares pelo ARI, que vale 1 quando duas partições põem as mesmas pessoas juntas e "
                f"zero quando a concordância é a do acaso. Com k igual a 5, 6 e 8, as dez seeds chegam praticamente aos "
                f"mesmos grupos, com ARI de {comma(k5['ari'], 2)} ou mais. Já k igual a 3 e 9 são instáveis: cada seed "
                "divide de um jeito.",
        "estudo": [
            "ARI (Adjusted Rand Index): conta os pares de pessoas que as duas partições põem juntas ou separadas, "
            "corrigido pelo acaso. Não depende do número dado a cada grupo.",
            "45 pares de seeds por k (10 seeds, combinadas duas a duas).",
            f"ARI médio: 3: {comma(pk['3']['ari'], 2)}; 5: {comma(k5['ari'], 3)}; 6: {comma(k6['ari'], 3)}; 7: "
            f"{comma(pk['7']['ari'], 2)}; 8: {comma(k8['ari'], 3)}; 9: {comma(pk['9']['ari'], 2)}.",
            "Um k instável sugere que o algoritmo corta uma região sem fronteira natural.",
        ],
        "perguntas": [
            ("O número de cada grupo muda entre seeds. O ARI não se confunde?",
             "Não. O ARI olha só se cada par de pessoas está junto ou separado nas duas partições; os nomes dos grupos "
             "não importam."),
        ],
    })

    # 9 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:35",
        "fala": "Essa estabilidade vem das dez inicializações. Se cada seed fizer um sorteio só, cada uma para num "
                f"mínimo local diferente: com k igual a 6, o ARI cai de {comma(k6['ari'], 3)} para "
                f"{comma(k6['ari_1'], 2)}, e a inércia piora em média {comma(k6['inercia_piora_1'], 0)}%. Com dez "
                f"inicializações, o ajuste leva menos de um segundo, {comma(k6['tempo_s'], 1)} segundo nas 30 mil "
                "pessoas. É um custo pequeno para ter sempre a mesma resposta.",
        "estudo": [
            f"Com 1 inicialização, o ARI médio fica entre {comma(min(v['ari_1'] for v in pk.values()), 2)} e "
            f"{comma(max(v['ari_1'] for v in pk.values()), 2)} para k de 2 a 10.",
            f"Tempo por ajuste (k = 6, mediana, um núcleo): {comma(k6['tempo_s'], 2)} s com 10 inicializações, "
            f"{comma(k6['tempo_1_s'], 2)} s com uma.",
            f"Estudo inteiro: {d['estudo_total_ajustes']} ajustes (9 k × 10 seeds, com 10 inicializações e com uma), "
            "cerca de 4 minutos.",
        ],
        "perguntas": [
            ("Então basta aumentar o número de inicializações?",
             "Até certo ponto: 10 já bastam para que as seeds concordem nos k estáveis. Nos k instáveis (3 e 9), o "
             "problema é a falta de fronteira nos dados, e mais inicializações não resolvem."),
        ],
    })

    # 10 -----------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:40",
        "fala": "Juntando tudo, escolhemos k igual a 6. O cotovelo da inércia fica entre 5 e 6; silhueta e "
                "Davies-Bouldin estão planas, então não desempatam; a estabilidade é quase perfeita, com ARI de "
                f"{comma(k6['ari'], 3)}; e, como dois grupos ficam com o capital, k igual a 6 deixa quatro grupos para "
                "quem não tem capital, com perfis bem distintos.",
        "estudo": [
            f"k = 5 (ARI {comma(k5['ari'], 3)}): só três grupos sem capital; junta os mais velhos sem cônjuge com os "
            "casados em ofícios manuais.",
            f"k = 8 (ARI {comma(k8['ari'], 3)}): seis grupos sem capital, alguns difíceis de distinguir (por exemplo, "
            "jovens de meio período e quem trabalha 66 h por semana).",
            "A escolha do k combina métricas e interpretação: não existe um k ‘correto’ em agrupamento.",
            f"Partição descrita: seed 42, fora das seeds 0 a 9; coincide com as 10 seeds (ARI de 0,977 a 0,999).",
        ],
        "perguntas": [
            ("Por que não k = 2, que tem a melhor silhueta?",
             "Porque k = 2 só separa quem tem ganho de capital. É a divisão mais nítida, mas descreve 8% das pessoas "
             "e deixa as outras 92% num grupo só."),
        ],
    })

    # 11 -----------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:45",
        "fala": "Obrigado, Paulo. Estes são os seis grupos, numerados do menor para o maior percentual de renda alta. "
                f"Os jovens solteiros, com {comma(g[1]['idade'], 0)} anos em média, muitos morando com os pais. Os mais "
                f"velhos sem cônjuge, com {comma(g[2]['idade'], 0)} anos, divorciados e viúvos. Os casados em ofícios "
                f"manuais, que trabalham {comma(g[3]['horas'], 0)} horas por semana. Os profissionais com muito estudo, "
                f"{comma(g[4]['estudo'], 1)} anos em média. E os dois grupos do capital, perda e ganho. Os quatro "
                "primeiros se separam pela fase da vida e pelo tipo de trabalho; os dois últimos, pelo capital.",
        "estudo": [
            f"Grupo 1: {thousands(g[1]['pessoas'])} pessoas; {g[1]['estado_civil']}; {g[1]['relacionamento']}; "
            f"{comma(g[1]['horas'], 0)} h/semana.",
            f"Grupo 2: {thousands(g[2]['pessoas'])}; {comma(g[2]['estudo'])} anos de estudo; casados só 37%, "
            "divorciados 34%, viúvos 11%.",
            f"Grupo 3: {thousands(g[3]['pessoas'])}; {g[3]['estado_civil']}; {g[3]['relacionamento']}; "
            f"{g[3]['ocupacao']}.",
            f"Grupo 4: {thousands(g[4]['pessoas'])}; {g[4]['ocupacao']}, mais 25% de gerentes; "
            f"{comma(g[4]['horas'], 0)} h/semana.",
            f"Grupo 5: {thousands(g[5]['pessoas'])}; todos com perda de capital (média de "
            f"{thousands(round(g[5]['perda']))} dólares).",
            f"Grupo 6: {thousands(g[6]['pessoas'])}; todos com ganho de capital (média de "
            f"{thousands(round(g[6]['ganho']))} dólares).",
            "Os nomes são nossos, tirados do perfil; o K-means só devolve números.",
        ],
        "perguntas": [
            ("Os nomes dos grupos vêm do algoritmo?",
             "Não. O K-means devolve só um número por pessoa. Os nomes resumem o perfil médio de cada grupo, e há "
             "pessoas diferentes desse perfil dentro dele."),
        ],
    })

    # 12 -----------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:35",
        "fala": "Só agora olhamos a renda. O K-means nunca a viu, e mesmo assim os grupos se ordenam por ela: "
                f"{comma(g[1]['positivos'])}% dos jovens solteiros ganham mais de 50 mil, contra "
                f"{comma(g[4]['positivos'])}% dos profissionais com muito estudo e {comma(g[6]['positivos'])}% de quem "
                f"tem ganho de capital. Na base inteira, são {comma(b['positivos'])}%. Os atributos que formam os "
                "grupos, como idade, estudo, estado civil e capital, são os mesmos que explicam a renda.",
        "estudo": [
            "% acima de 50 mil por grupo: " + "; ".join(f"{i}: {comma(g[i]['positivos'])}%" for i in range(1, 7)) + ".",
            "A ordem dos números dos grupos foi feita depois, pelo % de renda alta, só para facilitar a leitura.",
        ],
        "perguntas": [
            ("Se a renda não entrou, como os grupos ficaram ordenados por ela?",
             "Porque a renda depende dos mesmos atributos que definem os grupos: idade, estudo, estado civil, "
             "ocupação e capital. Pessoas parecidas nesses atributos tendem a ter rendas parecidas."),
        ],
    })

    # 13 -----------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:45",
        "fala": "Mas os grupos descrevem, não preveem. Se cada grupo chutasse a renda da sua maioria, acertaria "
                f"{comma(e['pureza'])}% das pessoas; essa é a pureza. Responder ‘até 50 mil’ para todos já acerta "
                f"{comma(e['chute'])}%, só {comma(acima_chute)} pontos a menos, e a SVM acerta "
                f"{comma(ref['svm_rbf_acuracia'])}%. Nenhum grupo é puro: no grupo dos profissionais, a chance de renda "
                "alta é de 45%, quase cara ou coroa. O K-means junta pessoas parecidas em tudo; o classificador aprende "
                "com a renda o que importa para ela.",
        "estudo": [
            "Pureza: cada grupo responde a classe mais comum entre as suas pessoas; é a fração de acertos. Grupos 1 a "
            "4 respondem ‘≤50K’; 5 e 6, ‘>50K’.",
            f"ARI contra a renda: {comma(e['ari_renda'], 2)}, perto do acaso. Com 6 grupos e 2 classes, o ARI não "
            "chegaria a 1 nem com grupos puros, por isso a pureza é a métrica mais fácil de ler.",
            f"Pessoas de renda alta nos grupos 3 e 4, que respondem ‘≤50K’: cerca de 1.800 e 2.600.",
            f"SVM RBF: {comma(ref['svm_rbf_acuracia'])}% de acurácia média no teste (10 seeds), na mesma base.",
        ],
        "perguntas": [
            ("Então o K-means não serve para nada aqui?",
             "Serve para descrever a população: mostra que perfis existem e onde a renda alta se concentra. Para "
             "prever a renda de uma pessoa, um classificador treinado com a renda é muito melhor."),
            ("A pureza e a acurácia são comparáveis?",
             "Aproximadamente: a pureza é a acurácia de um classificador que responde a classe da maioria do grupo, "
             "medida na base inteira. Serve como ordem de grandeza."),
        ],
    })

    # 14 -----------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:35",
        "fala": "Este gráfico projeta as 80 colunas em duas dimensões, as duas direções em que a base mais varia. Os "
                "dois grupos do capital ficam isolados, um em cima e outro embaixo. Os outros quatro se encostam numa "
                "nuvem contínua, dos jovens solteiros, à esquerda, aos profissionais, à direita. Isso explica a "
                f"silhueta baixa. A ressalva é que a projeção mostra só {comma(sum(d['pca']['variancia']), 0)}% da "
                "variação dos dados.",
        "estudo": [
            "PCA (análise de componentes principais): encontra as direções de maior variância e projeta os pontos "
            "nelas. Usada só para desenhar; o K-means agrupou nas 80 colunas.",
            f"Componente 1: {comma(d['pca']['variancia'][0])}% da variância; componente 2: "
            f"{comma(d['pca']['variancia'][1])}%.",
            "Amostra de 1.500 pessoas no slide, para o desenho não virar uma mancha; os centros usam todas.",
        ],
        "perguntas": [
            ("Grupos que se sobrepõem no gráfico não estão errados?",
             "Não necessariamente: o gráfico mostra só duas direções, 33% da variação. Nas outras, os grupos podem "
             "estar separados. Mas a sobreposição combina com a silhueta baixa."),
        ],
    })

    # 15 -----------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:40",
        "fala": "Para concluir. O K-means encontrou seis perfis de pessoas, estáveis entre seeds, que se ordenam pela "
                "renda sem nunca a ter visto. A base não tem grupos nítidos: são regiões de uma nuvem contínua, e o "
                "capital domina a distância, mesmo com logaritmo. Os grupos servem para descrever a população; para "
                "prever a renda, um classificador é muito melhor. E o custo é baixo: menos de um segundo por ajuste, "
                "crescendo linearmente com o número de pessoas. Obrigado; ficamos à disposição para perguntas.",
        "estudo": [
            "Lições: a distância decide tudo (escala, one-hot, log); métricas internas sozinhas não escolhem o k; "
            "estabilidade e interpretação completam a escolha.",
            "Trabalhos futuros: algoritmos para atributos mistos (k-prototypes), capital como ‘tem / não tem’, "
            "mistura de gaussianas, que dá a cada pessoa uma probabilidade de pertencer a cada grupo.",
        ],
        "perguntas": [
            ("O que vocês fariam diferente?",
             "Testaríamos uma distância própria para dados mistos, como no k-prototypes, que trata as categorias sem "
             "one-hot, e o capital como ‘tem / não tem’, para que ele não ocupe dois grupos."),
        ],
    })

    return notes
