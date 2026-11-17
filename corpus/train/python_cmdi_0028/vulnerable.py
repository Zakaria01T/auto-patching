@app.route('/execute', methods=['POST'])
def execute_command():
    command = request.form.get('command')
    os.system(command)
    return 'Command executed'