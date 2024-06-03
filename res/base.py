import os
import subprocess
import time
import torch
from colablib.colored_print import cprint, print_line

# Detect environment using environment variables
if 'COLAB_GPU' in os.environ:
    ui = "/content"
    env = 'Colab'
elif 'KAGGLE_KERNEL_RUN_TYPE' in os.environ:
    ui = "/home"
    env = 'Kaggle'
else:
    cprint('Error. Environment not detected', color="flat_red")
    exit(1)
    
branch = "master"
ui_path = os.path.join(ui, "sdw")
git_path = os.path.join(ui_path, "extensions")

torch_ver = torch.__version__
cuda_ver = torch.version.cuda
is_gpu = "Yes." if torch.cuda.is_available() else "GPU not detected."

def runSh(args, *, output=False, shell=False, cd=None):
    import subprocess, shlex

    if not shell:
        if output:
            proc = subprocess.Popen(
                shlex.split(args), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=cd
            )
            while True:
                output = proc.stdout.readline()
                if output == b"" and proc.poll() is not None:
                    return
                if output:
                    print(output.decode("utf-8").strip())
        return subprocess.run(shlex.split(args), cwd=cd).returncode
    else:
        if output:
            return (
                subprocess.run(
                    args,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=cd,
                )
                .stdout.decode("utf-8")
                .strip()
            )
        return subprocess.run(args, shell=True, cwd=cd).returncode

if __name__ == "__main__":   
    cprint(f"[+] PyTorch Version : {torch_ver} | Cuda : {cuda_ver} | GPU Access : {is_gpu}", color="flat_green")
    print_line(0)
    
    rudi = [
        ("apt-get update && apt -y install aria2 && pip install trash-cli && trash-put /opt/conda/lib/python3.10/site-packages/aiohttp*", "aria2"),
        ("apt-get install lz4", "lz4"),
        ("pip install colorama", "colorama"),
        ("npm install -g localtunnel", "localtunnel"),
        ("curl -s -OL https://github.com/DEX-1101/sd-webui-notebook/raw/main/res/new_tunnel", "new_tunnel"),
        ("curl -s -Lo /usr/bin/cl https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && chmod +x /usr/bin/cl", "cloudflared"),
        (f"curl -sLO https://github.com/openziti/zrok/releases/download/v0.4.23/zrok_0.4.23_linux_amd64.tar.gz && tar -xzf zrok_0.4.23_linux_amd64.tar.gz && rm -rf zrok_0.4.23_linux_amd64.tar.gz && mv {ui}/zrok /usr/bin", "zrok"),
        (f"wget https://github.com/gutris1/segsmaker/raw/main/kaggle/script/pantat88.py -O {ui}/semvak_zeus.py", "semvak_zeus.py")
    ]

    yanto = [
        (f"wget https://raw.githubusercontent.com/DEX-1101/SecretNAI/main/download_list.txt -O {ui}/download_list.txt", "download_list.txt"),
        (f"aria2c --console-log-level=error -c -x 16 -s 16 -k 1M https://huggingface.co/x1101/UI/resolve/main/ui.tar.lz4 -o ui.tar.lz4 && tar -xI lz4 -f ui.tar.lz4 && mv {ui}/kaggle/working/x1101 {ui} && rm {ui}/ui.tar.lz4 && rm -rf {ui}/kaggle", "Installing UI..."),
        (f"cd {ui_path} && git reset --hard && git pull && git switch {branch} && git pull && git reset --hard", "Updating UI..."),
        (f"rm -rf {git_path}/* && cd {git_path} && git clone https://github.com/BlafKing/sd-civitai-browser-plus && git clone https://github.com/Mikubill/sd-webui-controlnet && git clone https://github.com/DominikDoom/a1111-sd-webui-tagcomplete && git clone https://github.com/DEX-1101/sd-encrypt-image && git clone https://github.com/DEX-1101/timer && git clone https://github.com/gutris1/sd-hub && git clone https://github.com/Bing-su/adetailer.git && git clone https://github.com/zanllp/sd-webui-infinite-image-browsing && git clone https://github.com/thomasasfk/sd-webui-aspect-ratio-helper && git clone https://github.com/hako-mikan/sd-webui-regional-prompter && git clone https://github.com/picobyte/stable-diffusion-webui-wd14-tagger && git clone https://github.com/Coyote-A/ultimate-upscale-for-automatic1111 && git clone https://github.com/Haoming02/sd-webui-tabs-extension", "Installing Extensions..."),
        
    ]

    agus = []
    
    if env == 'Colab':
        agus.append(("pip install xformers==0.0.25 --no-deps", "Installing xformers..."))
    elif env == 'Kaggle':
        agus.append(("pip install xformers==0.0.26.post1", "Installing xformers..."))
    else:
        agus.append((""))
            
    si_kontol = 0
    kntl = 0
    total_time = 0
    
    cprint(f"[+] Installing [{env}] Requirements", color="flat_yellow")
    for oppai, asu in rudi + yanto + agus:
        cprint(f"    > {asu}", color="flat_cyan")
        start_time = time.time()
        return_code = runSh(oppai, shell=True)
        if return_code == 0:
            si_kontol += 1
        else:
            cprint(f"Error at [{asu}]: Command failed with return code {return_code}", color="flat_red")
            kntl += 1
        end_time = time.time()
        total_time += end_time - start_time
        
    print_line(0)
    cprint(f"[+] {kntl} of {si_kontol} error found. All completed within: {total_time:.2f} secs", color="flat_yellow")
