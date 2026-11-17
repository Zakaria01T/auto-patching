def run_command(user_input):
    command = "ls -l " + user_input
    os.system(command)