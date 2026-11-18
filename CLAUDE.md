# CLAUDE.md

Trabalhos da disciplina de Aprendizagem de Máquina (PPGCC010, UFPI). Cada família de modelos é estudada numa base própria:

- **`proteinas/`**: base 1, molécula → proteína-alvo (ChEMBL 37, 27.714 moléculas, 4 classes). Árvore de decisão e variações: Random Tree, Random Forest, Gradient Boosting. Concluída.
- **`emprestimos/`**: base 2, cliente → aprovação de empréstimo (Kaggle, 4.269 pedidos, binária). Redes neurais (concluída) e SVM (próxima etapa).
- **`comum/`**: o que os slides das duas bases compartilham (`slides_common.py`, template SBC, `export_slides_pdf.ps1`).

O README explica as bases e os resultados. Este arquivo trata de como trabalhar no código.

## Idioma

Tudo em português: notebooks, código (nomes de funções em `emprestimos/src` estão em português; os de `proteinas/src`, em inglês), relatórios, slides e mensagens de commit. Os dados mantêm os nomes de coluna originais (`loan_status`, `cibil_score`, `Molecular Weight`); a tradução para gráficos e textos fica em `emprestimos/src/config.py` (`NOMES`).

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

As duas bases têm um pacote chamado `src`. Nunca importe as duas no mesmo processo.

## Regras que não são óbvias

- **Números do relatório são gerados.** `report/results/numeros.tex`, `numeros_rn.tex` e as tabelas `tab_*.tex` são escritos pelos scripts (`results_tables.py`, `rn_report.py`). Não edite esses arquivos à mão: mude o script e rode de novo. O texto em `sections/` cita os números por macros (`\accGrupAmbos`, `\rnAccRede`, ...).
- **Slides são gerados.** Os `.pptx` e os roteiros `notas*.md` saem de `build_slides*.py` e dos arquivos `slides_*notes.py`. Para mudar um slide ou nota, edite o script. Regra de acessibilidade: nenhum texto abaixo de 18 pt (`audit_fonts` confere ao final).
- **Dados são byte a byte.** O `.gitattributes` marca `**/data/** -text`, porque o `proteinas/DATASET.md` e `emprestimos/src/config.py` (`RAW_SHA256`) guardam os hashes SHA-256 dos arquivos.
- **Seeds.** Os resultados finais usam 10 seeds (0 a 9). Análises de uma seed só usam 42.
- **Base 1, divisão agrupada.** Moléculas com os mesmos 5 descritores ficam do mesmo lado da divisão (`modeling.descriptor_groups`). A divisão aleatória existe só para medir o vazamento.
- **Base 2, protocolo comum.** Todo modelo novo passa por `emprestimos/src/avaliacao.py`: `rodar_seeds(fabrica, X, y)` faz a divisão estratificada 80/20, a busca com validação cruzada de 5 partes dentro do treino e mede os tempos num único núcleo. `resumir` agrega as seeds. Os resultados ficam em `emprestimos/resultados/` (`referencias.csv`, `rede.csv`), uma linha por seed e modelo.

## Próxima etapa: SVM na base 2

Siga o padrão da rede neural:

- `emprestimos/src/svm.py`: fábrica do modelo (Pipeline com `StandardScaler`, como em `rede.py`) e a grade de hiperparâmetros;
- `emprestimos/notebooks/05_svm.ipynb`: estudo do modelo e comparação com a rede e com os modelos de referência, pelo mesmo protocolo;
- `emprestimos/resultados/svm.csv`: uma linha por seed, com as mesmas colunas de `rede.csv`.

O relatório e os slides da SVM ainda não têm formato definido. Pergunte antes de criá-los.

## Ambiente (Windows)

- `.venv` com Python 3.13 e `requirements.txt`. O `.venv` não tem `python-pptx`; os scripts de slides rodam com o Python do sistema (`python`), que tem.
- PDF dos slides: `powershell -File comum/export_slides_pdf.ps1 <arquivo.pptx>` (exige PowerPoint).
- LaTeX: MiKTeX. Pelo Bash, `latexmk` falha com erro do MiKTeX; compile pelo PowerShell, dentro de `report/`: `pdflatex main`, `bibtex main`, `pdflatex main` duas vezes.
- Para testar um notebook sem alterar o arquivo: `jupyter nbconvert --to notebook --execute <nb> --output-dir <pasta temporária>`, rodado de dentro de `notebooks/`.
