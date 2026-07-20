
### 3.4 docs/04-infraestrutura-fisica.md

```markdown
# Parte 4 - Infraestrutura Fisica

## Cabeamento

| Trecho | Tipo | Distancia | Velocidade |
|--------|------|-----------|------------|
| Backbone | Fibra OM4 | Até 50m | 40 Gbps |
| Horizontal | Cat6a | Até 90m | 10 Gbps |
| Patch cord | Cat6a | Até 5m | 10 Gbps |

## Rack (De cima para baixo)

| U | Equipamento | Especificacao |
|---|-------------|---------------|
| 1-2 | Patch Panel 24p | Cat6a, etiquetado |
| 3-4 | Organizacao de cabos | Mangueiras com velcro |
| 5-7 | Switch 48p | Cisco 9300-48U |
| 8-9 | Organizacao de cabos | Mangueiras com velcro |
| 10-11 | Firewall | FortiGate 200F |
| 12-14 | Servidor 1 (Bot) | Dell PowerEdge R660 |
| 15-17 | Servidor 2 (BD) | Dell PowerEdge R660 |
| 18-19 | Organizacao de cabos | Mangueiras com velcro |
| 20-22 | Nobreak Online | 30 min autonomia |

## Requisitos

- **Distancia maxima:** 85 metros (margem de 5m)
- **Refrigeracao:** 5.000 BTU/h
- **Energia:** Nobreak 3.000 VA + gerador