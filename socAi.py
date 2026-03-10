import subprocess
import csv
import json
import os
import uuid
import socket
import requests
from collections import Counter

# ------------------------------------------------
# CONFIGURAÇÃO INICIAL
# ------------------------------------------------

INTERFACE = "eth0"              
CAPTURE_DURATION = 100         
THRESHOLD = 40                  

PCAP_FILE = "traffic.pcap"
CSV_FILE = "traffic.csv"
ALERT_FILE = "alert.json"

# ---- Airia Webhook ----
AIRIA_API_URL = # adicione sua url 
AIRIA_API_KEY = # adicione sua api key

# Metadata
DESTINATION_HOST = "Internal-server"
DESTINATION_IP = #adicione seu host




def run_command(cmd, description):
    print(f"[+] {description}")
    subprocess.run(cmd, check=True)

# ------------------------------------------------
#CAPTURANDO O TRÁFEGO
# ------------------------------------------------

def capture_traffic():
    if os.path.exists(PCAP_FILE):
        os.remove(PCAP_FILE)

    capture_cmd = [
        "tshark",
        "-i", INTERFACE,
        "-f", "icmp and dst host",
        "-a", f"duration:{CAPTURE_DURATION}",
        "-w", PCAP_FILE
    ]

    run_command(capture_cmd, f"Capturing on {INTERFACE} for {CAPTURE_DURATION}s")

    if not os.path.exists(PCAP_FILE):
        raise RuntimeError("PCAP capture failed.")

    print(f"[+] Capture saved to {PCAP_FILE}")

# ------------------------------------------------
# CONVERSÃO PARA CSV
# ------------------------------------------------

def convert_to_csv():
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)

    convert_cmd = [
        "tshark",
        "-r", PCAP_FILE,
        "-T", "fields",
        "-e", "frame.time_epoch",
        "-e", "ip.src",
        "-e", "ip.dst",
        "-e", "ip.proto",
        "-e", "frame.len",
        "-E", "header=y",
        "-E", "separator=,",
        "-E", "quote=d"
    ]

    with open(CSV_FILE, "w", newline="") as outfile:
        subprocess.run(convert_cmd, stdout=outfile, check=True)

    print(f"[+] CSV created at {CSV_FILE}")

# ------------------------------------------------
# ANALISANDO O TRÁFEGO
# ------------------------------------------------

def analyze_traffic():
    ip_counter = Counter()

    with open(CSV_FILE, newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            src_ip = (row.get("ip.src") or "").strip().strip('"')
            if src_ip:
                ip_counter[src_ip] += 1

    print("\n[+] Traffic volume per source IP:\n")
    for ip, count in ip_counter.items():
        print(f"{ip}: {count} packets")

    # Return first suspicious IP found
    for ip, count in ip_counter.items():
        if count > THRESHOLD:
            print(f"\n[!] Suspicious IP detected: {ip}")
            return ip, count

    print("\n[+] No suspicious activity detected.")
    return None, None

# ------------------------------------------------
#  HOSTNAME
# ------------------------------------------------

def resolve_hostname(ip):
    """
    Realiza a resolução DNS reversa de um endereço IP.

    Usa socket.gethostbyaddr(), que consulta o DNS reverso (registro PTR)
    para tentar obter o nome de host associado ao IP.

    O retorno de gethostbyaddr() é uma tupla no formato:
        (hostname, lista_de_aliases, lista_de_enderecos)
    Por isso usamos [0] para pegar apenas o hostname principal.

    Se não houver registro PTR configurado para o IP (comum em IPs
    externos ou mal configurados), a exceção socket.herror é lançada
    e a função retorna None sem interromper o fluxo.

    Parâmetros:
        ip (str): Endereço IP a ser resolvido.

    Retorna:
        str | None: Hostname encontrado, ou None se não houver registro.
    """
    try:
        # Tenta buscar o hostname via DNS reverso
        hostname = socket.gethostbyaddr(ip)[0]
        print(f"[+] Hostname resolvido: {ip} → {hostname}")
        return hostname

    except socket.herror:
        # Lançado quando não há registro DNS reverso para o IP
        print(f"[+] Sem hostname para {ip} (sem registro PTR)")
        return None

    except Exception as e:
        # Captura erros inesperados (ex: timeout, falha de rede)
        print(f"[!] Erro ao resolver hostname para {ip}: {e}")
        return None

# ------------------------------------------------
# GEAR O ALERTA EM JSON
# ------------------------------------------------

def generate_alert(ip, count, hostname=None):
    alert_id = f"SOC-{uuid.uuid4().hex[:8].upper()}"

    alert = {
        "alert_id": alert_id,
        "alert_type": "Suspicious Network Volume",
        "indicator_type": "ip",
        "indicator_value": ip,
        # Hostname incluído no alerta se disponível, caso contrário "Unresolved"
        "indicator_hostname": hostname if hostname else "Unresolved",
        "destination_host": DESTINATION_HOST,
        "destination_ip": DESTINATION_IP,
        "evidence": {
            "packet_count": count,
            "time_window_seconds": CAPTURE_DURATION,
            "data_source": os.path.basename(PCAP_FILE)
        },
        "analyst_question": "Is this expected activity or suspicious scanning/noise?"
    }

    with open(ALERT_FILE, "w") as f:
        json.dump(alert, f, indent=4)

    print(f"[+] Alert JSON written to {ALERT_FILE}")
    return alert

# ------------------------------------------------
# STEP 6 – ENVIA PARA A API DA AIRA
# ------------------------------------------------

def send_to_airia(alert):
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": # SUA CHAVE API AQUI
    }

    payload = {
        "userInput": json.dumps(alert),
        "asyncOutput": False
    }

    print("[+] Sending alert to Airia Agent Execution API...")

    response = requests.post(
        AIRIA_API_URL,
        headers=headers,
        json=payload,
        timeout=100
    )

    response.raise_for_status()

    print(f"[+] Airia responded with status {response.status_code}")

    try:
        data = response.json()
        print("[+] Airia Response JSON:")
        print(json.dumps(data, indent=2))
    except Exception:
        print("[+] Airia response (raw text):")
        print(response.text)

# ------------------------------------------------
# FUNÇÃO MAIN
# ------------------------------------------------

def main():
    try:
        capture_traffic()
        convert_to_csv()
        ip, count = analyze_traffic()

        if ip:
            # Tenta resolver o hostname do IP suspeito antes de gerar o alerta
            hostname = resolve_hostname(ip)

            # Passa o hostname para o alerta (pode ser None se não resolvido)
            alert = generate_alert(ip, count, hostname)

            send_to_airia(alert)
        else:
            print("[+] No alert generated, nothing sent to Airia.")

        print("\n[+] Workflow complete.")

    except Exception as e:
        print(f"\n[!] Error: {e}")

if __name__ == "__main__":
    main()