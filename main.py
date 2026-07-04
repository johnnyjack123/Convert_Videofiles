from file_handler import check_file, update_entries, collect_paths
import argparse
from utils import collect_informations, detect_gpu_vendor, process_queue, print_config

def start_program():
    input_folder_path, output_folder_path = collect_informations()
    video_queue = collect_paths(input_folder_path)
    process_queue(video_queue, output_folder_path)
    return

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", action="store_true")

    args = parser.parse_args()
    return args

def setup_gpu():
    gpu_info = detect_gpu_vendor()
    update_entries([{"gpu_info": gpu_info}])
    return

def setup_program():
    args = parse_arguments()
    if args.config:
        print_config()
        return False
    check_file()
    setup_gpu()
    return True

result = setup_program()
if result:
    start_program()