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

    args = parser.parse_args()
    return args

def setup_gpu():
    config = read()
    if config.gpu_index == -1:
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
    setup_gpu()
    return True

result = setup_program()
if result:
    start_program()