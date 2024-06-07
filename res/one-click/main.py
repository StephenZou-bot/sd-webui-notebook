import time
import sys
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Thread
import argparse
import torch
import re
import requests
from colorama import init, Fore, Back, Style
from pydantic import BaseModel  # 导入BaseModel

init(autoreset=True)

class CustomDirs(BaseModel):
    url: str
    dst: str

def install_colablib():
    if not os.path.exists(colablib_path):
        subprocess.run(['pip', 'install', '-q', 'git+https://github.com/StephenZou-bot/colablib'])

def remove_aiohttp():
    if os.path.exists(aiohttp_path):
        subprocess.run(['rm', '-rf', aiohttp_path])
    
python_version = ".".join(sys.version.split(".")[:2])
colablib_path = f"/opt/conda/lib/python{python_version}/dist-packages/colablib"
aiohttp_path = f"/opt/conda/lib/python{python_version}/site-packages/aiohttp-3.9.1.dist-info"

remove_aiohttp()
install_colablib()

from colablib.colored_print import cprint, print_line
from colablib.utils import py_utils
from colablib.utils.py_utils import get_filename
from colablib.sd_models.downloader import aria2_download, download
from colablib.utils.config_utils import read_config
from colablib.utils.git_utils import clone_repo

def detect_environment():
    iskaggle = os.environ.get('KAGGLE_KERNEL_RUN_TYPE', '')
    iscolab = 'COLAB_GPU' in os.environ
    if iscolab:
        return "/content", "Colab"
    elif iskaggle:
        return "/home", "Kaggle"
    else:
        cprint('Error. Environment not detected', color="flat_red")
        exit(1)

def run_command(command, description, debug=True):
    start_time = time.time()
    cprint(f"    > {description}", color="flat_cyan")
    try:
        result = subprocess.run(command, check=True, shell=True, text=True,
                                stdout=subprocess.PIPE if debug else subprocess.DEVNULL,
                                stderr=subprocess.PIPE if debug else subprocess.DEVNULL)
        if debug:
            cprint(result.stdout, color="flat_green")
            cprint(result.stderr, color="flat_red")
        end_time = time.time()
        return True, end_time - start_time
    except subprocess.CalledProcessError as e:
        cprint(f"Error at [{description}]: {e}", color="flat_red")
        end_time = time.time()
        return False, end_time - start_time

def execute_commands(commands, description, debug=True):
    cprint(f"[+] {description}", color="flat_yellow")
    start_time = time.time()
    success_count, error_count = 0, 0
    for command, desc in commands:
        success, command_time = run_command(command, desc, debug)
        success_count += success
        error_count += not success
    end_time = time.time()
    cprint(f"[+] {description} completed in: {end_time - start_time:.2f} secs", color="flat_yellow")
    return success_count, error_count, end_time - start_time

def parse_urls(filename):
    content = read_config(filename)
    lines = content.strip().split('\n')
    result = {}
    key = ''
    for line in lines:
        if not line.strip():
            continue
        if line.startswith('//'):
            continue
        if line.startswith('#'):
            key = line[1:].lower()
            result[key] = []
        else:
            urls = [url.strip() for url in line.split(',') if url.strip() != '']
            result[key].extend(urls)
    return result

def custom_download(custom_dirs, user_header, civitai_api_key):
    for key, value in custom_dirs.items():
        urls = value.url.split(",")  # Split the comma-separated URLs
        dst = value.dst

        if value.url:
            print_line(0, color="green")
            cprint(f" [+] Downloading {key}.", color="flat_yellow")

        for url in urls:
            url = url.strip()  # Remove leading/trailing whitespaces from each URL
            if url != "":
                print_line(0, color="green")
                if "|" in url:
                    url, filename = map(str.strip, url.split("|"))
                    if not filename.endswith((".safetensors", ".ckpt", ".pt", "pth")):
                        filename = filename + os.path.splitext(get_filename(url))[1]
                else:
                    if not url.startswith("fuse:"):
                        filename = get_filename(url)

                if url.startswith("fuse:"):
                    fuse(url, key, dst)
                elif key == "extensions":
                    clone_repo(url, cwd=dst)
                else:
                    download(url=url, filename=filename, user_header=user_header, dst=dst, quiet=False)

def download_from_textfile(filename, custom_dirs, civitai_api_key):
    for key, urls in parse_urls(filename).items():
        for url in urls:
            if "civitai.com" in url:
                url += f"&ApiKey={civitai_api_key}" if "?" in url else f"?ApiKey={civitai_api_key}"
        key_lower = key.lower()
        if key_lower in custom_dirs:
            if custom_dirs[key_lower].url:
                custom_dirs[key_lower].url += ',' + ','.join(urls)
            else:
                custom_dirs[key_lower].url = ','.join(urls)
        else:
            cprint(f"Warning: Category '{key}' from the file is not found in custom_dirs.", color="flat_yellow")

