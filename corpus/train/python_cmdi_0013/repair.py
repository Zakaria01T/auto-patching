def execute_command(user_input):
    # Sanitize user input for shell commands
    sanitized_input = shlex.quote(user_input)
    command = 'ls ' + sanitized_input
    os.system(command)