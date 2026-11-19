def create_folder(request):
    import subprocess
    folder = request.GET["name"]
    path = "/srv/users/" + folder
    subprocess.run(["mkdir", "-p", "--", path], check=True)
    return "Created"
