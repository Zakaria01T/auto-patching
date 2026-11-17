def execute_command(user_input):
    if len(user_input) > 256: # arbitrary limit, adjust as needed
        raise ValueError('Input too long')
    command = ["ls", "-l", user_input]
    subprocess.run(command, check=True)