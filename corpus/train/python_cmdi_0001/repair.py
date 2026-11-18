def execute_command(user_input):
    with open('myfile.txt', 'w') as f:
        f.write(user_input)