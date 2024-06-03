import os
import subprocess
import time
import torch
from colablib.colored_print import cprint, print_line

def detect_environment():
    if 'COLAB_GPU' in os.environ:
        ui = "/content"
        env = 'Colab'
    elif 'KAGGLE_KERNEL_RUN_TYPE' in os.environ:
        ui = "/home"
        env = 'Kaggle'
    else:
        cprint('Error. Environment not detected', color="flat_red")
        return None, None

def get_versions():
    torch_ver = torch.__version__
    cuda_ver = torch.version.cuda
    is_gpu = "Yes." if torch.cuda.is_available() else "GPU not detected."
    return torch_ver, cuda_ver, is_gpu

def execute_command(command, description, success_count, error_count):
    start_time = time.time()
    cprint(f"    > {description}", color="flat_cyan")
    try:
        subprocess.run(command, check=True, shell=True, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        success_count += 1
    except subprocess.CalledProcessError as e:
        print(f"Error at [{description}]: {e}")
        error_count += 1
    end_time = time.time()
    return success_count, error_count, end_time - start_time

if __name__ == "__main__":
    ui, env = detect_environment()
    if not ui:
        exit(1)

    ui_path = os.path.join(ui, "x1101")
    git_path = os.path.join(ui_path, "extensions")

    torch_ver, cuda_ver, is_gpu = get_versions()

    cprint(f"[+] PyTorch Version: {torch_ver} | Cuda: {cuda_ver} | GPU Access: {is_gpu}", color="flat_green")
    print_line(0)
    
    install_commands = [
        ("apt-get update && apt -y install aria2 && rm -rf /opt/conda/lib/python3.10/site-packages/aiohttp*", "Install aria2"),
        ("apt-get install lz4", "Install lz4"),
        ("pip install colorama", "Install colorama"),
        ("npm install -g localtunnel", "Install localtunnel"),
        ("curl -s -Lo /usr/bin/cl https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && chmod +x /usr/bin/cl", "Install cloudflared"),
        (f"curl -sLO https://github.com/openziti/zrok/releases/download/v0.4.23/zrok_0.4.23_linux_amd64.tar.gz && tar -xzf zrok_0.4.23_linux_amd64.tar.gz && rm -rf zrok_0.4.23_linux_amd64.tar.gz && mv {ui}/zrok /usr/bin", "Install zrok"),
        (f"wget https://github.com/gutris1/segsmaker/raw/main/kaggle/script/pantat88.py -O {ui}/semvak_zeus.py", "Download semvak_zeus.py script")
    ]
    additional_commands = []
    
    if env == 'Colab':
        additional_commands.append(("pip install xformers==0.0.25 --no-deps", "Install xformers"))
    elif env == 'Kaggle':
        additional_commands.append(("pip install xformers==0.0.26.post1", "Install xformers"))
            
    success_count = 0
    error_count = 0
    total_time = 0
    
    cprint(f"[+] Installing [{env}] Requirements", color="flat_yellow")
    for command, description in install_commands + additional_commands:
        success_count, error_count, command_time = execute_command(command, description, success_count, error_count)
        total_time += command_time
        
    print_line(0)
    cprint(f"[+] {error_count} of {success_count} commands failed. All completed within: {total_time:.2f} secs", color="flat_yellow")
