def execute_command(user_input):
    command = "ls " + user_input
    process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    output = process.communicate()[0]
    return output