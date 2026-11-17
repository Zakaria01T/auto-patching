def some_function():
    try:
        os.system('ls')
    except Exception as e:
        print(e)