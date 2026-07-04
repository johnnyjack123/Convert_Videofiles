from pathlib import Path
from file_handler import file_healthcheck, read, update_entries, collect_paths
from converter import start_ffmpeg
import platform
import shutil
import subprocess

def print_config():
    config = read()
    print(f"Config: \n {config}")
    return

def process_queue(video_queue, output_folder_path):
    config = read()
    videos = len(video_queue)
    count = 1
    for input_file_path in video_queue:
        print(f"Video {count} of {videos}.")
        start_ffmpeg(input_file_path, output_folder_path, config)
        count = count + 1
    return

def validate_bool(string):
    if isinstance(string, str):
        if string == "y" or string == "n":
            return True
    return False

def validate_int(integer):
    try:
        integer = int(integer)
    except Exception as e:
        print("Invalid input: type in a number")
        return False
    return integer

def collect_informations():
    while True:
        # --- input folder path ---
        while True:
            input_folder_path = Path(input("Path to your input folder: "))
            if not input_folder_path.exists:
                print("Path not valid")
                continue
            break
        
        # --- output folder path ---
        while True:
            output_folder_path = Path(input("Path to your output folder: "))
            if not output_folder_path.exists:
                print("Path not valid")
                continue
            break
        
        if file_healthcheck():
            use_profile = input("Use last used settings? [Y/n]: ")
        else:
            use_profile = "n"
        if use_profile == "Y" or use_profile == "":
            break
        
        # --- recursive ---
        while True:
            recursive = input("Recursive video search? [Y/n]: ").lower()
            result = validate_bool(recursive)
            if not result:
                print("Inavlid input.")
                continue
            break
        
        # --- resolution_x ---
        while True:
            resolution_x = input("Output resolution on the x-Axis: ")
            resolution_x = validate_int(resolution_x)
            if not resolution_x:
                print("Inavlid input.")
                continue
            break
        
        # --- resolution_y ----
        while True:
            resolution_y = input("Output resolution on the y-Axis: ")
            resolution_y = validate_int(resolution_y)
            if not resolution_y:
                print("Inavlid input.")
                continue
            break
        
        # --- video_quality ---
        while True:
            video_quality = input("Video quality (choose between 0 and 51, the lower, the better): ")
            video_quality = validate_int(video_quality)
            if not video_quality:
                print("Inavlid input.")
                continue
            break

        # --- output_fps ---
        while True:
            output_fps = input("Output FPS of the video, leave empty to take the same fps like the source: ")
            if output_fps:
                output_fps = validate_int(output_fps)
                if not output_fps:
                    print("Inavlid input.")
                    continue
            break
        
        # --- video_codec ---
        while True:
            video_codec = input("Video codec [h264/h265]: ")
            if not video_codec:
                print("Inavlid input.")
                continue
            if not video_codec == "h264" and not video_codec == "h265":
                print("Inavlid input.")
                continue
            break

        # --- audio_codec ---
        while True:
            audio_codec = input("Audio codec: ")
            if not audio_codec:
                print("Inavlid input.")
                continue
            break
        
        # --- input_video_containers ---
        while True:
            input_video_containers = input("Video containers which are going to re-encode, you can choose severeal containers separated by a , [e.g. mp4,mov]: ")
            if not input_video_containers:
                print("Inavlid input.")
                continue
            containers = [x.strip() for x in input_video_containers.split(",")]
            break

        # --- output_video_container ---
        while True:
            output_video_container = input("Output video container: ")
            if not output_video_container:
                print("Inavlid input.")
                continue
            break

        # --- output_audio_container ---
        while True:
            output_audio_container = input("Output audio container: ")
            if not output_audio_container:
                print("Inavlid input.")
                continue
            break

        # --- use_gpu ---
        while True:
            use_gpu = input("Render videos on GPU if available? [Y/n]: ").lower()
            result = validate_bool(use_gpu)
            if not result:
                print("Inavlid input.")
                continue
            break

        entries = [
            {"resolution_x": resolution_x},
            {"resolution_y": resolution_y},
            {"video_quality": video_quality},
            {"video_fps": output_fps},
            {"use_gpu": use_gpu},
            {"video_codec": video_codec},
            {"audio_codec": audio_codec},
            {"input_video_containers": containers},
            {"output_video_container": output_video_container},
            {"output_audio_container": output_audio_container}
        ]
        update_entries(entries)
    return input_folder_path, output_folder_path


def detect_gpu_vendor() -> dict:
    def run_command(cmd: list[str]) -> str | None:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode != 0:
                print(f"Command failed: {' '.join(cmd)}")
                if result.stderr.strip():
                    print(f"stderr: {result.stderr.strip()}")
                return None
            return result.stdout
        except FileNotFoundError:
            print(f"Command not found: {cmd[0]}")
            return None
        except Exception as e:
            print(f"Unexpected error while running {' '.join(cmd)}: {e}")
            return None

    def get_gpu_names() -> list[str]:
        system = platform.system().lower()

        if system == "windows":
            output = run_command([
                "powershell",
                "-Command",
                "(Get-CimInstance Win32_VideoController).Name"
            ])
            if output is None:
                print("Could not query GPUs on Windows.")
                return []
            return [line.strip() for line in output.splitlines() if line.strip()]

        if system == "linux":
            output = run_command(["lspci"])
            if output is None:
                print("Could not query GPUs on Linux. Make sure 'lspci' is installed.")
                return []

            gpu_lines = []
            for line in output.splitlines():
                lower = line.lower()
                if "vga" in lower or "3d controller" in lower or "display controller" in lower:
                    gpu_lines.append(line.strip())

            return gpu_lines

        print(f"Unsupported operating system: {platform.system()}")
        return []

    def ffmpeg_exists() -> bool:
        if shutil.which("ffmpeg") is None:
            print("ffmpeg is not installed or not in PATH.")
            return False
        return True

    def ffmpeg_has_any_gpu_support() -> bool:
        output = run_command(["ffmpeg", "-hide_banner", "-encoders"])
        if output is None:
            print("Could not read ffmpeg encoders.")
            return False

        output = output.lower()
        return any(name in output for name in [
            "h264_nvenc", "hevc_nvenc",
            "h264_amf", "hevc_amf"
        ])

    gpu_names = get_gpu_names()
    if not gpu_names:
        print("No GPU information could be detected.")
        return {
            "vendor": "cpu",
            "gpu_names": []
        }

    print("Detected GPUs:")
    for gpu in gpu_names:
        print(f" - {gpu}")

    normalized = [gpu.lower() for gpu in gpu_names]

    has_nvidia_gpu = any("nvidia" in gpu for gpu in normalized)
    has_amd_gpu = any("amd" in gpu or "radeon" in gpu for gpu in normalized)

    if not ffmpeg_exists():
        print("Falling back to CPU because ffmpeg is unavailable.")
        return {
            "vendor": "cpu",
            "gpu_names": gpu_names
        }

    if not ffmpeg_has_any_gpu_support():
        print("ffmpeg does not appear to have NVIDIA NVENC or AMD AMF support.")
        print("Falling back to CPU.")
        return {
            "vendor": "cpu",
            "gpu_names": gpu_names
        }

    if has_nvidia_gpu:
        print("NVIDIA GPU detected.")
        return {
            "vendor": "nvidia",
            "gpu_names": gpu_names
        }

    if has_amd_gpu:
        print("AMD GPU detected.")
        return {
            "vendor": "amd",
            "gpu_names": gpu_names
        }

    print("No supported NVIDIA or AMD GPU was detected.")
    print("Falling back to CPU.")
    return {
        "vendor": "cpu",
        "gpu_names": gpu_names
    }