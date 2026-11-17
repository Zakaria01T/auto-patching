def execute_user_input():
    user_input = input("Enter your command: ")
    # Validate and sanitize user input
    if all(c.isalnum() or c.isspace() for c in user_input):
        try:
            # Use subprocess instead of os.system for better security
            subprocess.run(user_input, shell=True, check=True)
        except Exception as e:
            print('Error:', e)
    else:
        print('Invalid input')