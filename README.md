# pq-artigo-corrida-bancaria

Material de apoio do artigo **"Corrida bancária sem fila: Diamond-Dybvig, liquidez e a regulação que ainda falta"** publicado em [Pílulas de Quant](https://pilulasdequant.com.br).

A peça central é uma simulação do **processo de Hawkes univariado** ilustrando a autoexcitação de saques numa corrida digital, animada como uma fileira de dominós com propagação física: dominós espacialmente próximos se tocam e empurram o vizinho; quando os eventos se afastam no tempo, os dominós ficam longe entre si e a corrente quebra naturalmente.

## Como reproduzir

A simulação principal está em Julia. Pré-requisitos: Julia 1.10+ e os pacotes em `Project.toml`.

```bash
julia --project=. -e 'using Pkg; Pkg.instantiate()'
julia --project=. _gen_hawkes_dominoes.jl
```

Saída: `hawkes_dominoes.gif` (~1 MB, 12 s de animação a 10 fps).

A simulação tem seed fixa (`SEED = 20260504`), então o resultado é determinístico. Os parâmetros do cenário pedagógico estão no topo do script:

| Regime | μ | α | β | α/β |
|---|---|---|---|---|
| Estável (0–8 h) | 2,0 / h | 0,30 | 5,0 / h | 0,06 |
| Cascata (8 h em diante) | 2,0 / h | 1,50 | 2,0 / h | 0,75 |

A transição de regime em t = 8 h injeta um "evento de notícia" (saque grande) que move o sistema para o regime instável. O caixa cruza o piso operacional Bₜ em τ ≈ 9,7 h e zera em t ≈ 10,3 h.

## Licença

Código sob [MIT](LICENSE). O texto do artigo e as figuras geradas são de André Camatta, 2026.
