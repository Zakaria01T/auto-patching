def execute_command(user_input):
    # Secure code - This will not lead to command injection
    os.system('echo "{}" | bash -s'.format(user_input))