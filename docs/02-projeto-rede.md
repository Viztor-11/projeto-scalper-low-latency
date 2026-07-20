# Parte 2 - Projeto da Rede

## Link de Internet

**Escolha: Link Dedicado com SLA + Link de Backup**

| Criterio | Fibra Corporativa | Link Dedicado | MPLS |
|----------|-------------------|---------------|------|
| Latencia | 10-20ms | 2-5ms | 5-10ms |
| Jitter | 2-5ms | <0,5ms | <1ms |
| SLA | 99,9% | 99,99% | 99,95% |
| Custo | R$ 5.000 | R$ 25.000 | R$ 15.000 |

**Configuracao:**
- Link principal: Fibra dedicada 1 Gbps, latencia < 5ms
- Link secundario: Fibra corporativa 500 Mbps (failover)

## Equipamentos

| Equipamento | Modelo | Justificativa |
|-------------|--------|---------------|
| Switch Core | Cisco Catalyst 9300-48U | QoS avancado, <1µs switching |
| Firewall | FortiGate 200F | Stateful, QoS, baixa latencia |
| Switch Distribuicao | Cisco 9200L-48P | PoE+, VLANs |

## Topologia
BINANCE (Cloud)
|
RTT ~ 3-5ms
|
Link Dedicado 1 Gbps
|
Roteador/Firewall FortiGate
|
Switch Core <1µs
| | |
VLAN 10 VLAN 20 VLAN 30
Admin 40 PCs Bot Servers

## VLANs

| VLAN | ID | Dispositivos | Prioridade QoS |
|------|----|--------------|----------------|
| Administrativa | 10 | 40 computadores | Baixa |
| Operacoes | 20 | Servidores do bot | **Maxima** |
| Servidores | 30 | BD, logs, backup | Media |