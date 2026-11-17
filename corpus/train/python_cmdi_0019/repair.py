def execute_command(user_input):
    # Sanitize the user input
    sanitized_input = shlex.quote(user_input)
    command = "ls " + sanitized_input
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(result.stdout)