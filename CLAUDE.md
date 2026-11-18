# CLAUDE.md

Trabalhos da disciplina de Aprendizagem de Máquina (PPGCC010, UFPI). Cada família de modelos é estudada numa base própria:

- **`proteinas/`**: base 1, molécula → proteína-alvo (ChEMBL 37, 27.714 moléculas, 4 classes). Árvore de decisão e variações: Random Tree, Random Forest, Gradient Boosting. Concluída.
- **`emprestimos/`**: base 2, cliente → aprovação de empréstimo (Kaggle, 4.269 pedidos, binária). Redes neurais. Concluída.
- **`renda/`**: base 3, pessoa → renda anual acima de 50 mil dólares ([Adult Census Income](https://www.kaggle.com/datasets/uciml/adult-census-income), censo dos EUA de 1994, 32.561 pessoas, binária). SVM. Próxima etapa.
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

## Próxima etapa: SVM na base 3

A SVM é estudada numa base nova, não na de empréstimos. Siga o formato de `emprestimos/`:

- `renda/` com a mesma estrutura das outras bases; CSV do Kaggle em `renda/data/raw/adult.csv`, conferido por `RAW_SHA256` em `renda/src/config.py`;
- notebooks na ordem: curadoria (feita), análise exploratória, pontos de referência e SVM;
- protocolo de avaliação como o de `emprestimos/src/avaliacao.py` (copiado para `renda/src/`, já que os pacotes `src` não se misturam): 10 seeds, divisão estratificada 80/20, busca com validação cruzada de 5 partes no treino, tempo num único núcleo;
- resultados em `renda/resultados/`, uma linha por seed e modelo.

Decisões da curadoria (`renda/notebooks/01_curadoria.ipynb`):

- os `?` de `workclass`, `occupation` e `native.country` viram células vazias em `renda.csv`, e as linhas ficam (a ausência se relaciona com o alvo). O tratamento do vazio (por exemplo, uma categoria "ausente") fica no `Pipeline` de cada modelo;
- as 24 linhas repetidas saem; a base processada tem 32.537 pessoas;
- `education` (texto de `education.num`) e `fnlwgt` (peso amostral do censo) ficam na base, mas fora dos modelos (`config.FORA`). Os modelos usam `config.FEATURES`: 5 numéricos (`config.NUMERICOS`) e 7 categóricos (`config.CATEGORICOS`);
- o alvo `income` vira 1 para renda acima de 50 mil (24,1%).

O que ainda precisa de decisão:

- atributos categóricos, que a SVM só aceita depois de codificados (one-hot dentro do `Pipeline`, com a padronização dos numéricos);
- ganho e perda de capital, zerados para mais de 90% das pessoas e muito assimétricos, o que pesa na padronização;
- classes desbalanceadas, o que pede F1 macro e AUC além da acurácia;
- tamanho: com cerca de 26 mil pessoas no treino, o `SVC` com kernel é lento (o custo cresce mais que linearmente com o número de exemplos); a busca precisa caber no tempo.

O relatório e os slides da SVM ainda não têm formato definido. Pergunte antes de criá-los.

## Ambiente (Windows)

- `.venv` com Python 3.13 e `requirements.txt`. O `.venv` não tem `python-pptx`; os scripts de slides rodam com o Python do sistema (`python`), que tem.
- PDF dos slides: `powershell -File comum/export_slides_pdf.ps1 <arquivo.pptx>` (exige PowerPoint).
- LaTeX: MiKTeX. Pelo Bash, `latexmk` falha com erro do MiKTeX; compile pelo PowerShell, dentro de `report/`: `pdflatex main`, `bibtex main`, `pdflatex main` duas vezes.
- Para testar um notebook sem alterar o arquivo: `jupyter nbconvert --to notebook --execute <nb> --output-dir <pasta temporária>`, rodado de dentro de `notebooks/`.
