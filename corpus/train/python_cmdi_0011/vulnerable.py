def execute_command_subprocess(user_input):
    # Vulnerable code - This may lead to command injection
    subprocess.Popen(user_input, shell=True)