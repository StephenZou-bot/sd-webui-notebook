import os
import subprocess
import time
import torch
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

python_version = ".".join(sys.version.split(".")[:2])
colablib_path = f"/opt/conda/lib/python{python_version}/dist-packages/colablib"
aiohttp_path = f"/opt/conda/lib/python{python_version}/site-packages/aiohttp-3.9.1.dist-info"

def install_colablib():
    if not os.path.exists(colablib_path):
        subprocess.run(['pip', 'install', '-q', 'git+https://github.com/StephenZou-bot/colablib'])

def remove_aiohttp():
    if os.path.exists(aiohttp_path):
        subprocess.run(['rm', '-rf', aiohttp_path])
        
remove_aiohttp()
install_colablib()


from colablib.colored_print import cprint, print_line

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

if __name__ == "__main__":
    ui, env = detect_environment()
    branch = "master"
    ui_path = os.path.join(ui, "ComfyUI")
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
        ("apt-get install lz4 && apt install ffmpeg", "Install lz4 ffmpeg"),
        ("pip install colorama", "Install colorama"),
        ("npm install -g localtunnel", "Install localtunnel")
    ]

    parallel_commands = [
        ("curl -s -Lo /usr/bin/cl https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && chmod +x /usr/bin/cl", "Install cloudflared"),
        ("wget https://github.com/fatedier/frp/releases/download/v0.58.1/frp_0.58.1_linux_amd64.tar.gz && tar -xzf frp_0.58.1_linux_amd64.tar.gz -C /usr/bin --strip-components=1 frp_0.58.1_linux_amd64/frpc && rm frp_0.58.1_linux_amd64.tar.gz","Install Frp"),
        (f"cd {ui} && curl -sLO https://github.com/openziti/zrok/releases/download/v0.4.23/zrok_0.4.23_linux_amd64.tar.gz && tar -xzf zrok_0.4.23_linux_amd64.tar.gz && rm -rf zrok_0.4.23_linux_amd64.tar.gz && mv {ui}/zrok /usr/bin", "Install zrok")
    ]

    resource_commands = [
        (f"cd {ui} && aria2c --console-log-level=error -c -x 16 -s 16 -k 1M https://huggingface.co/datasets/Carmeninkunming/fast-repo-kaggle/resolve/main/cui.tar.lz4 -o cui.tar.lz4 && tar -xI lz4 -f cui.tar.lz4 --directory={ui_path} && rm {ui}/cui.tar.lz4", "Install UI"),
        (f"cd {ui_path} && git reset --hard && git pull && git switch {branch} && git pull && git reset --hard", "Update UI")
    ]

    env_specific_commands = []
#     if env == "Colab":
#         env_specific_commands.append(("pip install xformers==0.0.25 --no-deps", "Install xformers for Colab"))
#     elif env == "Kaggle":
#         env_specific_commands.append(("pip install xformers==0.0.26.post1", "Install xformers for Kaggle"))

    total_success, total_error, grand_total_time = 0, 0, 0

    # Execute initial commands
    success_count, error_count, total_time = execute_commands(initial_commands, "Installing initial requirements", debug=False)
    total_success += success_count
    total_error += error_count
    grand_total_time += total_time

    # Execute parallel commands
    cprint(f"[+] Installing parallel commands for [{env}]", color="flat_yellow")
    parallel_start_time = time.time()
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_command = {executor.submit(run_command, cmd, desc, False): desc for cmd, desc in parallel_commands}
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
    success_count, error_count, total_time = execute_commands(resource_commands + env_specific_commands, "Installing resource commands", debug=False)
    total_success += success_count
    total_error += error_count
    grand_total_time += total_time

    print_line(0)
    cprint(f"[+] {total_error} of {total_success + total_error} commands failed. All completed within: {grand_total_time:.2f} secs", color="flat_yellow")