def custom_download_list(url, root_path, user_header):
    filename = "custom_download_list.txt"
    filepath = os.path.join(root_path, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    if 'pastebin.com' in url:
        if 'raw' not in url:
            url = url.replace('pastebin.com', 'pastebin.com/raw')
    download(url=url, filename=filename, user_header=user_header, dst=root_path, quiet=True)
    return filepath

def create_custom_dirs():
    return {
        "model": CustomDirs(url=custom_model_url, dst=models_dir),
        "vae": CustomDirs(url=custom_vae_url, dst=vaes_dir),
        "embedding": CustomDirs(url=custom_embedding_url, dst=embeddings_dir),
        "lora": CustomDirs(url=custom_LoRA_url, dst=lora_dir),
        "extensions": CustomDirs(url=custom_extensions_url, dst=extensions_dir),
    }

def get_public_ip(version='ipv4'):
    try:
        url = f'https://api64.ipify.org?format=json&{version}=true'
        response = requests.get(url)
        data = response.json()
        public_ip = data['ip']
        return public_ip
    except Exception as e:
        print(f"Error getting public {version} address:", e)

def parse_args():
    parser = argparse.ArgumentParser(description="Script to set up environment and install necessary packages")
    parser.add_argument("--pastebin", type=str, help="Pastebin URL if you want to download model/lora/extensions.", default="")
    parser.add_argument("--hf_token", type=str, help="HuggingFace's Token if you download it from private repo for Pastebin download.")
    parser.add_argument("--zrok_token", type=str, help="Token for tunneling with Zrok (optional).")
    parser.add_argument("--ngrok_token", type=str, help="Token for tunneling with ngrok (optional).")
    parser.add_argument("--hub_token", type=str, help="Token for HUB extension for easily downloading stuff inside WebUI, do NOT put your token here but instead link file contains the token.")
    parser.add_argument("--debug", action='store_true', help="Enable debug mode.")
    return parser.parse_args()

def main():
    args = parse_args()

    ui, env = detect_environment()
    branch = "master"
    ui_path = os.path.join(ui, "sdw")
    os.makedirs(ui_path, exist_ok=True)
    git_path = os.path.join(ui_path, "extensions")
    torch_ver = torch.__version__
    cuda_ver = torch.version.cuda
    is_gpu = "Yes." if torch.cuda.is_available() else "GPU not detected."

    cprint(f"[+] PyTorch Version: {torch_ver} | Cuda: {cuda_ver} | GPU Access: {is_gpu}", color="flat_green")
    print_line(0)

    initial_commands = [
        ("apt-get update", "Update package list"),
        ("apt -y install aria2", "Install aria2"),
        ("apt-get install lz4", "Install lz4"),
        ("pip install colorama", "Install colorama"),
        ("npm install -g localtunnel", "Install localtunnel")
    ]

    parallel_commands = [
        ("curl -s -Lo /usr/bin/cl https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && chmod +x /usr/bin/cl", "Install cloudflared"),
        (f"cd {ui} && curl -sLO https://github.com/openziti/zrok/releases/download/v0.4.23/zrok_0.4.23_linux_amd64.tar.gz && tar -xzf zrok_0.4.23_linux_amd64.tar.gz && rm -rf zrok_0.4.23_linux_amd64.tar.gz && mv {ui}/zrok /usr/bin", "Install zrok")
    ]

    resource_commands = [
        (f"cd {ui} && aria2c --console-log-level=error -c -x 16 -s 16 -k 1M https://huggingface.co/datasets/Carmeninkunming/fast-repo-kaggle/resolve/main/sdw.tar.lz4 -o sdw.tar.lz4 && tar -xI lz4 -f sdw.tar.lz4 --directory={ui_path} && rm {ui}/sdw.tar.lz4", "Install UI"),
        (f"cd {ui} && aria2c --console-log-level=error -c -x 16 -s 16 -k 1M https://huggingface.co/datasets/Carmeninkunming/fast-repo-kaggle/resolve/main/site-packages.tar.lz4 -o site-packages.tar.lz4 && tar -xI lz4 -f site-packages.tar.lz4 --directory=/opt/conda/lib/python{python_version}/site-packages && rm {ui}/site-packages.tar.lz4", "Prepare Packages"),
        (f"cd {ui} && aria2c --console-log-level=error -c -x 16 -s 16 -k 1M https://huggingface.co/datasets/Carmeninkunming/fast-repo-kaggle/resolve/main/cache.tar.lz4 -o cache.tar.lz4 && tar -xI lz4 -f cache.tar.lz4 --directory=/ && rm {ui}/cache.tar.lz4", "Prepare Huggingface Cache"),
        (f"cd {ui_path} && git reset --hard && git pull && git switch {branch} && git pull && git reset --hard", "Update UI")
    ]

    env_specific_commands = []

    total_success, total_error, grand_total_time = 0, 0, 0

    # Execute initial commands
    success_count, error_count, total_time = execute_commands(initial_commands, "Installing initial requirements", debug=args.debug)
    total_success += success_count
    total_error += error_count
    grand_total_time += total_time

    # Execute parallel commands
    cprint(f"[+] Installing parallel commands for [{env}]", color="flat_yellow")
    parallel_start_time = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_command = {executor.submit(run_command, cmd, desc, args.debug): desc for cmd, desc in parallel_commands}
        for future in as_completed(future_to_command):
            desc = future_to_command[future]
            try:
                success, command_time = future.result()
                total_success += success
                total_error += not success
                grand_total_time += command_time
            except Exception as exc:
                cprint(f'Command {desc} generated an exception: {exc}', color="flat_red")
                total_error += 1
    parallel_end_time = time.time()
    cprint(f"[+] Parallel commands completed in: {parallel_end_time - parallel_start_time:.2f} secs", color="flat_yellow")

    # Execute resource and environment-specific commands
    success_count, error_count, total_time = execute_commands(resource_commands + env_specific_commands, "Installing resource commands", debug=args.debug)
    total_success += success_count
    total_error += error_count
    grand_total_time += total_time

    print_line(0)
    cprint(f"[+] {total_error} of {total_success + total_error} commands failed. All completed within: {grand_total_time:.2f} secs", color="flat_yellow")

    ################# PASTEBIN DL #################
    root_path = ui  # Assuming root_path is the same as ui

    webui_path = os.path.join(root_path, "sdw")

    custom_model_url = ""
    custom_vae_url = ""
    custom_embedding_url = ""
    custom_LoRA_url = ""
    custom_extensions_url = ""
    models_dir = os.path.join(webui_path, "models", "Stable-diffusion")
    vaes_dir = os.path.join(webui_path, "models", "VAE")
    lora_dir = os.path.join(webui_path, "models", "Lora")
    embeddings_dir = os.path.join(webui_path, "embeddings")
    extensions_dir = os.path.join(webui_path, "extensions")
    download_list = os.path.join(root_path, "download_list.txt")

    custom_dirs = create_custom_dirs()
    user_header = f"Authorization: Bearer {args.hf_token}"
    if args.pastebin:
        textfile_path = custom_download_list(args.pastebin, root_path, user_header)
    download_from_textfile(download_list, custom_dirs, args.hf_token)
    custom_download(custom_dirs, user_header, args.hf_token)

    elapsed_time = py_utils.calculate_elapsed_time(start_time)
    print_line(0, color="green")
    cprint(f"[+] Download completed within {elapsed_time}.", color="flat_yellow")

    from colablib.utils.tunnel import Tunnel

    try:
        start_colab
    except:
        start_colab = int(time.time()) - 5

    public_ipv4 = get_public_ip(version='ipv4')

    tunnel_port = 7860
    tunnel = Tunnel(tunnel_port)
    tunnel.add_tunnel(command="cl tunnel --url localhost:{port}", name="cl", pattern=re.compile(r"[\w-]+\.trycloudflare\.com"))
    tunnel.add_tunnel(command="lt --port {port}", name="lt", pattern=re.compile(r"[\w-]+\.loca\.lt"), note="Password : " + Fore.GREEN + public_ipv4 + Style.RESET_ALL + " rerun cell if 404 error.")
    if args.zrok_token:
        subprocess.run(f"zrok enable {args.zrok_token}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tunnel.add_tunnel(command="zrok share public http://localhost:{port}/ --headless", name="zrok", pattern=re.compile(r"[\w-]+\.share\.zrok\.io"))

    with tunnel:
        subprocess.run(f"echo -n {start_colab} >{webui_path}/static/colabTimer.txt", shell=True)
        subprocess.run(f"cd {webui_path} && python launch.py --port=7860 --ngrok {args.ngrok_token} --api --xformers --theme dark --enable-insecure-extension-access --disable-console-progressbars --disable-safe-unpickle --no-half-vae", shell=True)

if __name__ == "__main__":
    main()
