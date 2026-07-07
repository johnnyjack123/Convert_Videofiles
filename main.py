from file_handler import check_file, update_entries, collect_paths, read, GPUInfo
import argparse
from utils import collect_informations, detect_gpu_vendor, process_queue, print_config

def start_program():
    input_folder_path, output_folder_path = collect_informations()
    video_queue = collect_paths(input_folder_path)
    process_queue(video_queue, input_folder_path, output_folder_path)
    return

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", action="store_true")
    parser.add_argument("--regpu", action="store_true",
                         help="Force re-detection of the GPU vendor "
                              "(useful if the app is stuck on CPU despite "
                              "having a working NVIDIA/AMD GPU).")

    args = parser.parse_args()
    return args

def _looks_like_dedicated_gpu(gpu_names):
    return any(("nvidia" in n.lower() or "amd" in n.lower() or "radeon" in n.lower()) for n in gpu_names)

def setup_gpu(force=False):
    config = read()

    # Auto-heal: if a dedicated GPU is physically present but the stored
    # vendor is still "cpu" (e.g. detection failed once, ffmpeg was missing
    # nvenc/amf support at that time, etc.), re-run detection instead of
    # being stuck on CPU forever.
    stale_cpu_fallback = (
        config.gpu_info.vendor == "cpu"
        and _looks_like_dedicated_gpu(config.gpu_info.gpu_names)
    )

    if config.gpu_index == -1 or force or stale_cpu_fallback:
        if stale_cpu_fallback and not force:
            print("A dedicated GPU was found but is currently marked as unusable "
                  "(vendor='cpu'). Re-checking GPU support...")
        gpu_info = detect_gpu_vendor()
        gpu_list = gpu_info["gpu_names"]
        gpu_number = len(gpu_list)
        if gpu_number > 1:
            print(f"{gpu_number} GPUs found:")
            x = 1
            while x <= gpu_number:
                print(f"[{x}] {gpu_list[(x-1)]}")
                x = x+1
            while True:
                gpu_index = input("Select GPU by index: ")
                try:
                    gpu_index = int(gpu_index) - 1
                except Exception as e:
                    print(f"Invalid input: {e}")
                    continue
                if gpu_index < 0 or gpu_index > gpu_number - 1:
                    print(f"Invalid input: select a number between 1 and {gpu_number}.")
                    continue
                break
        else:
            gpu_index = 0
        update_entries({"gpu_index": gpu_index})
        gpu_info_model = GPUInfo.model_validate(gpu_info)
        update_entries({"gpu_info": gpu_info_model})

        config = read()
        if gpu_number > 0:
            print(f"GPU set to: {config.gpu_info.gpu_names[gpu_index]}")
        else:
            print("No usable GPU detected; using CPU.")
    return

def setup_program():
    args = parse_arguments()
    check_file()
    if args.config:
        print_config()
        return False
    setup_gpu(force=args.regpu)
    return True

result = setup_program()
if result:
    start_program()