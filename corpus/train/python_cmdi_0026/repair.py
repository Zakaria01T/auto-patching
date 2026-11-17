def run_command(user_input):
    command = ['ls', user_input]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Command execution failed with error: {e}")