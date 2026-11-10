"""Roteiro e material de estudo da terceira apresentação (rede neural na base de empréstimos).

Mesmo formato de slides_rt_notes.py: para cada slide, `tempo` e `fala` (o que dizer), `estudo` (apoio para
quem apresenta; não faz parte da fala) e `perguntas` (perguntas prováveis, com resposta curta).

Os números saem de report/results/rn_dados.json, gerado por rn_data.py com as mesmas funções dos
notebooks da pasta emprestimos/.
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
    base, ms, s42, pad = d["base"], d["multiseed"], d["seed42"], d["padronizacao"]
    m, c, r = ms["modelos"], ms["comparacoes"], ms["rede"]
    acc = {nome: comma(info["acuracia"]) for nome, info in m.items()}
    sd = {nome: comma(info["desvio"]) for nome, info in m.items()}
    paradas = {(p["taxa"], p["paciencia"]): p for p in s42["epocas"]["paradas"]}
    lenta10, lenta30 = paradas[(0.001, 10)], paradas[(0.001, 30)]
    rapida10, rapida30 = paradas[(0.01, 10)], paradas[(0.01, 30)]
    neur = s42["neuronios"]
    erros = s42["erros"]
    rede_f, arv_f = erros["rede neural"]["por_faixa"], erros["árvore de decisão"]["por_faixa"]
    razao_treino = m["rede neural"]["treino_ms"] / m["árvore de decisão"]["treino_ms"]
    razao_busca = m["rede neural"]["busca_s"] / m["árvore de decisão"]["busca_s"]

    notes = []

    # 1 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:20",
        "fala": "Bom dia, professor e colegas. Eu sou o Thiago e, com o Paulo e o Bernan, vou apresentar a terceira "
                "parte do trabalho. A base mudou: em vez de moléculas, pedidos de empréstimo. E o modelo também: "
                "agora é uma rede neural, que comparamos com a árvore de decisão e com modelos mais simples, "
                "inclusive no tempo de execução.",
        "estudo": [
            "Disciplina: PPGCC010 – Aprendizagem de Máquina (UFPI, 2026.2), Prof. Vinicius Ponte Machado.",
            "Tudo no relatório atualizado (Seção 7) e nos notebooks 01 a 04 da pasta emprestimos/ do repositório.",
            "Biblioteca: scikit-learn (MLPClassifier), a mesma das partes anteriores.",
        ],
        "perguntas": [
            ("Por que scikit-learn e não PyTorch ou TensorFlow?",
             "A base é pequena e tabular, e a rede tem poucas camadas. O MLPClassifier do scikit-learn basta e permite "
             "usar o mesmo protocolo (divisão, validação cruzada, busca em grade) dos outros modelos."),
        ],
    })

    # 2 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:55",
        "fala": f"A base vem do Kaggle: {thousands(base['linhas'])} pedidos de empréstimo, cada um com "
                f"{base['atributos']} atributos. Há dados de quem pede, como dependentes, escolaridade e se é "
                f"autônomo; de dinheiro, como renda, valor pedido e quatro tipos de patrimônio; o prazo; e o score de "
                f"crédito, de 300 a 900. O rótulo diz se o pedido foi aprovado: {comma(base['aprovados'])}% foram. "
                f"Então responder sempre ‘aprovado’ já acerta {comma(base['aprovados'])}%, e esse é o piso. A "
                f"curadoria foi curta: não há valores ausentes nem linhas repetidas. O único problema foram "
                f"{base['negativos_residencial']} pedidos com patrimônio residencial negativo, que trocamos por zero.",
        "estudo": [
            "Kaggle: ‘Loan-Approval-Prediction-Dataset’, de architsharma01 (versão 1, 2023, licença MIT). O arquivo "
            "é conferido pelo hash SHA-256 no notebook 01.",
            f"Os {base['negativos_residencial']} negativos eram todos −100.000. A aprovação nessas linhas (57%) é "
            f"parecida com a geral ({comma(base['aprovados'])}%), então parece erro de digitação; mantivemos as "
            "linhas e trocamos o valor por 0, que já aparece em outros 45 pedidos.",
            "Nomes e textos vinham com espaço no início (‘ Approved’); removemos. Os textos viraram 0/1 "
            "(Graduate = 1, Yes = 1, Approved = 1).",
            "A página não diz a moeda. O score é do CIBIL, o birô de crédito da Índia, então devem ser rúpias. Para "
            "os modelos, a moeda não importa.",
            f"Base provavelmente sintética: score e renda quase uniformes (quartis do score "
            f"{', '.join(str(int(q)) for q in base['score_quartis'])}, contra 450, 600 e 750 de uma uniforme de 300 "
            "a 900); escolaridade e autônomo quase 50/50.",
        ],
        "perguntas": [
            ("Por que não apagar as linhas com valor negativo?",
             "Porque o resto da linha parece normal e a taxa de aprovação delas é parecida com a geral. Trocar só o "
             "valor impossível preserva os outros 10 atributos e o rótulo."),
            ("A base é real?",
             "Provavelmente não: as distribuições são quase uniformes e o rótulo segue uma regra quase exata, como "
             "mostra o próximo slide. Isso limita o alcance das conclusões, e o relatório discute isso."),
        ],
    })

    # 3 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:05",
        "fala": f"A análise exploratória mostrou que um atributo decide quase tudo: o score de crédito. O gráfico mostra "
                f"a taxa de aprovação por faixa de score. Abaixo de 550, só cerca de {comma(base['aprovacao_abaixo_550'], 0)}% "
                f"dos pedidos são aprovados; a partir de 550, praticamente todos. Não é uma rampa, é um degrau. A regra "
                f"‘aprovar se o score for pelo menos 550’ acerta {comma(base['regra_550_base'])}% da base. E os poucos "
                f"aprovados abaixo de 550 têm todos prazo curto, de 2 ou 4 anos. Ou seja, os rótulos seguem quase uma "
                f"regra explícita. Isso vai ser importante para entender o resultado da rede.",
        "estudo": [
            f"Correlação com a aprovação: score {comma(base['corr_score_alvo'], 2)}; prazo "
            f"{signed(base['corr_prazo_alvo'], 2)}; os outros nove atributos perto de zero.",
            f"Renda × valor do empréstimo: {comma(base['corr_renda_valor'], 2)}; renda × bens de luxo: "
            f"{comma(base['corr_renda_luxo'], 2)}. Os valores em dinheiro são redundantes entre si.",
            f"Abaixo de 550: aprovação de {comma(base['aprovacao_abaixo_550_por_prazo']['2'], 0)}% com prazo de 2 anos, "
            f"{comma(base['aprovacao_abaixo_550_por_prazo']['4'], 0)}% com 4 anos e 0% com 6 anos ou mais.",
            "Nos modelos, a ‘regra de um corte’ é uma árvore de profundidade 1: ela escolhe sozinha o atributo e o "
            "limiar no treino. Escolheu o score e 549,5 nas 10 seeds, sem olhar o teste.",
        ],
        "perguntas": [
            ("Se uma regra já acerta 95%, para que um modelo?",
             "Para medir se o modelo descobre a regra e a exceção dos prazos curtos sozinho. A regra de um corte é "
             "a régua mínima: um modelo que fique abaixo dela não aprendeu nada útil."),
            ("O 550 não foi escolhido olhando o teste?",
             "Não. Nos modelos, o limiar é aprendido só com o treino de cada seed (deu 549,5 em todas). O 550 deste "
             "slide é da análise exploratória, para descrever a base."),
        ],
    })

    # 4 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:10",
        "fala": "Antes do resultado, como funciona a rede. Cada neurônio faz uma conta simples: multiplica cada "
                "entrada por um peso, soma tudo e passa o resultado por uma função de ativação. Nas camadas ocultas, "
                "usamos a ReLU, que deixa passar os positivos e zera os negativos. Na saída, um neurônio com sigmoide "
                "dá um número entre 0 e 1: a probabilidade de aprovação. Se for acima de 50%, a rede diz ‘aprovado’. "
                "Os pesos começam sorteados. No treino, a rede vê os pedidos, mede o erro e ajusta cada peso um "
                "pouco na direção que reduz o erro. Uma passada completa por todo o treino é uma época. Um detalhe: "
                "uma rede com um único neurônio sigmoide é exatamente a regressão logística, que também comparamos.",
        "estudo": [
            "Neurônio: z = w1·x1 + … + w11·x11 + b; saída = ativação(z). ReLU(z) = max(0, z). Sigmoide(z) = 1/(1 + e^−z).",
            "Perda: entropia cruzada, que pune muito uma probabilidade alta dada à classe errada.",
            "Retropropagação (backpropagation): calcula quanto cada peso contribuiu para o erro, da saída para trás. "
            "Otimizador Adam: ajusta o tamanho do passo de cada peso sozinho. Taxa de aprendizado: o tamanho base do "
            "passo.",
            f"A arquitetura do diagrama (32 e 16 neurônios) foi a mais escolhida pela busca em grade "
            f"({r['arquiteturas'].get('32-16', 0)} das 10 seeds).",
            f"Neurônios (validação cruzada, seed 42): 1 neurônio → {comma(neur['1_camada'][0])}%; 4 numa camada → "
            f"{comma(neur['1_camada'][2])}%; 8 em duas camadas → {comma(neur['2_camada'][3])}%; 64 numa camada → "
            f"{comma(neur['1_camada'][-1])}%. Mais neurônios não ajudam.",
        ],
        "perguntas": [
            ("Por que ReLU e não sigmoide nas camadas ocultas?",
             "A ReLU é simples de calcular e não ‘satura’ para valores positivos, o que facilita o treino. A sigmoide "
             "fica só na saída, onde precisamos de uma probabilidade."),
            ("Quantos pesos tem essa rede?",
             "11×32 + 32 = 384 na primeira camada, 32×16 + 16 = 528 na segunda e 16 + 1 = 17 na saída: 929 no total."),
        ],
    })

    # 5 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:55",
        "fala": f"O primeiro cuidado é a padronização. Os atributos têm escalas muito diferentes: dependentes vão de "
                f"0 a 5, e a renda chega a quase 10 milhões. Sem ajustar isso, a soma de cada neurônio fica dominada "
                f"pelos valores em dinheiro, e o treino não funciona. A mesma rede, nas 10 seeds, acerta "
                f"{comma(pad['sem']['acuracia'])}% sem padronização, abaixo até do piso de "
                f"{comma(base['aprovados'])}%. Com padronização, {comma(pad['com']['acuracia'])}%. Padronizar é, para "
                f"cada atributo, subtrair a média e dividir pelo desvio padrão: todos passam a ficar em torno de "
                f"zero, na mesma escala. E a média e o desvio vêm só do treino, para o teste não vazar.",
        "estudo": [
            f"Sem padronização: {comma(pad['sem']['acuracia'])} ± {comma(pad['sem']['desvio'])}%, AUC "
            f"{comma(pad['sem']['auc'])}% (sorteio = 50%). Com: {comma(pad['com']['acuracia'])} ± "
            f"{comma(pad['com']['desvio'])}%, AUC {comma(pad['com']['auc'])}%. Rede de 16 neurônios, 10 seeds.",
            "Exemplo: renda de 5 milhões, média 5,06 milhões e desvio 2,8 milhões → (5,0 − 5,06) / 2,8 ≈ −0,02. "
            "Dependentes = 4, média 2,5 e desvio 1,7 → (4 − 2,5) / 1,7 ≈ 0,9. Depois disso, os dois são comparáveis.",
            "Por que importa: o passo do otimizador é parecido para todos os pesos; um passo que serve a um atributo "
            "de 0 a 5 é minúsculo para um de 0 a 40 milhões, e vice-versa (LeCun et al., 1998).",
            "No código, a padronização (StandardScaler) fica dentro de um Pipeline com a rede: em cada treino da "
            "validação cruzada, ela é recalculada só com aquele treino.",
            "A árvore não precisa disso: ela só compara cada atributo com um limiar, e mudar a escala não muda a "
            "ordem dos valores.",
        ],
        "perguntas": [
            ("Por que sem padronização fica abaixo do piso, e não no piso?",
             "Porque ela não aprendeu nada útil, e errar mais que o piso é possível quando o modelo prevê ao acaso. "
             "A AUC de 51% confirma: ela não ordena os pedidos melhor que um sorteio. O desvio de 3 pontos entre "
             "seeds também mostra que o resultado é instável."),
            ("Padronizar com a média de toda a base seria errado?",
             "Seria um vazamento pequeno: o teste influenciaria a média. Por isso o Pipeline calcula a média e o "
             "desvio só no treino de cada divisão."),
        ],
    })

    # 6 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:15",
        "fala": f"O segundo cuidado é quando parar o treino. A cada época a rede melhora no treino, mas a partir de um "
                f"ponto passa a decorar o treino, e não a aprender. Por isso usamos parada antecipada: separamos 10% do "
                f"treino como validação e paramos quando a validação passa um certo número de épocas sem melhorar. "
                f"Esse número é a paciência. O gráfico mostra a acurácia de validação de uma rede com duas taxas de "
                f"aprendizado. Com a taxa menor, a rede aprende devagar e fica um tempo parada perto de 92%. Com a "
                f"paciência padrão do scikit-learn, de 10 épocas, o treino pararia na época {lenta10['epoca']}, com "
                f"{comma(lenta10['acuracia'])}%, quando a mesma rede chegaria a {comma(lenta10['melhor'])}%. Por isso "
                f"usamos paciência 30 e colocamos a taxa na busca em grade. A busca escolheu a taxa maior nas "
                f"{r['taxa_001']} seeds.",
        "estudo": [
            "Época: uma passada completa pelos pedidos de treino. Paciência: quantas épocas seguidas sem melhora "
            "(de pelo menos 0,0001) a rede tolera antes de parar.",
            f"Taxa 0,001: paciência 10 → para na época {lenta10['epoca']} ({comma(lenta10['acuracia'])}%); paciência 30 "
            f"→ época {lenta30['epoca']} ({comma(lenta30['acuracia'])}%); melhor das 400 épocas: "
            f"{comma(lenta10['melhor'])}%.",
            f"Taxa 0,01: paciência 10 → época {rapida10['epoca']} ({comma(rapida10['acuracia'])}%); paciência 30 → "
            f"época {rapida30['epoca']} ({comma(rapida30['acuracia'])}%); melhor: {comma(rapida10['melhor'])}%.",
            "A perda de treino continua caindo enquanto a de validação se estabiliza: é o começo do sobreajuste "
            "(overfitting). A figura do relatório (Figura de épocas) mostra as duas perdas.",
            f"Busca em grade: {r['combinacoes']} combinações (6 arquiteturas × 2 regularizações L2 × 2 taxas), "
            f"validação cruzada de 5 partes. Escolheu duas camadas em {r['duas_camadas']} das 10 seeds; a rede final "
            f"treinou de {r['epocas'][0]} a {r['epocas'][2]} épocas.",
        ],
        "perguntas": [
            ("A parada antecipada não desperdiça 10% do treino?",
             "Um pouco, sim: a rede final ajusta os pesos com 90% do treino. Em troca, para sozinha no ponto certo, "
             "sem precisar fixar o número de épocas."),
            ("Por que não treinar sempre 400 épocas?",
             "Depois do melhor ponto a validação cai ou fica parada, e o tempo de treino cresce sem ganho. Na busca "
             "em grade, com 120 redes por seed, isso pesaria muito no tempo."),
        ],
    })

    # 7 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:05",
        "fala": f"Com a rede ajustada, comparamos seis modelos com a mesma régua das partes anteriores: 10 seeds, "
                f"treino e teste estratificados, e busca de hiperparâmetros só dentro do treino. A rede acerta "
                f"{acc['rede neural']}%. Ela supera a regressão logística nas 10 seeds, em "
                f"{comma(c['rede neural × regressão logística']['pontos'])} pontos: as camadas ocultas fazem diferença. "
                f"Mas, contra a regra de um corte, a vantagem é de só {comma(c['rede neural × regra de um corte']['pontos'])} "
                f"ponto, menor que a variação entre seeds. E a árvore de decisão, com {acc['árvore de decisão']}%, "
                f"vence a rede em todas as 10 seeds. A Random Forest empata com a árvore.",
        "estudo": [
            f"Acurácias (10 seeds): classe majoritária {acc['classe majoritária']}%; regressão logística "
            f"{acc['regressão logística']} ± {sd['regressão logística']}%; regra de um corte {acc['regra de um corte']} ± "
            f"{sd['regra de um corte']}%; rede {acc['rede neural']} ± {sd['rede neural']}%; árvore "
            f"{acc['árvore de decisão']} ± {sd['árvore de decisão']}%; Random Forest {acc['random forest']} ± "
            f"{sd['random forest']}%.",
            f"Seed a seed (pontos de acurácia): rede − logística {signed(c['rede neural × regressão logística']['pontos'])} "
            f"(10/10); rede − regra {signed(c['rede neural × regra de um corte']['pontos'])} "
            f"({c['rede neural × regra de um corte']['seeds']}/10, 1 empate); rede − árvore "
            f"{signed(c['rede neural × árvore de decisão']['pontos'])} (0/10); rede − floresta "
            f"{signed(c['rede neural × random forest']['pontos'])} ({c['rede neural × random forest']['seeds']}/10).",
            f"AUC (ordena bem os pedidos?): rede {comma(m['rede neural']['auc'])}%, árvore "
            f"{comma(m['árvore de decisão']['auc'])}%, floresta {comma(m['random forest']['auc'])}%. A rede ordena melhor "
            "que a árvore; o que ela erra é o corte em 50%.",
            f"A rede é a menos estável: desvio de {sd['rede neural']} ponto, quase 3 vezes o da árvore "
            f"({sd['árvore de decisão']}).",
        ],
        "perguntas": [
            ("A diferença para a árvore não é ruído?",
             f"Não: a árvore vence nas 10 seeds, com diferença média de "
             f"{comma(-c['rede neural × árvore de decisão']['pontos'])} ponto e desvio de "
             f"{comma(c['rede neural × árvore de decisão']['desvio'])}. Já contra a regra, a vantagem da rede é menor "
             "que o desvio."),
            ("Como a AUC da rede pode ser maior se ela acerta menos?",
             "A AUC olha a ordem das probabilidades, não o corte. A rede põe quase sempre o aprovado acima do "
             "rejeitado, mas perto do degrau dá probabilidades intermediárias, e o corte em 50% erra alguns."),
        ],
    })

    # 8 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:55",
        "fala": f"Na apresentação anterior, o professor perguntou sobre o tempo de execução. Desta vez medimos: tudo num "
                f"único núcleo, com uma rodada de aquecimento descartada e a mediana das 10 seeds. Treinar a rede "
                f"final leva cerca de {comma(m['rede neural']['treino_ms'] / 1000)} segundo, umas "
                f"{comma(razao_treino, 0)} vezes a árvore, mas menos que a Random Forest. O custo maior está na busca "
                f"de hiperparâmetros: {comma(m['rede neural']['busca_s'], 0)} segundos por seed, contra menos de um "
                f"segundo da árvore. Para prever, a rede e a árvore levam menos de um milissegundo, e a floresta, que "
                f"consulta 300 árvores, uns {comma(m['random forest']['previsao_ms'], 0)}.",
        "estudo": [
            "Máquina: AMD Ryzen 5 9600X (6 núcleos), 31 GB de memória, Windows 11, Python 3.14, scikit-learn 1.9.1.",
            "Um núcleo: n_jobs=1 e threadpool_limits(1), que limita também a álgebra linear do numpy. Assim a "
            "comparação é entre algoritmos, não entre quantos núcleos cada um usa.",
            "Busca medida à parte: depois da busca, o modelo final é treinado de novo com os hiperparâmetros "
            "escolhidos, e só esse treino entra na coluna ‘treino’.",
            f"Busca da rede: {r['combinacoes']} combinações × 5 partes = 120 redes, mais o treino final. Busca da "
            f"árvore: {r['combinacoes_arvore']} combinações × 5 = 150 árvores, ainda assim "
            f"{comma(razao_busca, 0)} vezes mais rápida.",
            "Medianas, e não médias, porque uma medição isolada com o computador ocupado puxaria a média. Os valores "
            "absolutos mudam de máquina para máquina; as razões entre modelos são mais estáveis.",
        ],
        "perguntas": [
            ("Com vários núcleos a rede não ficaria mais rápida?",
             "A busca em grade, sim, porque as combinações são independentes; mas a da árvore também. Por isso "
             "medimos tudo num núcleo: a razão entre os modelos é o que interessa."),
            ("O tempo da rede depende do número de épocas?",
             f"Sim. A rede final treinou de {r['epocas'][0]} a {r['epocas'][2]} épocas, conforme a seed; a parada "
             "antecipada também economiza tempo."),
        ],
    })

    # 9 ------------------------------------------------------------------------------------------
    notes.append({
        "tempo": "1:05",
        "fala": f"Por que a rede perde para a árvore? Os gráficos mostram, para cada pedido de teste, a probabilidade "
                f"de aprovação em função do score. Na árvore, os pontos ficam em 0 ou em 100%, com um salto em 550: "
                f"ela representa o degrau com uma única pergunta. A rede desenha uma rampa: perto de 550 aparecem "
                f"probabilidades intermediárias, e é ali que ela erra. Entre 550 e 599 pontos, a rede erra "
                f"{rede_f[2]} pedidos, e a árvore, {arv_f[2]}. A árvore tem outro ponto fraco: a exceção dos prazos "
                f"curtos abaixo de 550, onde estão {erros['árvore de decisão']['na_excecao']} dos seus "
                f"{erros['árvore de decisão']['total']} erros.",
        "estudo": [
            f"Seed 42, {s42['teste']} pedidos de teste. Erros por faixa de score (< 500 / 500–549 / 550–599 / ≥ 600; "
            f"pedidos {' / '.join(map(str, erros['pedidos']))}): rede {' / '.join(map(str, rede_f))}; árvore "
            f"{' / '.join(map(str, arv_f))}.",
            f"Entre 500 e 599 pontos, {comma(erros['rede_intermediarias_500_600'], 0)}% das probabilidades da rede "
            f"ficam entre 10% e 90%; na árvore, {comma(erros['arvore_intermediarias_500_600'], 0)}%.",
            f"Exceção (score < 550 e prazo ≤ 4 anos): {erros['excecao_pedidos']} pedidos de teste. Erros nela: árvore "
            f"{erros['árvore de decisão']['na_excecao']}, rede {erros['rede neural']['na_excecao']}.",
            "Redes tendem a aprender funções suaves; relações em degrau favorecem árvores em dados tabulares "
            "(Grinsztajn et al., 2022).",
        ],
        "perguntas": [
            ("Mais neurônios ou mais épocas resolveriam a rampa?",
             "Em parte: a rampa pode ficar mais íngreme, mas a curva de neurônios mostrou que mais de 8 não ajuda, e "
             "treinar mais leva a decorar o treino. A árvore resolve com um corte."),
            ("Mudar o corte de 50% ajudaria a rede?",
             "Poderia reduzir alguns erros, já que a AUC é alta, mas o corte teria de ser escolhido na validação, não "
             "no teste. Não fizemos isso para manter o mesmo critério em todos os modelos."),
        ],
    })

    # 10 -----------------------------------------------------------------------------------------
    notes.append({
        "tempo": "0:50",
        "fala": f"Para concluir: a rede neural funciona. Com padronização e parada antecipada, acerta "
                f"{acc['rede neural']}% e supera a regressão logística. Mas, nesta base, não compensa: a árvore acerta "
                f"mais, treina umas {comma(razao_treino, 0)} vezes mais rápido e ainda dá regras legíveis. O motivo é "
                f"a forma da regra que gerou os rótulos, um degrau no score, que a árvore captura com uma pergunta. "
                f"Com dados reais, onde a relação costuma ser mais gradual, a rede poderia se sair melhor. Obrigado; "
                f"ficamos à disposição para perguntas.",
        "estudo": [
            "Lições sobre redes: padronizar sempre; a paciência e a taxa de aprendizado decidem quando a rede para; "
            "poucos neurônios bastam para uma base pequena; a busca de hiperparâmetros é o maior custo.",
            "Limitação principal: base provavelmente sintética; a conclusão vale para ela, não para crédito em geral.",
            "Trabalhos futuros: repetir em dados de crédito reais; separar a variação dos pesos iniciais da variação "
            "da divisão dos dados.",
        ],
        "perguntas": [
            ("Então redes neurais não servem para dados tabulares?",
             "Servem, mas não são a escolha automática. Em bases pequenas e com relações em degrau, árvores e "
             "conjuntos de árvores costumam ganhar. A rede vale mais com muitos dados ou relações suaves e complexas."),
            ("Qual modelo vocês usariam nesta base?",
             f"A árvore de decisão: {acc['árvore de decisão']}%, empatada com a Random Forest, treino de "
             "milissegundos e regras que um analista de crédito consegue ler."),
        ],
    })
    return notes
