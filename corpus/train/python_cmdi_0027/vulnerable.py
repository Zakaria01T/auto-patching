def open_link(url):
    import subprocess
    subprocess.Popen("xdg-open " + url, shell=True)