def execute_command(user_input):
    # Split the user's input into a list of arguments
    args = shlex.split(user_input)

    # Validate and sanitize the input
    if len(args) == 1 and args[0].isalpha():
        command = "ls"
        process = subprocess.Popen([command, args[0]], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        output, error = process.communicate()

        if process.returncode != 0:
            print(f"Command failed with error: {error}")
        else:
            print(output)
    else:
        print("Invalid input. Please enter alphabetic characters only.")