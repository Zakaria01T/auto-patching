def get_pod(namespace, pod):
    import subprocess
    output = subprocess.check_output(["kubectl", "get", "pod", "-n", namespace, "-o", "json", "--", pod], text=True)
    return output
