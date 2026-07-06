from converter_utils import build_ffmpeg_command, run_ffmpeg_with_progress

def start_ffmpeg(file_path, input_folder_path, output_folder_path, config):
    relative_path = file_path.relative_to(input_folder_path)
    output_container = str(config.output_video_container).strip().lstrip(".")
    if not output_container:
        output_container = file_path.suffix.lstrip(".")
    output_file_path = (output_folder_path / relative_path).with_suffix(f".{output_container}")
    output_file_path.parent.mkdir(parents=True, exist_ok=True)

    result = build_ffmpeg_command(config, file_path, output_file_path)
    if result is None:
        print(f"Skipping {file_path}: could not build ffmpeg command.")
        return
    cmd, env = result
    return_code = run_ffmpeg_with_progress(cmd, file_path, env=env)
    print(f"Return code: {return_code}")
    return