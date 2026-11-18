def convert_audio(source, destination, audio_format):
    import subprocess
    if audio_format not in {"mp3", "wav", "ogg", "flac"}:
        raise ValueError("unsupported audio format")
    subprocess.run(["sox", "--", source, f"{destination}.{audio_format}"], check=True)
