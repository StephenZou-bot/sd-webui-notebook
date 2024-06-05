import re
import requests
from colorama import init, Fore, Back, Style
from colablib.colored_print import cprint, print_line
import time
import subprocess
import threading
try:
    start_colab
except:
    start_colab = int(time.time())-5
    
def get_public_ip(version='ipv4'):
    try:
        url = f'https://api64.ipify.org?format=json&{version}=true'
        response = requests.get(url)
        data = response.json()
        public_ip = data['ip']
        return public_ip
    except Exception as e:
        print(f"Error getting public {version} address:", e)

public_ipv4 = get_public_ip(version='ipv4')

class Tunnel:
    def __init__(self, port):
        self.port = port
        self.tunnels = []
        self.tunnel_urls = []

    def add_tunnel(self, command, name, pattern, note=None):
        tunnel_info = {
            'command': command.format(port=self.port),
            'name': name,
            'pattern': pattern,
            'note': note
        }
        self.tunnels.append(tunnel_info)

    def start_tunnels(self):
        self.processes = []
        for tunnel in self.tunnels:
            process = subprocess.Popen(tunnel['command'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.processes.append((process, tunnel))
        print("Tunnel Started")
        self._get_urls()

    def stop_tunnels(self):
        for process, tunnel in self.processes:
            process.terminate()
            print(f"{Fore.RED}Stopping tunnel{Style.RESET_ALL}")

    def _get_urls(self):
        threads = []
        for process, tunnel in self.processes:
            thread = threading.Thread(target=self._filter_output, args=(process, tunnel))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()

    def _filter_output(self, process, tunnel):
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                self._extract_url(output.strip(), tunnel)

    def _extract_url(self, output, tunnel):
        match = tunnel['pattern'].search(output)
        if match:
            url = match.group(0)
            self.tunnel_urls.append((url, tunnel['note']))
            print(f"* Running on: {url} {tunnel['note'] or ''}")

    def __enter__(self):
        self.start_tunnels()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_tunnels()

tunnel_class = Tunnel
tunnel_port= 1101
tunnel = tunnel_class(tunnel_port)
