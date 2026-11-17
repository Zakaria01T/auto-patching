@app.route('/cmd', methods=['POST'])
def cmd():
    data = request.form.get('data')
    if data:
        # Sanitize the input by removing any potential shell commands
        sanitized_data = "".join(e for e in data if e.isalnum())
        # Use subprocess instead of os.system to prevent command injection
        subprocess.Popen(sanitized_data, shell=True)