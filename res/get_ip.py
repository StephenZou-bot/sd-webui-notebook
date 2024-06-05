import re
import requests
from colorama import init, Fore, Back, Style
from colablib.colored_print import cprint, print_line
import time
import subprocess
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
            self.processes.append(process)
            print(f"{Fore.GREEN}Started tunnel {tunnel['name']} with command: {tunnel['command']}{Style.RESET_ALL}")
            if tunnel['note']:
                print(f"{Fore.YELLOW}{tunnel['note']}{Style.RESET_ALL}")
            self._filter_output(process)

    def stop_tunnels(self):
        for process in self.processes:
            process.terminate()
            print(f"{Fore.RED}Terminated tunnel process {process.pid}{Style.RESET_ALL}")

    def _filter_output(self, process):
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                self._print_filtered_output(output.strip())

    def _print_filtered_output(self, output):
        if "your url is" in output or "Visit it at" in output:
            print(f"{Fore.CYAN}{output}{Style.RESET_ALL}")
        elif re.search(r"https?://[\w.-]+", output):
            print(f"{Fore.CYAN}{output}{Style.RESET_ALL}")

    def __enter__(self):
        self.start_tunnels()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop_tunnels()

tunnel_class = Tunnel
tunnel_port= 1101
tunnel = tunnel_class(tunnel_port)
