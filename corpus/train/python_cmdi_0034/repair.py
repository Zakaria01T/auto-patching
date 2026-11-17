def vulnerable_function(user_input):
    command = "echo " + shlex.quote(user_input) + " > /dev/null"
    os.system(command)