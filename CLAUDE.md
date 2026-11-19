# CLAUDE.md

Trabalhos da disciplina de Aprendizagem de Máquina (PPGCC010, UFPI). Cada família de modelos é estudada numa base própria:

- **`proteinas/`**: base 1, molécula → proteína-alvo (ChEMBL 37, 27.714 moléculas, 4 classes). Árvore de decisão e variações: Random Tree, Random Forest, Gradient Boosting. Concluída.
- **`emprestimos/`**: base 2, cliente → aprovação de empréstimo (Kaggle, 4.269 pedidos, binária). Redes neurais. Concluída.
- **`renda/`**: base 3, pessoa → renda anual acima de 50 mil dólares ([Adult Census Income](https://www.kaggle.com/datasets/uciml/adult-census-income), censo dos EUA de 1994, 30.139 pessoas após a curadoria, binária). SVM, comparada com a rede neural da base 2. Notebooks, slides e relatório concluídos.
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
- **Base 3, raça e sexo.** `race` e `sex` ficam em `renda.csv`, mas fora de `config.FEATURES`: nenhum modelo os usa. Servem só à análise exploratória e à comparação de erros entre grupos depois da previsão (`carregar_sensiveis`).
- **Base 3, notebooks demorados.** O `04_svm_estudo` leva cerca de 45 min, o `05_svm_comparacao` cerca de 2 h e o `06_rede_comparacao` cerca de 20 min. O 06 não treina as SVMs de novo: lê `svm.csv`. Rode em segundo plano.

- **O relatório entregue é cumulativo.** Cada atividade acrescenta uma parte ao mesmo documento, sem reescrever as anteriores: título, resumo, introdução, fundamentação, limitações e conclusão só ganham trechos sobre a parte nova. O relatório atual, com as quatro partes, fica em `renda/report/`, partindo da última versão única (commit 5b6d62d), com a SVM na seção 8. `proteinas/report/` e `emprestimos/report/` são versões por base, feitas na reorganização. Em `renda/report/`, só `numeros_svm.tex`, `tab_svm_*.tex`, `svm_dados.json` e `figures/svm_*.pdf` são gerados ali (`renda/scripts/svm_data.py` e `svm_report.py`); os arquivos das partes 1 a 3 são cópias dos gerados em `proteinas/` e `emprestimos/`, e precisam ser copiados de novo se algum deles mudar.
- **Base 3, slides.** `renda/scripts/build_slides_svm.py` e `slides_svm_notes.py` montam `renda/slides/apresentacao_svm.pptx` (15 slides, 10 min) a partir de `svm_dados.json`. Raça e sexo ficam fora dos slides por decisão do grupo.

## Ambiente (Windows)

- `.venv` com Python 3.13 e `requirements.txt`. O `.venv` não tem `python-pptx`; os scripts de slides rodam com o Python do sistema (`python`), que tem.
- PDF dos slides: `powershell -File comum/export_slides_pdf.ps1 <arquivo.pptx>` (exige PowerPoint).
- LaTeX: MiKTeX. Pelo Bash, `latexmk` falha com erro do MiKTeX; compile pelo PowerShell, dentro de `report/`: `pdflatex main`, `bibtex main`, `pdflatex main` duas vezes. Na máquina do Thiago, o MiKTeX está em `%LOCALAPPDATA%\Programs\MiKTeX\miktex\bin\x64` (instalação por usuário).
- Sem PowerPoint instalado, o PDF dos slides pode ser exportado pelo PowerPoint online.
- Para testar um notebook sem alterar o arquivo: `jupyter nbconvert --to notebook --execute <nb> --output-dir <pasta temporária>`, rodado de dentro de `notebooks/`.
