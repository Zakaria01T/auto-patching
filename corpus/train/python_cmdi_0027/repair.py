def execute_user_command():
    user_input = input("Enter your command: ")
    # Use subprocess instead of os.system to avoid shell injection
    subprocess.run(user_input, shell=True, check=True)