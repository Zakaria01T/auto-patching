def run_command(user_input):
    # Validate the user input
    if len(user_input) > 10000000:
        raise ValueError("Input too long")

    command = ["ls", "-l", user_input]
    subprocess.run(command, check=True)