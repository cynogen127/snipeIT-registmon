#!/usr/bin/env python3
"""
Network Printer Scanner
Scans the network for printers and displays their IP addresses.
"""

import socket
import ipaddress
import threading
from queue import Queue
import argparse

PRINTER_PORTS = [9100, 631, 515, 161]  # JetDirect, IPP, LPD, SNMP

GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_printer_port(ip, port, timeout=1):
    """Check if a specific port is open on the IP address."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((str(ip), port))
        sock.close()
        return result == 0
    except:
        return False

def get_device_info(ip):
    """Try to get hostname of the device."""
    try:
        hostname = socket.gethostbyaddr(str(ip))[0]
        return hostname
    except:
        return "Unknown"

def scan_ip(ip, results):
    """Scan a single IP for printer ports."""
    open_ports = []

    for port in PRINTER_PORTS:
        if check_printer_port(ip, port):
            open_ports.append(port)

    if open_ports:
        hostname = get_device_info(ip)
        results.append({
            'ip': str(ip),
            'hostname': hostname,
            'ports': open_ports
        })
        print(f"{GREEN}[+] Found potential printer: {ip} ({hostname}) - Ports: {open_ports}{RESET}")

def worker(queue, results):
    """Worker thread to scan IPs from the queue."""
    while True:
        ip = queue.get()
        if ip is None:
            break
        scan_ip(ip, results)
        queue.task_done()

def scan_network(network, num_threads=50):
    """Scan the network for printers using multiple threads."""
    print(f"{BLUE}[*] Starting scan on network: {network}{RESET}")
    print(f"{BLUE}[*] Using {num_threads} threads{RESET}")
    print(f"{BLUE}[*] Scanning ports: {PRINTER_PORTS}{RESET}\n")

    results = []
    queue = Queue()

    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker, args=(queue, results))
        t.start()
        threads.append(t)

    net = ipaddress.ip_network(network, strict=False)
    total_hosts = sum(1 for _ in net.hosts())

    print(f"{BLUE}[*] Scanning {total_hosts} hosts...{RESET}\n")

    for ip in net.hosts():
        queue.put(ip)

    queue.join()

    for _ in range(num_threads):
        queue.put(None)
    for t in threads:
        t.join()

    return results

def display_results(results):
    """Display the scan results in a formatted table."""
    print(f"\n{'='*80}")
    print(f"{YELLOW}SCAN RESULTS - Found {len(results)} potential printer(s){RESET}")
    print(f"{'='*80}\n")

    if not results:
        print(f"{YELLOW}No printers found on the network.{RESET}")
        return

    print(f"{'IP Address':<20} {'Hostname':<30} {'Open Ports':<30}")
    print(f"{'-'*80}")

    for printer in sorted(results, key=lambda x: ipaddress.ip_address(x['ip'])):
        ports_str = ', '.join(map(str, printer['ports']))
        print(f"{printer['ip']:<20} {printer['hostname']:<30} {ports_str:<30}")

    print(f"\n{GREEN}Port Legend:{RESET}")
    print(f"  9100 = JetDirect (Raw/HP)")
    print(f"  631  = IPP (Internet Printing Protocol)")
    print(f"  515  = LPD (Line Printer Daemon)")
    print(f"  161  = SNMP (Network Management)")

def main():
    parser = argparse.ArgumentParser(
        description='Scan network for printers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s -n 192.168.1.0/24
  %(prog)s -n 10.0.0.0/24 -t 100
  %(prog)s --network 172.16.0.0/16 --threads 200
        ''')

    parser.add_argument('-n', '--network',
                        required=True,
                        help='Network to scan in CIDR notation (e.g., 192.168.1.0/24)')
    parser.add_argument('-t', '--threads',
                        type=int,
                        default=50,
                        help='Number of threads to use (default: 50)')

    args = parser.parse_args()

    try:
        ipaddress.ip_network(args.network, strict=False)

        results = scan_network(args.network, args.threads)

        display_results(results)

    except ValueError as e:
        print(f"{YELLOW}[!] Invalid network address: {e}{RESET}")
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[!] Scan interrupted by user{RESET}")
    except Exception as e:
        print(f"{YELLOW}[!] Error: {e}{RESET}")

if __name__ == "__main__":
    main()
