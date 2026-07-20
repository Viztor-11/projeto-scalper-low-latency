# Parte 1 - Diagnostico do Codigo

## Protocolos Utilizados

O robo Python atual utiliza a seguinte pilha de protocolos:

| Camada | Protocolo | Funcao |
|--------|-----------|--------|
| Aplicacao | HTTPS/REST | Requisicoes a API Binance |
| Transporte | TCP | Conexao orientada a conexao |
| Seguranca | TLS 1.2/1.3 | Criptografia e autenticacao |
| Rede | IP | Roteamento de pacotes |
| Resolucao | DNS | Resolucao de nomes para IPs |

**Analise critica:** Cada chamada REST exige um novo handshake TCP + TLS, que adiciona cerca de 50-200ms de latencia por conexao.

## Conexoes por Ciclo

| Cenario | Conexoes | Motivo |
|---------|----------|--------|
| Minimo | 3-4 | Preco + saldo + ordem |
| Medio | 5-7 | Preco + saldo + ordem + RSI + verificacao |
| Maximo | 8-10 | Preco + saldo + ordem + RSI + ordens abertas + retries |

**Calculo de latencia acumulada (cenario medio):**
- 6 conexoes x 100ms = 600ms por ciclo
- Com 10.000 operacoes/dia = 6.000 segundos (~100 minutos) apenas em overhead

## Volume de Trafego

| Operacao | Frequencia | Tamanho | Impacto |
|----------|------------|---------|---------|
| Consulta de preco | A cada ciclo | ~2KB | **Alto** (polling constante) |
| Consulta de saldo | A cada ciclo | ~3KB | Medio |
| Calculo de RSI | A cada ciclo | ~5KB | Medio |
| Envio de ordem | Quando executa | ~1KB | Alto (tempo critico) |

## Candidatos a WebSocket

| Operacao REST | Substituicao por WebSocket | Justificativa |
|---------------|---------------------------|---------------|
| Consulta de preco | **Sim** | Dados em tempo real, elimina polling |
| Consulta de saldo | **Sim** | User Data Stream em tempo real |
| Consulta de ordens abertas | **Sim** | Status em tempo real |
| Envio de ordem | **Parcial** | REST com keep-alive e mais rapido |