from pathlib import Path
from file_handler import file_healthcheck, read, update_entries, collect_paths
from converter import start_ffmpeg
from globals import VIDEO_CODEC_ALIASES, AUDIO_CODEC_ALIASES, CONTAINER_COMPAT
import platform
import shutil
import subprocess

VIDEO_CODEC_OPTIONS = "/".join(sorted(VIDEO_CODEC_ALIASES.keys()))
AUDIO_CODEC_OPTIONS = "/".join(sorted(AUDIO_CODEC_ALIASES.keys()))
CONTAINER_OPTIONS = "/".join(sorted(CONTAINER_COMPAT.keys()))

def print_config():
    config = read()
    print(config.model_dump_json(indent=4))
    return

def process_queue(video_queue, input_folder_path, output_folder_path):
    config = read()
    videos = len(video_queue)
    count = 1
    for input_file_path in video_queue:
        print(f"Video {count} of {videos}.")
        start_ffmpeg(input_file_path, input_folder_path, output_folder_path, config)
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
            input_folder_path = Path(input("Path to your input folder [existing folder]: "))
            if not input_folder_path.exists():
                print("Path not valid")
                continue
            break

        # --- output folder path ---
        while True:
            output_folder_path = Path(input("Path to your output folder [created automatically if missing]: "))
            break

        if file_healthcheck():
            use_profile = input("Use last used settings? [Y/n]: ").strip().lower()
        else:
            use_profile = "n"
        if use_profile == "y" or use_profile == "":
            break

        # --- resolution_x / resolution_y ---
        while True:
            resolution_x_raw = input("Output resolution on the x-Axis [e.g. 1920, leave empty to keep source resolution]: ")
            if not resolution_x_raw:
                resolution_x, resolution_y = 0, 0
                break
            resolution_x = validate_int(resolution_x_raw)
            if not resolution_x:
                continue
            resolution_y_raw = input("Output resolution on the y-Axis [e.g. 1080]: ")
            resolution_y = validate_int(resolution_y_raw)
            if not resolution_y:
                print("Invalid input.")
                continue
            break

        # --- video_quality ---
        while True:
            video_quality = input("Video quality [0-51, the lower, the better]: ")
            video_quality = validate_int(video_quality)
            if not video_quality:
                continue
            break

        # --- output_fps ---
        while True:
            output_fps = input("Output FPS of the video [e.g. 30, leave empty to take the same fps like the source]: ")
            if output_fps:
                output_fps = validate_int(output_fps)
                if not output_fps:
                    continue
            else:
                output_fps = 0
            break

        # --- video_codec ---
        while True:
            video_codec = input(f"Video codec [{VIDEO_CODEC_OPTIONS}, leave empty to keep source codec]: ").strip().lower()
            if not video_codec:
                break
            normalized_video_codec = VIDEO_CODEC_ALIASES.get(video_codec)
            if normalized_video_codec is None:
                print("Invalid input.")
                continue
            video_codec = normalized_video_codec
            break

        # --- audio_codec ---
        while True:
            audio_codec = input(f"Audio codec [{AUDIO_CODEC_OPTIONS}, leave empty to keep source codec]: ").strip().lower()
            if not audio_codec:
                break
            normalized_audio_codec = AUDIO_CODEC_ALIASES.get(audio_codec)
            if normalized_audio_codec is None:
                print("Invalid input.")
                continue
            audio_codec = normalized_audio_codec
            break

        # --- input_video_containers ---
        while True:
            input_video_containers = input(f"Video containers which are going to re-encode, you can choose several containers separated by a , [{CONTAINER_OPTIONS}]: ")
            if not input_video_containers:
                print("Invalid input.")
                continue
            containers = [x.strip().lower().lstrip(".") for x in input_video_containers.split(",")]
            invalid_containers = [c for c in containers if c not in CONTAINER_COMPAT]
            if invalid_containers:
                print(f"Invalid container(s): {', '.join(invalid_containers)}. Choose from: {CONTAINER_OPTIONS}")
                continue
            break

        # --- output_video_container ---
        while True:
            output_video_container = input(f"Output video container [{CONTAINER_OPTIONS}, leave empty to keep source container]: ").strip().lower().lstrip(".")
            if not output_video_container:
                break
            if output_video_container not in CONTAINER_COMPAT:
                print(f"Invalid container. Choose from: {CONTAINER_OPTIONS}")
                continue
            break

        # --- use_gpu ---
        while True:
            use_gpu = input("Render videos on GPU if available? [Y/n]: ").lower()
            if use_gpu:
                result = validate_bool(use_gpu)
                if not result:
                    print("Invalid input.")
                    continue
                if use_gpu == "y":
                    use_gpu = True
                else:
                    use_gpu = False
            else:
                use_gpu = True
            break

        entries = {
            "resolution_x": resolution_x,
            "resolution_y": resolution_y,
            "video_quality": video_quality,
            "output_fps": output_fps,
            "use_gpu": use_gpu,
            "video_codec": video_codec,
            "audio_codec": audio_codec,
            "input_video_containers": containers,
            "output_video_container": output_video_container,
            "configured": True,
        }

        update_entries(entries)
        break
    return input_folder_path, output_folder_path


def detect_gpu_vendor() -> dict:
    def run_command(cmd: list[str]) -> str | None:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
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