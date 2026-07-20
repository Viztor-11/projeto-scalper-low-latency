# Parte 3 - Estrategias de Reducao de Latencia

## REST vs WebSocket

| Aspecto | REST | WebSocket | Ganho |
|---------|------|-----------|-------|
| Conexao | Nova a cada req | **Persistente** | Elimina handshake |
| Overhead | TCP + TLS por req | **Uma vez so** | ~50-100ms |
| Latencia | 50-200ms | **1-10ms** | 10-20x mais rapido |
| Push de dados | Nao (polling) | **Sim** | Dados imediatos |

## Cache Local

| Dado | TTL | Justificativa |
|------|-----|---------------|
| Saldo | 5 segundos | Atualizacoes frequentes |
| RSI | 1 minuto | Dados historicos |
| Ordens abertas | 2 segundos | Mudancas rapidas |
| Preco | WebSocket | Dado mais critico |

## Paralelismo

```python
# asyncio - Executa multiplas consultas em paralelo
async def get_market_data(session, symbols):
    tasks = []
    for symbol in symbols:
        tasks.append(session.get(f"url/{symbol}"))
    responses = await asyncio.gather(*tasks)
    return responses

    