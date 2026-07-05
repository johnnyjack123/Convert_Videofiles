from pathlib import Path
from pydantic import BaseModel, Field
import json

file = Path("data.json")

class GPUInfo(BaseModel):
    vendor: str = "cpu"
    gpu_names: list[str] = Field(default_factory=list)

class Config(BaseModel):
    resolution_x: int = 0
    resolution_y: int = 0
    video_quality: int = 0
    video_codec: str = ""
    audio_codec: str = ""
    input_video_containers: list = []
    output_video_container: str = ""
    output_fps: int = 0
    use_gpu: bool = True
    gpu_info: GPUInfo = Field(default_factory=GPUInfo)
    gpu_index: int = -1

def save(config):
    global file
    file.write_text(
    config.model_dump_json(indent=2),
    encoding="utf-8")
    return

def check_file():
    global file
    if not file.exists():
        config = Config()
        file.write_text(config.model_dump_json(indent=4), encoding="utf-8")
        return
    return

def read():
    global file
    data = json.loads(file.read_text(encoding="utf-8"))
    config = Config.model_validate(data)
    return config

def update_entries(entries):
    config = read()
    for key, value in entries.items():
        setattr(config, key, value)
    save(config)
    return

def file_healthcheck():
    config = read()
    if config.resolution_x and config.resolution_y and config.quality and config.input_video_containers and config.output_video_container and config.video_codec and config.audio_codec and config.output_fps and config.use_gpu and config.gpu_index:
        return True
    else:
        return False
    
def collect_paths(folder_path):
    print("Collect paths.")
    input_video_containers = read().input_video_containers

    video_queue = [p for p in folder_path.rglob("*") if p.is_file() and p.suffix.lower() in input_video_containers]
    return video_queue