def main():
    user_input = UserInput()
    user_input.get_user_input()
    # Escape user input to prevent command injection
    escaped_user_input = shlex.quote(user_input.user_input)
    os.system("echo " + escaped_user_input)