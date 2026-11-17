def execute_command(user_input):
    allowed_commands = ['ls', 'pwd']  # Add all allowed commands here
    if user_input in allowed_commands:
        command = user_input
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output, error = process.communicate()
            print(output.decode('utf-8'))
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("Command not allowed.")