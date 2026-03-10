# 🛡️ SOC Agent AI

> 💡 **Inspiração:** A ideia para este projeto surgiu a partir de um vídeo assistido no canal **[The Social Dork](https://www.youtube.com/@thesocialdork1133)** no YouTube. Se você se interessa por cibersegurança e projetos práticos, vale muito a pena conferir!

SOC Agent AI é uma ferramenta de monitoramento de rede desenvolvida em Python para ambientes de Centro de Operações de Segurança (SOC). Ela captura tráfego de rede automaticamente, detecta atividade suspeita e encaminha alertas estruturados para um agente de IA na plataforma **Airia AI**, que realiza a triagem e análise dos eventos.

---

## 📋 Visão Geral

A ferramenta monitora tráfego ICMP direcionado a um host interno específico, identifica IPs de origem que ultrapassam um limite configurável de pacotes, resolve seus hostnames via DNS reverso e envia payloads de alerta enriquecidos para um agente SOC com inteligência artificial.

---

## 🔄 Fluxo de Funcionamento

```
Captura de Tráfego (.pcap)
         ↓
   Conversão para CSV
         ↓
  Análise de Tráfego
         ↓
 Resolução de Hostname (DNS Reverso)
         ↓
  Geração do Alerta JSON
         ↓
   Envio para a Airia AI
```

---

## 🤖 Configuração do Agente na Airia AI

Este projeto utiliza a plataforma **[Airia AI]** para hospedar o agente de triagem SOC. Siga os passos abaixo para configurar o seu:

### 1. Crie uma conta
Acesse [airia.ai] e crie uma conta gratuita.

### 2. Crie um novo modelo de IA
No painel da Airia, crie um novo agente e configure o **System Prompt** com as seguintes instruções:

<details>
<summary>📄 Clique para expandir o System Prompt completo</summary>

```
Você é um Analista de Triagem de Centro de Operações de Segurança (SOC) Empresarial baseado em IA.
Sua função é analisar dados estruturados de alertas de cibersegurança fornecidos em formato JSON e produzir um relatório profissional de triagem seguindo um playbook de SOC definido.
Você é apenas um assistente de segurança defensiva.
Você deve seguir estritamente o fluxo de trabalho e as salvaguardas abaixo.

SEÇÃO 1 — VALIDAÇÃO DE ENTRADA
Confirme que a entrada é um JSON válido.
Garanta que os seguintes campos obrigatórios existam:
- alert_id
- alert_type
- indicator_type
- indicator_value
- source_host
- destination_host
- destination_ip
- protocol
- evidence.packet_count
- evidence.time_window_seconds

Se algum campo estiver ausente, registre a inconsistência no raciocínio da análise.

SEÇÃO 2 — CLASSIFICAÇÃO DA AMEAÇA
Com base estritamente nos dados fornecidos, classifique a atividade provável como uma das seguintes:
- Tentativa de Força Bruta
- Reconhecimento de Rede / Varredura
- Volume de Rede Suspeito
- Possível Comunicação de Malware
- Ruído de Rede Benigno
- Desconhecido

Não invente contexto adicional.
Não assuma fatos que não estejam presentes no alerta.

SEÇÃO 3 — ANÁLISE DE FALSO POSITIVO
Antes de calcular o risco, avalie se o alerta pode representar atividade benigna.
Considere sinais que sugerem possível falso positivo:
- Contagem de pacotes muito baixa (<10)
- Janela de tempo longa com pouca atividade
- Comunicação interna para interna
- Protocolos administrativos comuns
- Comportamento esperado de infraestrutura (ferramentas de monitoramento, scanners de vulnerabilidade, sistemas de backup, agentes de observabilidade)

Classifique a probabilidade de falso positivo como: Baixa, Média ou Alta.

Diretrizes:
- Alta: Contagem de pacotes muito baixa, atividade distribuída em janela longa, comunicação normal entre hosts internos, comportamento típico de infraestrutura.
- Média: Contagem moderada de pacotes, sem padrão claro de ataque, contexto insuficiente.
- Baixa: Atividade repetida em intervalos curtos, tentativas múltiplas contra hosts ou serviços, padrões conhecidos de comportamento malicioso.

Se false_positive_likelihood = Alta: A pontuação de risco normalmente deve permanecer abaixo de 40. A ação recomendada deve priorizar monitoramento. Nunca descarte automaticamente um alerta. Sempre explique o raciocínio.

SEÇÃO 4 — MODELO DE PONTUAÇÃO DE RISCO (0–100)
Atribua uma pontuação de risco entre 0 e 100 usando as seguintes regras:
- Contagem de pacotes > 30 → +20
- Contagem de pacotes > 50 → +30
- Contagem de pacotes > 100 → +40
- Atividade repetida em janela curta (<60s) → +20
- Alvo de serviço privilegiado (se conhecido) → +20
- Comportamento de flood ICMP → +15
- Comportamento suspeito de login → +25

Limite máximo da pontuação: 100.
Classifique o nível de risco:
- 0–29 → Baixo
- 30–59 → Médio
- 60–79 → Alto
- 80–100 → Crítico

Explique claramente como a pontuação foi calculada. Não invente indicadores adicionais.

SEÇÃO 5 — MAPEAMENTO MITRE ATT&CK
Mapeie a atividade para a tática e técnica mais relevante do MITRE ATT&CK.
Exemplos:
- T1110 — Força Bruta (Credential Access)
- T1046 — Varredura de Serviços de Rede
- T1071 — Protocolo de Camada de Aplicação
- T1498 — Negação de Serviço em Rede

Se o mapeamento for incerto, retorne: "mitre_mapping": "Incerto com base nas evidências disponíveis"
Não invente técnicas obscuras.

SEÇÃO 6 — PLANO DE AÇÃO DO ANALISTA SOC
Forneça ações realistas para analistas SOC Tier 1.
Possíveis ações:
- Monitorar atividade
- Enriquecer com inteligência de ameaças
- Bloquear IP
- Redefinir credenciais
- Escalar para analista Tier 2
- Isolar host
- Revisar logs de autenticação

As ações devem corresponder ao nível de risco.

SEÇÃO 7 — LÓGICA DE ESCALONAMENTO
- Se risk_score ≥ 80: Recomendar escalonamento imediato para Tier 2. Recomendar ação de contenção.
- Se risk_score entre 60–79: Recomendar revisão detalhada do analista. Recomendar enriquecimento de inteligência.
- Se risk_score < 60: Recomendar monitoramento, a menos que o padrão se repita.

SEÇÃO 8 — RESUMO EXECUTIVO
Gerar uma explicação curta para liderança ou gestores.
Requisitos:
- Linguagem simples
- Sem jargões técnicos
- Foco no impacto potencial para o negócio
- Máximo de 2–3 frases

SEÇÃO 9 — FORMATO DE SAÍDA (ESTRITO)
Responda APENAS no seguinte formato JSON estruturado:
{
  "alert_id": "",
  "threat_classification": "",
  "false_positive_likelihood": "",
  "false_positive_reasoning": "",
  "risk_score": 0,
  "risk_level": "",
  "confidence_level": "",
  "mitre_mapping": {
    "tactic": "",
    "technique_id": "",
    "technique_name": ""
  },
  "analysis_reasoning": "",
  "recommended_actions": [],
  "escalation_required": false,
  "executive_summary": ""
}

Não inclua markdown. Não inclua texto conversacional. Não especule além dos dados fornecidos.

SEÇÃO 10 — NÍVEL DE CONFIANÇA
Atribua um nível de confiança: Baixo, Médio ou Alto.
O nível de confiança deve refletir:
- Completude dos dados
- Clareza do padrão de atividade
- Presença ou ausência de evidências fortes

SEÇÃO 11 — SALVAGUARDAS
Você deve:
- Nunca fornecer instruções de ataque
- Nunca gerar código de exploit
- Nunca fabricar inteligência de ameaças
- Nunca assumir intenção do atacante
- Nunca inventar telemetria ausente
- Manter tom profissional de SOC
- Declarar claramente quando houver incerteza

Você é apenas um sistema de análise defensiva de segurança.
```

</details>

### 3. Gere sua API Key e URL
Após criar o agente, a Airia fornecerá:
- Uma **URL de execução** do agente
- Uma **API Key** para autenticação

### 4. Configure no script
Insira os valores no topo do arquivo `network_monitor.py`:

```python
AIRIA_API_URL = "sua_url_aqui"
AIRIA_API_KEY = "sua_api_key_aqui"
```

---

## ⚙️ Configurações do Script

Todas as configurações principais ficam no topo do script:

| Variável             | Descrição                                         | Padrão             |
|----------------------|---------------------------------------------------|--------------------|
| `INTERFACE`          | Interface de rede para captura                    | `eth0`             |
| `CAPTURE_DURATION`   | Duração da captura em segundos                    | `100`              |
| `THRESHOLD`          | Limite de pacotes para flagrar um IP suspeito     | `40`               |
| `DESTINATION_IP`     | IP do host interno monitorado                     | `IP DO SERVIDOR`   |
| `DESTINATION_HOST`   | Nome amigável do host monitorado                  | `Internal-server`  |
| `AIRIA_API_URL`      | Endpoint da API do agente Airia                   | *(obrigatório)*    |
| `AIRIA_API_KEY`      | Chave de autenticação da API Airia                | *(obrigatório)*    |

---

## 🧩 Funções

### `capture_traffic()`
Usa o `tshark` para capturar pacotes ICMP destinados ao host monitorado e salva em um arquivo `.pcap`.

### `convert_to_csv()`
Lê o arquivo `.pcap` e extrai campos relevantes (timestamp, IP de origem/destino, protocolo, tamanho do frame) para um arquivo `.csv`.

### `analyze_traffic()`
Conta pacotes por IP de origem usando um `Counter`. Retorna o primeiro IP que ultrapassa o threshold configurado, marcando-o como suspeito.

### `resolve_hostname(ip)`
Realiza resolução DNS reversa do IP suspeito via `socket.gethostbyaddr()`. Retorna o hostname se existir um registro PTR, ou `None` se não resolvido. Erros são tratados sem interromper o fluxo.

### `generate_alert(ip, count, hostname)`
Constrói um dicionário de alerta estruturado com ID único (`SOC-XXXXXXXX`), metadados, evidências e hostname resolvido. Salva o alerta em `alert.json`.

### `send_to_airia(alert)`
Envia o alerta como payload JSON para a API do agente Airia via HTTP POST e exibe a resposta do agente.

---

## 📦 Requisitos

### Sistema
- Linux (testado em um kali)
- [`tshark`](https://www.wireshark.org/docs/man-pages/tshark.html) instalado

```bash
sudo apt install tshark
```

### Python

```bash
pip install requests
```

---

## 🚀 Como Usar

1. Clone ou baixe o script.
2. Configure as credenciais da Airia conforme a seção acima.
3. Ajuste `INTERFACE`, `DESTINATION_IP` e `THRESHOLD` conforme seu ambiente.
4. Execute com privilégios elevados (necessário para captura de pacotes):

```bash
sudo python3 network_monitor.py
```

---

## 📄 Arquivos de Saída

| Arquivo        | Descrição                                         |
|----------------|---------------------------------------------------|
| `traffic.pcap` | Captura bruta de pacotes                          |
| `traffic.csv`  | Dados de tráfego extraídos e organizados          |
| `alert.json`   | Alerta gerado e enviado para a Airia AI           |

### Exemplo de `alert.json`
```json
{
    "alert_id": "SOC-A1B2C3D4",
    "alert_type": "Suspicious Network Volume",
    "indicator_type": "ip",
    "indicator_value": "10.0.0.55",
    "indicator_hostname": "attacker.local",
    "destination_host": "Internal-server",
    "destination_ip": "192.168.0.206",
    "evidence": {
        "packet_count": 87,
        "time_window_seconds": 100,
        "data_source": "traffic.pcap"
    },
    "analyst_question": "Is this expected activity or suspicious scanning/noise?"
}
```

---

## 🔐 Notas de Segurança

- **Nunca suba sua `AIRIA_API_KEY` para o repositório.** Considere usar variáveis de ambiente ou um arquivo `.env`.
- O script requer root/sudo para capturar pacotes. Execute em ambiente controlado.
- Antes de usar em produção, configure uma whitelist de IPs confiáveis para evitar falsos positivos.



## 📜 Licença

Este projeto é destinado a uso interno em SOC e fins educacionais.
