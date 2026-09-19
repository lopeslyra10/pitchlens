# ADR-0006: BoT-SORT para rastrear e cor do uniforme para separar os times

- **Status:** aceito
- **Data:** 2026-09-18
- **Fase:** 2

## Contexto

Depois da detecção, cada jogador precisa de um identificador que se mantenha ao longo do vídeo
e de um time. Os vídeos disponíveis (ADR-0004) têm câmera em movimento, e nenhum deles tem
rótulos de identidade ou de time.

A primeira versão usava o `sv.ByteTrack` do supervision, com as detecções filtradas em 0,35 de
confiança, e um k-means simples com dois grupos sobre a cor do uniforme. No clipe de teste,
ela criou 329 identificadores para cerca de 11 jogadoras visíveis e colocou árbitras e
reservas num dos dois times. Além disso, o `sv.ByteTrack` está obsoleto e será removido na
versão 0.31 do supervision.

## Decisão

1. **Rastreamento com o BoT-SORT do pacote [`trackers`](https://github.com/roboflow/trackers)**
   (Apache 2.0), alimentado com as detecções a partir de **0,1 de confiança**. A calibração
   dos times usa só detecções acima de 0,5, e a bola, a mais confiável acima de 0,3.
2. **Separação de times pela cor mediana do tronco**, ignorando os pixels de gramado, com:
   - **ajuste robusto**: depois do k-means, as cores mais distantes de cada time são
     descartadas e o centro é recalculado;
   - **rejeição**: cores fora do raio ampliado dos dois times ficam sem time;
   - **voto por identificador**: o time de cada jogador é o mais votado ao longo do tempo.
3. **Goleiros** entram no time cujo centro está mais perto; **arbitragem** fica fora dos times.

## Resultados que sustentam a decisão

Clipe `u17-nz-can-25` (45 s, câmera na mão), mesmo detector e mesmas detecções:

| Configuração | Identificadores | Duração mediana | Rastros < 1 s |
| --- | --- | --- | --- |
| `sv.ByteTrack`, limiar 0,35 | 329 | 0,5 s | 67% |
| ByteTrack (`trackers`), limiar 0,1 | 86 | 3,5 s | 23% |
| **BoT-SORT (`trackers`), limiar 0,1** | **78** | **3,8 s** | 28% |

Na conferência de 111 recortes, as trocas de time caíram de 9 para 0 com o ajuste robusto e a
rejeição (ver o [relatório](../../reports/fase-2/README.md)).

## Alternativas consideradas

| Alternativa | Por que não |
| --- | --- |
| Manter o `sv.ByteTrack` | Obsoleto e sem compensação de movimento de câmera |
| ByteTrack do `trackers` | Resultado próximo, mas cria mais identificadores com a câmera em movimento. Continua disponível com `--tracker bytetrack` |
| Embeddings visuais (SigLIP) + UMAP + k-means para os times | Mais pesado e com mais dependências. A cor resolveu o clipe de teste sem nenhuma troca; fica como evolução para uniformes parecidos |
| Rotular times à mão | Não escala para vídeos novos e contraria o objetivo de funcionar sem rótulos |

## Consequências

- **Reidentificação ainda não existe.** Um jogador que sai do quadro volta com outro número.
  Com câmera fixa (gravação própria) isso acontece bem menos; se continuar relevante, a
  reidentificação por aparência entra numa fase futura.
- **Uniformes verdes** são confundidos com o gramado e ficam sem time. Uniformes de cores
  parecidas entre si também seriam um problema para o método de cor.
- **Parâmetros ajustados num único clipe.** A gravação própria (issue #15) será a validação
  independente.
- **O rastreamento acontece em pixels.** Com a homografia da Fase 3, as posições passam a ser
  em metros, e a atribuição de goleiros pode usar a posição real no campo.
