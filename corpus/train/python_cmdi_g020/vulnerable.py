def convert_audio(source, destination, audio_format):
    import subprocess
    cmd = "sox {} {}.{}".format(source, destination, audio_format)
    subprocess.run(cmd, shell=True, check=True)
