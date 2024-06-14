import os
import time
import argparse
from colablib.utils import py_utils
from pydantic import BaseModel
from colablib.utils.py_utils import get_filename
from colablib.sd_models.downloader import aria2_download, download
from colablib.colored_print import cprint, print_line
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

ui, env = detect_environment()
root_path = ui  # Assuming root_path is the same as ui

webui_path = os.path.join(root_path, "ComfyUI")

custom_checkpoints_url = ""
custom_clip_url = ""
custom_clip_version_url = ""
custom_configs_url = ""
custom_controlnet_url = ""
custom_diffusers_url = ""
custom_embeddings_url = ""
custom_gligen_url = ""
custom_hypernetworks_url = ""
custom_loras_url = ""
custom_style_model_url = ""
custom_unet_url = ""
custom_upscale_models_url = ""
custom_vae_url = ""
custom_vae_approx_url = ""
custom_extensions_url = ""

checkpoints_dir     = os.path.join(webui_path, "models", "checkpoints")
clip_dir            = os.path.join(webui_path, "models", "clip")
clip_version_dir    = os.path.join(webui_path, "models", "clip_version")
configs_dir         = os.path.join(webui_path, "models", "configs")
controlnet_dir      = os.path.join(webui_path, "models", "controlnet")
diffusers_dir       = os.path.join(webui_path, "models", "diffusers")
embeddings_dir      = os.path.join(webui_path, "models", "embeddings")
gligen_dir          = os.path.join(webui_path, "models", "gligen")
hypernetworks_dir   = os.path.join(webui_path, "models", "hypernetworks")
loras_dir           = os.path.join(webui_path, "models", "loras")
style_model_dir     = os.path.join(webui_path, "models", "style_models")
unet_dir            = os.path.join(webui_path, "models", "unet")
upscale_models_dir  = os.path.join(webui_path, "models", "upscale_models")
vae_dir             = os.path.join(webui_path, "models", "vae")
vae_approx_dir      = os.path.join(webui_path, "models", "vae_approx")
extension_dir       = os.path.join(webui_path, "custom_nodes")
download_list       = os.path.join(root_path, "download_list.txt")

class CustomDirs(BaseModel):
    url: str
    dst: str

def create_custom_dirs():
    return {
        "checkpoints"         : CustomDirs(url=custom_checkpoints_url, dst=checkpoints_dir),
        "clip"                 : CustomDirs(url=custom_clip_url, dst=clip_dir),
        "clip_version"         : CustomDirs(url=custom_clip_version_url, dst=clip_version_dir),
        "configs"              : CustomDirs(url=custom_configs_url, dst=configs_dir),
        "controlnet"           : CustomDirs(url=custom_controlnet_url, dst=controlnet_dir),
        "diffusers"            : CustomDirs(url=custom_diffusers_url, dst=diffusers_dir),
        "embeddings"           : CustomDirs(url=custom_embeddings_url, dst=embeddings_dir),
        "gligen"               : CustomDirs(url=custom_gligen_url, dst=gligen_dir),
        "hypernetworks"        : CustomDirs(url=custom_hypernetworks_url, dst=hypernetworks_dir),
        "loras"                : CustomDirs(url=custom_loras_url, dst=loras_dir),
        "style_model"          : CustomDirs(url=custom_style_model_url, dst=style_model_dir),
        "unet"                 : CustomDirs(url=custom_unet_url, dst=unet_dir),
        "upscale_models"       : CustomDirs(url=custom_upscale_models_url, dst=upscale_models_dir),
        "vae"                  : CustomDirs(url=custom_vae_url, dst=vae_dir),
        "vae_approx"           : CustomDirs(url=custom_vae_approx_url, dst=vae_approx_dir),
        "extensions"           : CustomDirs(url=custom_extensions_url, dst=extension_dir)
    }

def parse_urls(filename):
    content = read_config(filename)
    lines   = content.strip().split('\n')
    result  = {}
    key     = ''
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
        urls     = value.url.split(",")  # Split the comma-separated URLs
        dst      = value.dst

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

def main(pastebin_url, hf_token, civitai_api_key):
    start_time = time.time()
    textfile_path = download_list
    custom_dirs = create_custom_dirs()
    user_header = f"Authorization: Bearer {hf_token}"
    if pastebin_url:
        textfile_path = custom_download_list(pastebin_url, root_path, user_header)
    download_from_textfile(textfile_path, custom_dirs, civitai_api_key)
    custom_download(custom_dirs, user_header, civitai_api_key)

    elapsed_time = py_utils.calculate_elapsed_time(start_time)
    print_line(0, color="green")
    cprint(f"[+] Download completed within {elapsed_time}.", color="flat_yellow")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download script with pastebin URL and HF token.")
    parser.add_argument("--pastebin_url", type=str, required=True, help="The Pastebin URL.")
    parser.add_argument("--hf_token", type=str, required=True, help="The Hugging Face token.")
    parser.add_argument("--civitai_api_key", type=str, required=True, help="The CivitAI API key.")

    args = parser.parse_args()
    main(args.pastebin_url, args.hf_token, args.civitai_api_key)
