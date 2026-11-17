def execute_command():
    command = input("Enter your command: ")
    try:
        subprocess.run(command, shell=True, check=True)
    except Exception as e:
        print(f"Error executing command: {e}")