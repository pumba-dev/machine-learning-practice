# CLAUDE.md

Trabalhos da disciplina de Aprendizagem de Máquina (PPGCC010, UFPI). Cada família de modelos é estudada numa base própria:

- **`proteinas/`**: base 1, molécula → proteína-alvo (ChEMBL 37, 27.714 moléculas, 4 classes). Árvore de decisão e variações: Random Tree, Random Forest, Gradient Boosting. Concluída.
- **`emprestimos/`**: base 2, cliente → aprovação de empréstimo (Kaggle, 4.269 pedidos, binária). Redes neurais. Concluída.
- **`renda/`**: base 3, pessoa → renda anual acima de 50 mil dólares ([Adult Census Income](https://www.kaggle.com/datasets/uciml/adult-census-income), censo dos EUA de 1994, 30.139 pessoas após a curadoria, binária). Parte 4: SVM, comparada com a rede neural da base 2; notebooks, slides e relatório concluídos. Parte 5: clusterização com K-means; notebook, slides e relatório concluídos.
- **`comum/`**: o que os slides das bases compartilham (`slides_common.py`, template SBC, `export_slides_pdf.ps1`).

O README explica as bases e os resultados. Este arquivo trata de como trabalhar no código.

## Idioma

Tudo em português: notebooks, código (nomes de funções em `emprestimos/src` estão em português, e `renda/src` segue o mesmo padrão; os de `proteinas/src`, em inglês), relatórios, slides e mensagens de commit. Os dados mantêm os nomes de coluna originais (`loan_status`, `cibil_score`, `Molecular Weight`, `income`); a tradução para gráficos e textos fica no `config.py` de cada base (`NOMES`).

Commits: frase no imperativo em 3ª pessoa, sem prefixo, como "Adiciona curadoria da base de empréstimos" ou "Atualiza o README com ...". Os commits vão direto para o `master`.

## Estrutura de cada base

```
data/raw/, data/processed/   dados brutos e base final
notebooks/                   numerados na ordem de execução; só chamam funções de src/
src/                         pacote `src`, com config.py (caminhos e constantes)
report/                      LaTeX (formato SBC): main.tex, sections/, figures/, results/, main.pdf
scripts/                     geram report/results, report/figures e os slides
slides/                      .pptx, .pdf e roteiros .md
```

Os caminhos são calculados a partir do próprio arquivo, nunca do diretório de trabalho:

- `src/config.py`: `ROOT = Path(__file__).resolve().parent.parent`, a pasta da base;
- notebooks: `ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()` e `sys.path.insert(0, str(ROOT))`;
- scripts: `ROOT = Path(__file__).resolve().parent.parent`; os que montam slides acrescentam `ROOT.parent / "comum"` ao `sys.path`.

Todas as bases têm um pacote chamado `src`. Nunca importe duas delas no mesmo processo; o que uma base precisar de outra, copie.

## Regras que não são óbvias

- **Números do relatório são gerados.** `report/results/numeros.tex`, `numeros_rn.tex` e as tabelas `tab_*.tex` são escritos pelos scripts (`results_tables.py`, `rn_report.py`). Não edite esses arquivos à mão: mude o script e rode de novo. O texto em `sections/` cita os números por macros (`\accGrupAmbos`, `\rnAccRede`, ...).
- **Slides são gerados.** Os `.pptx` e os roteiros `notas*.md` saem de `build_slides*.py` e dos arquivos `slides_*notes.py`. Para mudar um slide ou nota, edite o script. Regra de acessibilidade: nenhum texto abaixo de 18 pt (`audit_fonts` confere ao final).
- **Dados são byte a byte.** O `.gitattributes` marca `**/data/** -text`, porque o `proteinas/DATASET.md` e o `src/config.py` das outras bases (`RAW_SHA256`) guardam os hashes SHA-256 dos arquivos.
- **Seeds.** Os resultados finais usam 10 seeds (0 a 9). Análises de uma seed só usam 42.
- **Base 1, divisão agrupada.** Moléculas com os mesmos 5 descritores ficam do mesmo lado da divisão (`modeling.descriptor_groups`). A divisão aleatória existe só para medir o vazamento.
- **Base 2, protocolo comum.** Todo modelo novo passa por `emprestimos/src/avaliacao.py`: `rodar_seeds(fabrica, X, y)` faz a divisão estratificada 80/20, a busca com validação cruzada de 5 partes dentro do treino e mede os tempos num único núcleo. `resumir` agrega as seeds. Os resultados ficam em `emprestimos/resultados/` (`referencias.csv`, `rede.csv`), uma linha por seed e modelo.
- **Base 3, mesmo protocolo.** `renda/src/avaliacao.py` é uma cópia adaptada do da base 2: `preprocessador()` faz o one-hot dos categóricos e a padronização dos numéricos dentro do `Pipeline` (80 colunas), e `treinar_e_medir` grava também F1 da classe >50K, falsos positivos e negativos, vetores de suporte (SVC) e épocas (rede). Resultados em `renda/resultados/`: `referencias.csv`, `svm.csv`, `rede.csv`, uma linha por seed e modelo; os demais CSVs são do estudo numa seed (`svm_mapa.csv`, `svm_tempo_por_tamanho.csv`) e dos erros por grupo.
- **Base 3, raça e sexo.** `race` e `sex` ficam em `renda.csv`, mas fora de `config.FEATURES`: nenhum modelo os usa. Servem só à análise exploratória e à comparação de erros entre grupos depois da previsão (`carregar_sensiveis`). Na clusterização vale o mesmo: os dois ficam fora dos atributos agrupados.
- **Base 3, notebooks demorados.** O `04_svm_estudo` leva cerca de 45 min, o `05_svm_comparacao` cerca de 2 h e o `06_rede_comparacao` cerca de 20 min. O 06 não treina as SVMs de novo: lê `svm.csv`. Rode em segundo plano.

- **Um relatório por base, e dois na base 3.** Cada base tem o seu `report/`, que trata só dela: `proteinas/report/` (árvores, Random Tree e conjuntos), `emprestimos/report/` (rede neural) e `renda/report/`, com dois documentos: `main.tex` (SVM, parte 4) e `kmeans.tex` (K-means, parte 5). Os dois compartilham `figures/`, `results/` e `refs.bib`; as seções do K-means têm prefixo `km_`. O relatório do K-means cita a SVM só no pré-processamento (o mesmo) e na comparação final (85,4%), e não cita a rede neural. Nenhum relatório cita números, figuras ou seções de outra base; o que uma base precisar de outra (fundamentação, descrição de um modelo), copie para o texto dela. Em `renda/report/`, `numeros_svm.tex`, `tab_svm_*.tex`, `svm_dados.json` e `figures/svm_*.pdf` são gerados por `renda/scripts/svm_data.py` e `svm_report.py`; `numeros_clusters.tex`, `tab_clusters_*.tex`, `clusters_dados.json` e `figures/clusters_*.pdf`, por `clusters_data.py` e `clusters_report.py`. Compile cada documento à parte (`pdflatex kmeans`, `bibtex kmeans`, ...).
- **Base 3, slides.** `renda/scripts/build_slides_svm.py` e `slides_svm_notes.py` montam `renda/slides/apresentacao_svm.pptx` (15 slides, 10 min) a partir de `svm_dados.json`. Raça e sexo ficam fora dos slides por decisão do grupo.
- **Base 3, slides do K-means.** `renda/scripts/clusters_data.py` reúne os números do notebook 07 em `report/results/clusters_dados.json`; `build_slides_clusters.py` e `slides_clusters_notes.py` montam `renda/slides/apresentacao_clusters.pptx` (15 slides, 10 min) e `notas_clusters.md` a partir dele. Os nomes dos 6 grupos ficam em `clusters_data.py` (`NOMES_GRUPOS`), conferidos pelo tamanho de cada grupo. Nos gráficos de linha, os valores são multiplicados por 10 ou 100 e o formato põe uma vírgula literal, para a vírgula decimal não depender do idioma do Office. Raça e sexo ficam fora.

## Próxima etapa: clusterização na base 3

A parte 5 estuda aprendizado não supervisionado na mesma base de renda, só com o K-means (o professor pediu K-means; o agrupamento hierárquico ficou de fora por decisão do grupo). Só scikit-learn, sem dependência nova. Siga o formato da SVM:

- `renda/src/clusters.py`: pré-processamento, fábrica do K-means, métricas e perfil dos grupos. O pré-processamento parte do de `avaliacao.preprocessador()` (80 colunas);
- notebook `07_kmeans.ipynb`, que só chama funções de `src/`;
- resultados em `renda/resultados/` com prefixo `clusters_`.

Protocolo:

- não há divisão treino/teste: os grupos são formados na base inteira, só com `config.FEATURES`. `income`, `race` e `sex` entram só depois, para comparar (raça e sexo no relatório, nunca nos slides);
- métricas internas para k de 2 a 10: inércia (cotovelo), silhueta e Davies-Bouldin, cada uma nas 10 seeds (média e desvio);
- estabilidade nas 10 seeds para cada k (ARI entre as partições de seeds diferentes), comparada com `n_init=1`;
- a partição descrita (perfis, comparação com a renda, PCA) é a da seed 42, fora das seeds 0 a 9;
- comparação com a renda: proporção de `>50K` em cada grupo, pureza e ARI contra `income`;
- perfil de cada grupo pelos atributos, com os nomes de `config.NOMES`.

Decisões de pré-processamento:

- one-hot sem reescala: cada atributo de texto custa 2 na distância ao quadrado quando difere, e os categóricos respondem por cerca de 37% da distância média entre duas pessoas;
- log (`log1p`) em `capital.gain` e `capital.loss` antes da padronização: sem ele, o ganho de 99.999 fica a 13,3 desvios da média e tende a formar um grupo próprio; o notebook mostra a diferença;
- a silhueta em 30 mil pontos é de ordem n²: use `sample_size` com seed fixa.

Relatório e slides:

- relatório: novas seções em `renda/report/sections/`; título e resumo do `main.tex` serão revistos para cobrir as duas partes. Números em `report/results/numeros_clusters.tex` e figuras em `report/figures/clusters_*.pdf`, gerados por `renda/scripts/clusters_data.py` e `clusters_report.py`;
- slides: `renda/scripts/build_slides_clusters.py` e `slides_clusters_notes.py` montam `renda/slides/apresentacao_clusters.pptx` e `notas_clusters.md`, com a mesma regra de 18 pt. Pergunte a duração e o número de slides antes de criá-los.

## Ambiente (Windows)

- `.venv` com Python 3.13 e `requirements.txt`. O `.venv` não tem `python-pptx`; os scripts de slides rodam com o Python do sistema (`python`), que tem.
- PDF dos slides: `powershell -File comum/export_slides_pdf.ps1 <arquivo.pptx>` (exige PowerPoint).
- LaTeX: MiKTeX. Pelo Bash, `latexmk` falha com erro do MiKTeX; compile pelo PowerShell, dentro de `report/`: `pdflatex main`, `bibtex main`, `pdflatex main` duas vezes. Na máquina do Thiago, o MiKTeX está em `%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64` (instalação por usuário).
- Sem PowerPoint instalado, o PDF dos slides pode ser exportado pelo PowerPoint online.
- Para testar um notebook sem alterar o arquivo: `jupyter nbconvert --to notebook --execute <nb> --output-dir <pasta temporária>`, rodado de dentro de `notebooks/`.
