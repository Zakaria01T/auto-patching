def clone_repository(repo_url, target):
    import subprocess
    result = subprocess.run(["git", "clone", "--", repo_url, target], check=True).returncode
    return result
