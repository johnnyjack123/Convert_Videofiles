from converter_utils import build_ffmpeg_command, run_ffmpeg_with_progress

def start_ffmpeg(file_path, output_folder_path, config):
    cmd = build_ffmpeg_command(config, file_path, output_folder_path)
    return_code = run_ffmpeg_with_progress(cmd, file_path)
    print(f"Return code: {return_code}")
    return