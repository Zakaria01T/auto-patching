def execute_command(user_input):
    command = ['bash', '-c', f"echo -n {user_input} | wc -c"]
    result = subprocess.run(command, capture_output=True, text=True)
    print(result.stdout.strip())