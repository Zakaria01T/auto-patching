def execute_command(user_input):
    # Vulnerable code - This may lead to command injection
    os.system(user_input)