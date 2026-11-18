def create_folder(request):
    import os
    folder = request.GET["name"]
    cmd = "mkdir -p /srv/users/" + folder
    os.system(cmd)
    return "Created"
