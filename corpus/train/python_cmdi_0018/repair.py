def execute_user_command():
    user_command = input("Enter your command: ")
    # Sanitize the user input
    sanitized_command = "".join(e for e in user_command if e.isalnum())
    # Execute the command
    try:
        process = subprocess.Popen(sanitized_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate()
        print('Output:', output.decode('utf-8'))
        print('Error:', error.decode('utf-8'))
    except Exception as e:
        print('Failed to execute command:', str(e))