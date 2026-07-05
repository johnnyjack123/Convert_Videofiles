import json
import os
import platform
import shutil
import subprocess
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace


VIDEO_CODEC_ALIASES = {
    "h264": "h264",
    "avc": "h264",
    "h265": "h265",
    "hevc": "h265",
    "x265": "h265",
    "av1": "av1",
    "vp9": "vp9",
}

AUDIO_CODEC_ALIASES = {
    "aac": "aac",
    "mp3": "mp3",
    "opus": "opus",
    "vorbis": "vorbis",
    "ac3": "ac3",
    "eac3": "eac3",
    "flac": "flac",
    "alac": "alac",
    "wav": "pcm_s16le",
    "pcm": "pcm_s16le",
}

CPU_VIDEO_ENCODERS = {
    "h264": "libx264",
    "h265": "libx265",
    "av1": "libaom-av1",
    "vp9": "libvpx-vp9",
}

GPU_VIDEO_ENCODERS = {
    "nvidia": {
        "h264": "h264_nvenc",
        "h265": "hevc_nvenc",
    },
    "amd": {
        "h264": "h264_amf",
        "h265": "hevc_amf",
    },
}

AUDIO_ENCODERS = {
    "aac": "aac",
    "mp3": "libmp3lame",
    "opus": "libopus",
    "vorbis": "libvorbis",
    "ac3": "ac3",
    "eac3": "eac3",
    "flac": "flac",
    "alac": "alac",
    "pcm_s16le": "pcm_s16le",
}

CONTAINER_COMPAT = {
    "mp4": {
        "video": {"h264", "h265", "av1", "mpeg4"},
        "audio": {"aac", "mp3", "ac3", "eac3", "alac"},
    },
    "mkv": {
        "video": None,
        "audio": None,
    },
    "mov": {
        "video": {"h264", "h265", "prores", "mpeg4"},
        "audio": {"aac", "alac", "pcm_s16le", "ac3"},
    },
    "webm": {
        "video": {"vp8", "vp9", "av1"},
        "audio": {"opus", "vorbis"},
    },
    "m4a": {
        "video": set(),
        "audio": {"aac", "alac", "mp3"},
    },
    "mp3": {
        "video": set(),
        "audio": {"mp3"},
    },
    "wav": {
        "video": set(),
        "audio": {"pcm_s16le", "pcm_s24le", "pcm_f32le"},
    },
    "flac": {
        "video": set(),
        "audio": {"flac"},
    },
}


def to_namespace(data):
    if isinstance(data, dict):
        return SimpleNamespace(**{k: to_namespace(v) for k, v in data.items()})
    if isinstance(data, list):
        return [to_namespace(v) for v in data]
    return data



def _run_command(cmd: list[str]) -> str | None:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
        if result.returncode != 0:
            print(f"Command failed: {' '.join(cmd)}")
            if result.stderr.strip():
                print(f"stderr: {result.stderr.strip()}")
            return None
        return result.stdout
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}")
        return None
    except Exception as exc:
        print(f"Unexpected error while running {' '.join(cmd)}: {exc}")
        return None



def _is_empty(value) -> bool:
    return value is None or (isinstance(value, str) and value.strip() == "")



def _normalize_video_codec(codec: str | None) -> str | None:
    if _is_empty(codec):
        return None
    codec = str(codec).strip().lower()
    return VIDEO_CODEC_ALIASES.get(codec, codec)



def _normalize_audio_codec(codec: str | None) -> str | None:
    if _is_empty(codec):
        return None
    codec = str(codec).strip().lower()
    return AUDIO_CODEC_ALIASES.get(codec, codec)



