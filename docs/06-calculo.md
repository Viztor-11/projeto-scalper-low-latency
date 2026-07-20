# Parte 6 - Calculo Financeiro

## Parametros

| Parametro | Valor |
|-----------|-------|
| Operacoes por dia | 10.000 |
| Lucro medio por operacao | US$ 0,02 |
| Reducao de latencia | 10 ms |
| Aumento de lucro | 5% |
| Dias uteis por ano | 252 |

## Calculos

Lucro Diario Atual = 10.000 x US0,02=US0,02=US 200,00
Lucro Anual Atual = US200,00x252=US200,00x252=US 50.400,00

Lucro Diario Otimizado = US200,00x1,05=US200,00x1,05=US 210,00
Lucro Anual Otimizado = US$ 210
Ganho Diario Adicional = US$ 10,00
Ganho Anual Adicional = US$ 2.520,00

## ROI para Diferentes Cenarios

### Cenario 1: Infraestrutura Basica (R$ 50.000)

| Item | Custo (R$) |
|------|------------|
| Switch gerenciável | 5.000 |
| Roteador com QoS | 3.000 |
| Cabeamento estruturado | 10.000 |
| Link dedicado (1 ano) | 30.000 |
| **TOTAL** | **R$ 48.000** |


### Cenario 2: Infraestrutura Intermediaria (R$ 500.000)

| Item | Custo (R$) |
|------|------------|
| Switch Core + Distribuicao | 100.000 |
| Firewall/Roteador | 80.000 |
| Servidores (2) | 120.000 |
| Cabeamento + Rack | 50.000 |
| Link dedicado (3 anos) | 150.000 |
| **TOTAL** | **R$ 500.000** |

Payback = R500.000/R500.000/R 12.600
= 39,7 anos


**Conclusao:** Inviavel para este volume de operacoes.

### Cenario 3: Projeto Extremo (R$ 20.000.000)

Para justificar R$ 20 milhoes:

Ganho Anual Necessario = R20.000.000/5anos=R20.000.000/5anos=R 4.000.000/ano
= US$ 800.000/ano

Operacoes Adicionais Necessarias = US800.000/(US800.000/(US 0,02 x 252)
= 158.730 operacoes/dia

Aumento de Lucro Necessario = 158.730 / 10.000
= 15,87x


## Analise de Sensibilidade

| Reducao de Latencia | Aumento de Lucro | ROI (1 ano) | ROI (3 anos) |
|---------------------|------------------|-------------|--------------|
| 5 ms | 2,5% | Nao | Nao |
| 10 ms | 5% | Nao | Baixo |
| 20 ms | 10% | Nao | Medio |
| 50 ms | 25% | Medio | Alto |
| 100 ms | 50% | Alto | Muito Alto |

## Recomendacao Final

Para uma empresa de porte medio (10.000 operacoes/dia):
1. Implementar WebSocket e cache (baixo custo, alto impacto)
2. Link dedicado com SLA (custo medio)
3. **Evitar** investimento em FPGA/colocation (inviavel financeiramente)

Para empresas de grande porte (> 100.000 operacoes/dia):
1. Considerar colocation
2. FPGA para processamento em hardware
3. Infraestrutura de R$ 500.000+ se justifica