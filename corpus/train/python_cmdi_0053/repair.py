def inspect_document_path(path):
    import subprocess
    return subprocess.check_output(["file", "--", path], text=True)