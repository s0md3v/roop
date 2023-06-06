from flask import Flask, request, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import os
import threading
import subprocess
from flask import render_template

import queue
import uuid
import stat

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/home/ivo/roop2/roop/uploads'


task_queue = queue.Queue()
task_status = {}

# Esta funcion corre en un hilo separado para procesar las solicitudes en la queue
def worker():
    while True:
        task = task_queue.get()
        if task is None:
            break
        user_id, face_path, target_path, output_path = task
        run_script(face_path, target_path, output_path)
        # Cambia el estado de la tarea a 'done' cuando se ha completado
        task_status[user_id] = output_path
        task_queue.task_done()

# worker en un hilo separado
threading.Thread(target=worker, daemon=True).start()

@app.route('/')
def home():
    return render_template('index.html')

def run_script(face_path, target_path, output_path):
    cmd = [
        'python', '/home/ivo/roop2/roop/run.py',
        '-f', face_path,
        '-t', target_path,
        '-o', output_path,
        '--gpu'
    ]
    subprocess.run(cmd)
    # Cambiar los permisos
    os.chmod(output_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'face' not in request.files or 'target' not in request.files:
        return 'No file part'

    face_file = request.files['face']
    target_file = request.files['target']

    if face_file.filename == '' or target_file.filename == '':
        return 'No selected file'

    # Asignación de un userID único
    user_id = str(uuid.uuid4())

    face_filename = user_id + '_' + secure_filename(face_file.filename)
    target_filename = user_id + '_' + secure_filename(target_file.filename)
    
    face_path = os.path.join(app.config['UPLOAD_FOLDER'], face_filename)
    target_path = os.path.join(app.config['UPLOAD_FOLDER'], target_filename)

    face_file.save(face_path)
    target_file.save(target_path)

    output_filename = user_id + '_output_' + secure_filename(target_file.filename)
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

    # Agrega la tarea a la cola
    task_queue.put((user_id, face_path, target_path, output_path))
    # Establece el estado inicial de la tarea
    task_status[user_id] = 'processing'

    return jsonify(user_id=user_id, output_file=output_filename)

@app.route('/status/<user_id>')
def task_status_route(user_id):
    if user_id in task_status:
        if task_status[user_id] == 'processing':
            return 'processing'
        else:
            return '/output/' + os.path.basename(task_status[user_id])
    else:
        return 'No task found for this user id', 404

@app.route('/output/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run()
