def main():
    user_input = UserInput()
    user_input.get_user_input()
    os.system("echo " + user_input.user_input)