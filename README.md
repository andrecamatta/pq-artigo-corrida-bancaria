# Corrida bancária sem fila — código de apoio

Material de apoio do artigo **"Corrida bancária sem fila: Diamond-Dybvig, liquidez e a regulação que ainda falta"** publicado em [Pílulas de Quant](https://pilulasdequant.com.br).

A peça central é uma simulação do **processo de Hawkes univariado** ilustrando a autoexcitação de saques numa corrida digital, animada como uma fileira de dominós com propagação física: dominós próximos se tocam e empurram o vizinho; quando os eventos se afastam no tempo, os dominós ficam longe entre si e a corrente quebra naturalmente.

## Como reproduzir

Pré-requisitos: Python 3.10+ e as dependências em `requirements.txt`.

```bash
pip install -r requirements.txt
python artigos/_gen_hawkes_dominoes.py
```

Saída: `artigos/hawkes_dominoes.gif` (~1,1 MB, 12 s de animação a 10 fps).

A simulação tem seed fixa (`SEED = 20260504`), então o resultado é determinístico. Os parâmetros do cenário pedagógico estão no topo do script:

| Regime | μ | α | β | α/β |
|---|---|---|---|---|
| Estável (0–8 h) | 2,0 / h | 0,30 | 5,0 / h | 0,06 |
| Cascata (8 h em diante) | 2,0 / h | 1,50 | 2,0 / h | 0,75 |

A transição de regime em t = 8 h injeta um "evento de notícia" (saque grande) que move o sistema para o regime instável. O caixa cruza o piso operacional Bₜ em τ ≈ 9,7 h e zera em t ≈ 10,3 h.

## Estrutura

```
artigos/
├── _gen_hawkes_dominoes.py    Simulação Hawkes + animação dominó (peça central)
├── _gen_diagrama_nash.py      Diagrama dos dois equilíbrios de Nash (Diamond-Dybvig)
├── _gen_tabela_corridas.py    Tabela das quatro corridas históricas sem fila
├── _gen_header.js             Geração do header via OpenRouter (requer API key local)
├── corrida-bancaria-diamond-dybvig-regulacao.html   Artigo completo
├── corrida-bancaria-diamond-dybvig-regulacao_linkedin.md   Chamada para LinkedIn
├── hawkes_dominoes.gif
├── diagrama_nash_pareto_corrida.png
├── tabela_corridas_sem_fila.png
└── corrida-bancaria-diamond-dybvig-regulacao_header.png
```

Os geradores `_gen_diagrama_nash.py` e `_gen_tabela_corridas.py` usam Selenium + Chrome headless para renderizar HTML estilizado em PNG.

## Licença

Código sob [MIT](LICENSE). O texto do artigo e as figuras geradas são de André Camatta, 2026.
