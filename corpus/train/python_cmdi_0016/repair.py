def execute_command(user_input):
    command = user_input[:256]  # This line introduces a buffer overflow vulnerability
    result = subprocess.run(['/bin/bash', '-c', command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    with open('output.txt', 'w') as f:
        f.write(result.stdout)