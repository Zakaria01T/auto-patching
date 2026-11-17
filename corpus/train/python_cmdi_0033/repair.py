def execute_command(user_input):
    # Sanitize the user input
    sanitized_input = shlex.split(user_input)

    # Validate the sanitized input
    if len(sanitized_input) == 0:
        print("Invalid command")
        return

    try:
        # Use subprocess.run instead of subprocess.Popen for simplicity and security
        result = subprocess.run(sanitized_input, capture_output=True, text=True, check=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Command execution failed: {e}")