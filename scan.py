import socket
import socks
import threading
from queue import Queue
import ipaddress
import json
import os
import sys
from tqdm import tqdm  # Barre de progression
import time

# Chargement de la configuration
with open("config.json", "r") as f:
    config = json.load(f)

SCAN_NAME = config["scan_name"]
PROXIES = config["proxies"]
TARGETS_FILE = config["targets_file"]
PORTS = config["ports"]
TIMEOUT = config["timeout"]
THREADS_PER_PROXY = config["max_threads_per_proxy"]
OUTPUT_MODE = config["output_mode"]
OUTPUT_DIR = config["output_dir"]
LOG_DIR = config["log_dir"]


LOG_ERROR_FILE = LOG_DIR + SCAN_NAME + "_error.txt"
OUTPUT_FILE = OUTPUT_DIR + SCAN_NAME + "_open.txt"

# Assurer l'existence des répertoires de sortie
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

if os.path.exists(OUTPUT_FILE) or os.path.exists(LOG_ERROR_FILE):
    print(f"[!] WARNING : The {OUTPUT_FILE} or {LOG_ERROR_FILE} file already exists.")
    answer = input("Append results to this file (y/n)")
    if answer != "y":
        print("Well, edit your config file. See you Soon :)")
        exit()
    else :
        print(answer)

# File d'attente pour les tâches
queue = Queue()
lock = threading.Lock()  # Pour la synchronisation d'écriture
LOG_TEMPLATE = "[{status}] - {ip}:{port} via {proxy} -> {message}\n"

# Charger les cibles
def load_targets(file_path):
    targets = set()
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    if "/" in line:  # Plages CIDR
                        for ip in ipaddress.IPv4Network(line, strict=False):
                            targets.add(str(ip))
                    else:
                        targets.add(line)
                except ValueError:
                    print(f"[!] Invalid IP format: {line}")
    return list(targets)

# Vérifier la disponibilité d'un proxy
def test_proxy(proxy):
    try:
        socks.set_default_proxy(socks.SOCKS5, proxy["ip"], proxy["port"])
        s = socks.socksocket()
        s.settimeout(2)
        s.connect(("8.8.8.8", 53))  # Test rapide
        s.close()
        return True
    except Exception:
        return False

# Fonction de scan
def scan(ip, port, proxy, output, progress_bar):
    try:
        socks.set_default_proxy(socks.SOCKS5, proxy["ip"], proxy["port"])
        s = socks.socksocket()
        s.settimeout(TIMEOUT)
        s.connect((ip, port))
        result = LOG_TEMPLATE.format(status="+", ip=ip, port=port, proxy=f"{proxy['ip']}:{proxy['port']}", message="OPEN")
        with lock:
            with open(OUTPUT_FILE, "a") as f:
                f.write(result)
        print(result.strip())
        s.close()
    except socks.ProxyConnectionError as e:
        queue.put((ip, port))
        with lock:
            with open(LOG_ERROR_FILE, "a") as f:
                f.write(f"[!] Error: {SCAN_NAME} - {ip}:{port} via {proxy['ip']}:{proxy['port']} -> {e}\n")    
        print(f"[!] Proxy {proxy['ip']}:{proxy['port']} unreachable. Pausing thread...")
        while not test_proxy(proxy):
            print(f"[~] Waiting for proxy {proxy['ip']}:{proxy['port']} to recover...")
            time.sleep(5)
        print(f"[+] Proxy {proxy['ip']}:{proxy['port']} is back online. Resuming scan.")
    except Exception as e:
        with lock:
            with open(LOG_ERROR_FILE, "a") as f:
                f.write(f"[!] Error: {SCAN_NAME} - {ip}:{port} via {proxy['ip']}:{proxy['port']} -> {e}\n")
    finally:
        progress_bar.update(1)
        queue.task_done()

# Préparer les tâches sans proxy dans la queue
def prepare_tasks(targets, ports):
    for ip in targets:
        for port in ports:
            queue.put((ip, port))

# Démarrer les threads en mode "single"
def start_threads_single(proxies):
    threads = []
    total_tasks = queue.qsize()
    with tqdm(total=total_tasks, desc="Scan Progress", unit="requests") as progress_bar:
        for proxy in proxies:
            for _ in range(THREADS_PER_PROXY):
                t = threading.Thread(target=worker_single, args=(proxy, progress_bar))
                t.start()
                threads.append(t)
        for t in threads:
            t.join()

# Fonction de travail pour les threads (mode single)
def worker_single(proxy, progress_bar):
    while not queue.empty():
        ip, port = queue.get()
        if OUTPUT_MODE == "per_proxy":
            output = os.path.join(OUTPUT_DIR, f"results_{proxy['ip']}_{proxy['port']}.log")
        else:
            output = OUTPUT_FILE
        scan(ip, port, proxy, output, progress_bar)

# Démarrer les threads en mode "per_proxy"
def start_threads_per_proxy(proxies):
    threads = []
    total_tasks = queue.qsize()
    with tqdm(total=total_tasks, desc="Scan Progress", unit="requests") as progress_bar:
        for proxy in proxies:
            for _ in range(THREADS_PER_PROXY):
                t = threading.Thread(target=worker_per_proxy, args=(proxy, progress_bar))
                t.start()
                threads.append(t)
        for t in threads:
            t.join()

# Fonction de travail pour les threads (mode per_proxy)
def worker_per_proxy(proxy, progress_bar):
    while not queue.empty():
        ip, port, output = queue.get()
        scan(ip, port, proxy, output, progress_bar)

# Main
if __name__ == "__main__":
    print("[*] Loading targets...")
    targets = load_targets(TARGETS_FILE)
    if not targets:
        print("[X] No valid targets loaded.")
        sys.exit(1)

    print(f"[*] Loaded {len(targets)} targets.")
    print("[*] Preparing tasks...")

    if OUTPUT_MODE == "single":
        prepare_tasks(targets, PORTS)
        start_threads_single(PROXIES)
    elif OUTPUT_MODE == "per_proxy":
        for proxy in PROXIES:
            output = os.path.join(OUTPUT_DIR, f"results_{proxy['ip']}_{proxy['port']}.log")
            for ip in targets:
                for port in PORTS:
                    queue.put((ip, port, output))
        start_threads_per_proxy(PROXIES)

    print("\n[+] Scan complete. Results saved.")
