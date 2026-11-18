def get_pod(namespace, pod):
    import subprocess
    cmd = "kubectl get pod -n {} {} -o json".format(namespace, pod)
    return subprocess.check_output(cmd, shell=True, text=True)
