@app.route('/execute', methods=['POST'])
def execute_command():
    command = request.form.get('command')

    # Validate the command
    if re.match(COMMAND_REGEX, command):
        # Execute the command safely
        subprocess.call(command, shell=True)
        return 'Command executed'
    else:
        return 'Invalid command', 400