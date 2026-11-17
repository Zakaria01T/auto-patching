def run_command(user_input):
    # Sanitize user input
    sanitized_input = user_input.replace(';', '').replace('&', '').replace('|', '')
    command = f"echo Hello, {sanitized_input}"
    subprocess.call(command, shell=True)