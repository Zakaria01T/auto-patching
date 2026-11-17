def execute_command(command):
    try:
        # Use subprocess module instead of os.system for executing commands
        # It provides better security and control over the executed process
        subprocess.run(command, shell=True, check=True)
    except Exception as e:
        print(f"Error occurred while executing command: {e}")