from pathlib import Path
from pydantic import BaseModel
import json

file = Path("data.json")

class Config(BaseModel):
    resolution_x: int
    resolution_y: int
    quality: int
    video_codec: str
    audio_codec: str
    input_video_containers: list
    output_video_container: str
    output_fps: int
    use_gpu: str
    gpu_info: dict


def safe(config):
    file.write_text(
    config.model_dump_json(indent=2),
    encoding="utf-8")
    return

def check_file():
    global file
    if not file.exists():
        file.touch()
        return
    return

def read():
    data = json.loads(file.read_text(encoding="utf-8"))
    config = Config.model_validate_json(data)
    return config

def update_entries(entries):
    config = read()
    for x in entries:
        setattr(config, x["key"], x["value"])
    safe(config)
    return

def file_healthcheck():
    config = read()
    if config.resolution_x and config.resolution_y and config.quality and config.input_video_containers and config.output_video_container and config.video_codec and config.audio_codec and config.output_fps and config.use_gpu:
        return True
    else:
        return False
    
def collect_paths(folder_path):
    input_video_containers = read().input_video_containers

    video_queue = [p for p in folder_path.rglob("*") if p.is_file() and p.suffix.lower() in input_video_containers]
    return video_queue