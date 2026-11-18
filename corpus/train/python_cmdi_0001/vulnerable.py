def execute_command(user_input):
    command = "echo %s > myfile.txt" % (user_input)
    os.system(command)