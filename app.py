import os
import random
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "jd_tech_secreto_seguro_2026"

# Configuración para subida de fotos (evita errores si no existe la carpeta)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Base de datos simulada en memoria con todos los campos detallados
ordenes_db = [
    {
        "id": "ORD-501",
        "cliente": "Juan Naranjo",
        "cedula": "1015074219",
        "telefono": "313 5760462",
        "equipo": "Samsung A34",
        "imei": "3534343332",
        "problema": "Cambio de pantalla",
        "costo_rep": "58000",
        "costo_total": "120000",
        "estado": "Recibido",
        "foto": ""
    }
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/estado', methods=['GET', 'POST'])
def estado():
    ordenes = []
    error = None
    if request.method == 'POST':
        busqueda = request.form.get('busqueda', '').strip().lower()
        ordenes = [
            o for o in ordenes_db 
            if busqueda in o['cedula'].lower() or busqueda in o['cliente'].lower() or busqueda in o['id'].lower()
        ]
        if not ordenes:
            error = "No se encontró ninguna orden con ese número de cédula, nombre o código."
            
    return render_template('estado.html', ordenes=ordenes, error=error)

@app.route('/login-admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == "301023":
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash("Contraseña incorrecta", "danger")
            
    return render_template('login_admin.html')

@app.route('/admin', methods=['GET'])
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('login_admin'))
    return render_template('admin.html', ordenes=ordenes_db)

@app.route('/crear-orden', methods=['POST'])
def crear_orden():
    try:
        nuevo_id = f"ORD-{random.randint(500, 999)}"
        
        # Manejo de archivo de imagen si se adjunta
        foto_filename = ""
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                foto_filename = filename

        nueva_orden = {
            "id": nuevo_id,
            "cliente": request.form.get('cliente'),
            "cedula": request.form.get('cedula'),
            "telefono": request.form.get('telefono'),
            "equipo": request.form.get('equipo'),
            "imei": request.form.get('imei', 'N/A'),
            "problema": request.form.get('problema'),
            "costo_rep": request.form.get('costo_rep', '0'),
            "costo_total": request.form.get('costo_total', '0'),
            "estado": "Recibido",
            "foto": foto_filename
        }
        ordenes_db.append(nueva_orden)
        flash(f"¡Orden {nuevo_id} registrada con éxito!", "success")
        
        if session.get('admin'):
            return redirect(url_for('admin_panel'))
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error al registrar la orden: {e}", 500

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
