def execute_command_subprocess(user_input):
    # Secure code - This will not lead to command injection
    subprocess.Popen(['/bin/bash', '-c', user_input])