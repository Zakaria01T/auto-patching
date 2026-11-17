def some_function():
    try:
        output = subprocess.check_output(['ls'])
        print(output.decode())
    except subprocess.CalledProcessError as e:
        print("An error occurred while executing the command: ", e)