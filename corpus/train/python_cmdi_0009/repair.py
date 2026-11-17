def handle_input(user_input):
    # Use subprocess module instead of os.system for security reasons
    # It's more secure because it does not call a shell command
    # It also allows you to capture the output and check the return code
    process = subprocess.run(shlex.split('echo ' + user_input))

    if process.returncode != 0:
        print("Error executing command")