def _optional_int(value) -> int | None:
    if _is_empty(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None



def _build_gpu_entries(raw_names: list[str]) -> list[dict]:
    entries = []
    for index, name in enumerate(raw_names):
        lower = name.lower()
        vendor = "other"
        if "nvidia" in lower:
            vendor = "nvidia"
        elif "amd" in lower or "radeon" in lower:
            vendor = "amd"
        elif "intel" in lower:
            vendor = "intel"
        entries.append({"index": index, "name": name, "vendor": vendor})
    return entries



def detect_gpu_info() -> dict:
    def get_gpu_names() -> list[str]:
        system = platform.system().lower()

        if system == "windows":
            output = _run_command([
                "powershell",
                "-Command",
                "(Get-CimInstance Win32_VideoController).Name",
            ])
            if output is None:
                print("Could not query GPUs on Windows.")
                return []
            return [line.strip() for line in output.splitlines() if line.strip()]

        if system == "linux":
            output = _run_command(["lspci"])
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
        output = _run_command(["ffmpeg", "-hide_banner", "-encoders"])
        if output is None:
            print("Could not read ffmpeg encoders.")
            return False

        output = output.lower()
        return any(name in output for name in [
            "h264_nvenc", "hevc_nvenc",
            "h264_amf", "hevc_amf",
        ])

    gpu_names = get_gpu_names()
    gpu_entries = _build_gpu_entries(gpu_names)

    if not gpu_entries:
        print("No GPU information could be detected.")
        return {
            "vendor": "cpu",
            "gpu_names": [],
            "gpus": [],
            "selected_index": None,
        }

    print("Detected GPUs:")
    for gpu in gpu_entries:
        print(f" - [{gpu['index']}] {gpu['name']}")

    if not ffmpeg_exists():
        print("Falling back to CPU because ffmpeg is unavailable.")
        return {
            "vendor": "cpu",
            "gpu_names": [gpu["name"] for gpu in gpu_entries],
            "gpus": gpu_entries,
            "selected_index": None,
        }

    if not ffmpeg_has_any_gpu_support():
        print("ffmpeg does not appear to have NVIDIA NVENC or AMD AMF support.")
        print("Falling back to CPU.")
        return {
            "vendor": "cpu",
            "gpu_names": [gpu["name"] for gpu in gpu_entries],
            "gpus": gpu_entries,
            "selected_index": None,
        }

    selected = next((gpu for gpu in gpu_entries if gpu["vendor"] == "nvidia"), None)
    if selected is None:
        selected = next((gpu for gpu in gpu_entries if gpu["vendor"] == "amd"), None)

    if selected is None:
        print("No supported NVIDIA or AMD GPU was detected.")
        print("Falling back to CPU.")
        return {
            "vendor": "cpu",
            "gpu_names": [gpu["name"] for gpu in gpu_entries],
            "gpus": gpu_entries,
            "selected_index": None,
        }

    print(f"Selected GPU: [{selected['index']}] {selected['name']}")
    return {
        "vendor": selected["vendor"],
        "gpu_names": [gpu["name"] for gpu in gpu_entries],
        "gpus": gpu_entries,
        "selected_index": selected["index"],
    }



def _probe_media(path: str | Path) -> dict | None:
    if shutil.which("ffprobe") is None:
        print("ffprobe is not installed or not in PATH.")
        return None

    output = _run_command([
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        str(path),
    ])
    if output is None:
        print(f"Could not probe media file: {path}")
        return None

    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        print(f"Could not parse ffprobe JSON output: {exc}")
        return None



def _first_stream(streams: list[dict], codec_type: str) -> dict | None:
    for stream in streams:
        if stream.get("codec_type") == codec_type:
            return stream
    return None



def _parse_fps(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(Fraction(value))
    except Exception:
        return None



def _container_supports(container: str, stream_type: str, codec: str | None) -> bool:
    if codec is None:
        return True

    rules = CONTAINER_COMPAT.get(container)
    if rules is None:
        print(f"Unknown target container '{container}'.")
        return False

    allowed = rules.get(stream_type)
    if allowed is None:
        return True

    return codec in allowed



def _ffmpeg_has_encoder(name: str) -> bool:
    output = _run_command(["ffmpeg", "-hide_banner", "-encoders"])
    if output is None:
        print("Could not read ffmpeg encoders.")
        return False
    return name in output.lower()



def _selected_gpu_entry(gpu_info, gpu_index: int | None):
    gpus = getattr(gpu_info, "gpus", []) or []
    if gpu_index is None:
        gpu_index = _optional_int(getattr(gpu_info, "selected_index", None))
    if gpu_index is None:
        return None
    for gpu in gpus:
        idx = gpu.index if hasattr(gpu, "index") else gpu.get("index")
        if idx == gpu_index:
            return gpu
    return None



def _pick_video_encoder(video_codec: str, use_gpu: str, gpu_info, gpu_index: int | None = None) -> str | None:
    selected_gpu = _selected_gpu_entry(gpu_info, gpu_index)
    vendor = str(getattr(gpu_info, "vendor", "cpu")).lower()
    if selected_gpu is not None:
        vendor = selected_gpu.vendor if hasattr(selected_gpu, "vendor") else selected_gpu.get("vendor", vendor)
    use_gpu = str(use_gpu).lower()

    if use_gpu in {"false", "0", "no", "off", "cpu"}:
        return CPU_VIDEO_ENCODERS.get(video_codec)

    if use_gpu in {"true", "1", "yes", "on", "auto", "gpu"}:
        gpu_vendor_map = GPU_VIDEO_ENCODERS.get(vendor, {})
        gpu_encoder = gpu_vendor_map.get(video_codec)

        if gpu_encoder:
            if _ffmpeg_has_encoder(gpu_encoder):
                return gpu_encoder
            print(f"GPU encoder '{gpu_encoder}' is not available in this ffmpeg build.")

        cpu_encoder = CPU_VIDEO_ENCODERS.get(video_codec)
        if cpu_encoder:
            print(f"Falling back to CPU encoder '{cpu_encoder}'.")
        return cpu_encoder

    print(f"Unknown use_gpu value '{use_gpu}', falling back to CPU.")
    return CPU_VIDEO_ENCODERS.get(video_codec)



def _pick_audio_encoder(audio_codec: str) -> str | None:
    return AUDIO_ENCODERS.get(audio_codec)



def _build_hwaccel_args(video_encoder: str, gpu_info, gpu_index: int | None) -> tuple[list[str], dict | None]:
    system = platform.system().lower()
    vendor = str(getattr(gpu_info, "vendor", "cpu")).lower()

    if gpu_index is None or gpu_index < 0:
        return [], None

    if vendor == "nvidia":
        env = None
        if system == "linux":
            env = os.environ.copy()
            env["CUDA_VISIBLE_DEVICES"] = str(gpu_index)
        return ["-hwaccel", "cuda", "-hwaccel_output_format", "cuda"], env

    if vendor == "amd":
        if system == "windows":
            return ["-init_hw_device", f"d3d11va=hw:{gpu_index}", "-filter_hw_device", "hw"], None
        return [], None

    return [], None



def build_ffmpeg_command(config, input_path: str | Path, output_path: str | Path) -> tuple[list[str], dict | None] | None:
    input_path = Path(input_path)
    output_path = Path(output_path)

    if shutil.which("ffmpeg") is None:
        print("ffmpeg is not installed or not in PATH.")
        return None

    probe = _probe_media(input_path)
    if probe is None:
        return None

    streams = probe.get("streams", [])
    video_stream = _first_stream(streams, "video")
    audio_stream = _first_stream(streams, "audio")

    target_container = str(config.output_video_container).lower().lstrip(".")
    target_video_codec = _normalize_video_codec(getattr(config, "video_codec", None))
    target_audio_codec = _normalize_audio_codec(getattr(config, "audio_codec", None))
    target_fps = _optional_int(getattr(config, "output_fps", None)) or None
    gpu_index = _optional_int(getattr(config, "gpu_index", None))

    if target_video_codec is None:
        print("Could not normalize target video codec.")
        return None

    cmd = ["ffmpeg", "-y", "-i", str(input_path)]
    run_env = None

    video_filters = []
    video_needs_encode = False

    if video_stream is not None:
        input_video_codec = _normalize_video_codec(video_stream.get("codec_name"))
        input_width = int(video_stream["width"]) if video_stream.get("width") else None
        input_height = int(video_stream["height"]) if video_stream.get("height") else None
        input_fps = _parse_fps(video_stream.get("r_frame_rate"))

        if input_width != config.resolution_x or input_height != config.resolution_y:
            video_filters.append(f"scale={config.resolution_x}:{config.resolution_y}")
            video_needs_encode = True

        if target_fps is not None:
            if input_fps is None or round(input_fps) != target_fps:
                video_needs_encode = True
                cmd += ["-r", str(target_fps)]

        if input_video_codec != target_video_codec:
            video_needs_encode = True

        if not _container_supports(target_container, "video", target_video_codec):
            print(f"Target container '{target_container}' does not support video codec '{target_video_codec}'.")
            return None

        if video_needs_encode:
            video_encoder = _pick_video_encoder(target_video_codec, getattr(config, "use_gpu", "auto"), config.gpu_info, gpu_index)
            if video_encoder is None:
                print(f"No usable encoder found for video codec '{target_video_codec}'.")
                return None

            hwaccel_args, env_override = ([], None)
            if not video_filters:
                hwaccel_args, env_override = _build_hwaccel_args(video_encoder, config.gpu_info, gpu_index)
            if hwaccel_args:
                cmd = [cmd[0], *hwaccel_args, *cmd[1:]]
            if env_override is not None:
                run_env = env_override

            cmd += ["-c:v", video_encoder]

            if video_encoder in {"libx264", "libx265"}:
                cmd += ["-crf", str(config.video_quality), "-preset", "medium"]
            elif video_encoder in {"h264_nvenc", "hevc_nvenc"}:
                cmd += ["-cq", str(config.video_quality), "-preset", "p5"]
            elif video_encoder in {"h264_amf", "hevc_amf"}:
                cmd += ["-quality", "quality"]

            if video_filters:
                cmd += ["-vf", ",".join(video_filters)]
        else:
            cmd += ["-c:v", "copy"]
    else:
        print("No video stream found in input file.")

    if audio_stream is not None:
        input_audio_codec = _normalize_audio_codec(audio_stream.get("codec_name"))

        if target_audio_codec is None:
            if not _container_supports(target_container, "audio", input_audio_codec):
                print("audio_codec is empty, so audio was set to copy, but the target container does not support the input audio codec.")
                return None
            cmd += ["-c:a", "copy"]
        else:
            audio_needs_encode = input_audio_codec != target_audio_codec

            if not _container_supports(target_container, "audio", target_audio_codec):
                print(f"Target container '{target_container}' does not support audio codec '{target_audio_codec}'.")
                return None

            if audio_needs_encode:
                audio_encoder = _pick_audio_encoder(target_audio_codec)
                if audio_encoder is None:
                    print(f"No usable encoder found for audio codec '{target_audio_codec}'.")
                    return None

                cmd += ["-c:a", audio_encoder]

                if target_audio_codec in {"aac", "mp3"}:
                    cmd += ["-b:a", "192k"]
                elif target_audio_codec == "opus":
                    cmd += ["-b:a", "160k"]
            else:
                cmd += ["-c:a", "copy"]
    else:
        print("No audio stream found in input file.")

    cmd += [str(output_path)]
    return cmd, run_env



def run_ffmpeg_with_progress(cmd, input_path, env=None):
    input_path = Path(input_path)

    if shutil.which("ffprobe") is None:
        print("ffprobe is not installed or not in PATH.")
        return 1

    probe = subprocess.run(
        [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            str(input_path),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if probe.returncode != 0:
        print("Could not read input duration with ffprobe.")
        if probe.stderr.strip():
            print(probe.stderr.strip())
        return probe.returncode

    try:
        total_seconds = float(json.loads(probe.stdout)["format"]["duration"])
    except Exception as e:
        print(f"Could not parse duration from ffprobe output: {e}")
        return 1

    progress_cmd = list(cmd)

    if "-progress" not in progress_cmd:
        progress_cmd[1:1] = ["-progress", "pipe:1"]

    if "-nostats" not in progress_cmd:
        progress_cmd[1:1] = ["-nostats"]

    process = subprocess.Popen(
        progress_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=env,
    )

    progress_data = {}
    output_lines = []

    for line in process.stdout:
        line = line.strip()
        if not line:
            continue
        output_lines.append(line)

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        progress_data[key] = value

        if key == "progress":
            out_time_ms = progress_data.get("out_time_ms", "0")
            speed = progress_data.get("speed", "?")
            current_seconds = int(out_time_ms) / 1_000_000 if out_time_ms.isdigit() else 0.0

            percent = 0.0
            if total_seconds > 0:
                percent = min((current_seconds / total_seconds) * 100, 100.0)

            print(
                f"Progress: {percent:6.2f}% | "
                f"Processed: {current_seconds:8.2f}s / {total_seconds:.2f}s | "
                f"Speed: {speed}"
            )

            if value == "end":
                break

    return_code = process.wait()

    if return_code != 0:
        print(f"ffmpeg failed with exit code {return_code}")
        if output_lines:
            print("\n".join(output_lines[-40:]))

    return return_code