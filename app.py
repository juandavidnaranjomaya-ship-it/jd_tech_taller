import os
import random
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "jd_tech_secreto_seguro_2026"

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Base de datos simulada en memoria robusta
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
        "estado": "Reparado",
        "fecha_reparacion": "2026-11-20",
        "dias_restantes": 23,
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
    
    # Calcular días restantes actualizados para las órdenes reparadas
    hoy = datetime.now().date()
    for o in ordenes_db:
        if o['estado'] == 'Reparado' and o.get('fecha_reparacion'):
            f_rep = datetime.strptime(o['fecha_reparacion'], '%Y-%m-%d').date()
            dias_pasados = (hoy - f_rep).days
            o['dias_restantes'] = max(0, 30 - dias_pasados)
        else:
            o['dias_restantes'] = '-'

    return render_template('admin.html', ordenes=ordenes_db)

@app.route('/crear-orden', methods=['POST'])
def crear_orden():
    try:
        nuevo_id = f"ORD-{random.randint(500, 999)}"
        
        foto_filename = ""
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                foto_filename = filename

        estado_inicial = "Recibido"
        fecha_rep_val = ""
        
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
            "estado": estado_inicial,
            "fecha_reparacion": fecha_rep_val,
            "dias_restantes": '-',
            "foto": foto_filename
        }
        ordenes_db.append(nueva_orden)
        flash(f"¡Orden {nuevo_id} registrada con éxito!", "success")
        
        if session.get('admin'):
            return redirect(url_for('admin_panel'))
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error al registrar la orden: {e}", 500

@app.route('/actualizar-masivo', methods=['POST'])
def actualizar_masivo():
    if not session.get('admin'):
        return redirect(url_for('login_admin'))
    
    try:
        for o in ordenes_db:
            oid = o['id']
            nuevo_estado = request.form.get(f'estado_{oid}')
            nuevo_cliente = request.form.get(f'cliente_{oid}')
            nuevo_equipo = request.form.get(f'equipo_{oid}')
            nuevo_costo_total = request.form.get(f'costo_total_{oid}')
            
            if nuevo_estado:
                # Si pasa a Reparado por primera vez o cambia a reparado, registrar fecha actual
                if nuevo_estado == 'Reparado' and o['estado'] != 'Reparado':
                    o['fecha_reparacion'] = datetime.now().strftime('%Y-%m-%d')
                o['estado'] = nuevo_estado
            if nuevo_cliente:
                o['cliente'] = nuevo_cliente
            if nuevo_equipo:
                o['equipo'] = nuevo_equipo
            if nuevo_costo_total:
                o['costo_total'] = nuevo_costo_total
                
        flash("¡Cambios masivos guardados correctamente!", "success")
    except Exception as e:
        flash(f"Error al actualizar: {e}", "danger")
        
    return redirect(url_for('admin_panel'))

@app.route('/eliminar-orden/<string:orden_id>', methods=['POST'])
def eliminar_orden(orden_id):
    if not session.get('admin'):
        return redirect(url_for('login_admin'))
    
    global ordenes_db
    ordenes_db = [o for o in ordenes_db if o['id'] != orden_id]
    flash(f"Orden {orden_id} eliminada correctamente.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
