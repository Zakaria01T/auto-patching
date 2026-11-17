def execute_command(user_input):
    command = 'echo -n ' + user_input + ' | wc -c'
    os.system(command)