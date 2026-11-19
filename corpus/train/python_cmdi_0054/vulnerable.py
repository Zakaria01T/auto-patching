def copy_artifact(src: str, dst: str) -> None:
    import subprocess
    subprocess.call("cp %s %s" % (src, dst), shell=True)