def execute_command(user_input):
    command = user_input[:256]  # This line introduces a buffer overflow vulnerability
    os.system("echo '{}' > output.txt".format(command))