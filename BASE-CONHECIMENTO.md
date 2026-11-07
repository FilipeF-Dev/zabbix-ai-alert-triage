# Base de conhecimento — EXEMPLO FICTÍCIO

> Este arquivo vai junto com cada alerta para o modelo (em cache, então custa
> pouco). **Troque tudo por informações do seu ambiente.** Os nomes abaixo são
> inventados. **Nunca coloque senha, token, nome de pessoa ou dado de cliente.**

## 1. A empresa e a TI

- Empresa com duas unidades: **Matriz** e **Filial**, ligadas por um túnel VPN
- A TI é uma equipe enxuta, **sem plantão**. O alerta chega por e-mail e é lido
  quando dá. Por isso a análise precisa dizer o que conferir **primeiro**

## 2. Rede

| Faixa | O que é |
|---|---|
| `10.1.0.0/24` | Matriz, servidores e estações |
| `10.2.0.0/24` | Filial |
| `10.9.9.0/30` | túnel Matriz ↔ Filial |

- Roteador da Matriz com 2 links de internet e failover: a queda de um link não
  derruba a empresa
- Quando o túnel cai, a Filial fica sem ERP, arquivos e login

## 3. Servidores

| Host | Papel | Pontos fracos conhecidos |
|---|---|---|
| **SRV-HV01** | host de virtualização (hospeda o DC e o Zabbix) | hardware antigo; **crítico: não sugerir reiniciar como primeiro passo** |
| **SRV-DC01** | controlador de domínio principal (VM no SRV-HV01) | **crítico** |
| **SRV-FILES01** | arquivos e backup em discos USB revezados | os discos USB mudam de letra quando trocados |
| **SRV-ERP01** | banco do ERP | |
| **SRV-BRANCH01** | DC da Filial, visto pelo túnel | é um desktop, não um servidor de verdade |

## 4. Energia

- Nobreak com ~15 minutos de autonomia, **sem desligamento gerenciado**
- Vários hosts reiniciando juntos = suspeitar de energia primeiro

## 5. Backup

| Rotina | Onde | Situação conhecida |
|---|---|---|
| cópia noturna | SRV-FILES01 → disco USB | falha às vezes; só é novidade se o log parar |

## 6. Monitoramento e problemas conhecidos

- Problemas **conhecidos e permanentes** (não são novidade): memória alta no
  SRV-HV01, agente de inventário parado no SRV-FILES01
- O alerta do SRV-BRANCH01 depende do alerta do túnel: se o túnel caiu, só o do
  túnel aparece

## 6a. Guia por tipo de alerta

| Alerta | Causa mais provável aqui | Conferir primeiro |
|---|---|---|
| **Vários hosts fora ou reiniciados juntos** | queda de energia | se a Matriz tem energia; uptime do roteador; depois cada servidor |
| **Túnel da Filial indisponível** | link da Filial ou manutenção local | se o roteador da Matriz vê o túnel; ligar para a Filial |
| **Agente do Zabbix indisponível** (um host, ping ok) | serviço do agente parou ou firewall 10050 | serviço do agente no host |
| **Host reiniciado** (um só) | Windows Update ou travamento | Visualizador de Eventos, IDs 41/1074/6008 |
| **Disco com pouco espaço** | arquivos crescendo ou disco USB trocado | o que cresceu desde a última medição; **não apagar nada sem aprovação** |
| **Os serviços do antivírus parados juntos** | atualização do antivírus; voltam em 4 a 15 min | só é problema se não voltarem em ~20 min |

Regra geral: **um alerta só** num host costuma ser do host; **vários juntos**
costuma ser energia, rede ou o host de virtualização.

## 7. Onde está a documentação (para citar na resposta)

| Assunto | Documento |
|---|---|
| Servidores | `inventario/servidores.md` |
| Rede | `rede/roteador.md` |
