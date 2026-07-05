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
