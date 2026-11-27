import os
import random
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from werkzeug.utils import secure_filename
import csv
import io

app = Flask(__name__)
app.secret_key = "jd_tech_secreto_seguro_2026"

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Base de datos en memoria con datos de ejemplo idénticos al video
ordenes_db = [
    {
        "id": "ORD-501",
        "cliente": "Carlos Pérez",
        "cedula": "1015074219",
        "telefono": "3001234567",
        "equipo": "iPhone 11",
        "imei": "353434333211",
        "problema": "Cambio de pantalla",
        "costo_rep": "50000",
        "costo_total": "120000",
        "estado": "Reparado",
        "fecha": "10/11/2026",
        "fecha_reparacion": "13/11/2026 10:52",
        "foto": ""
    },
    {
        "id": "ORD-502",
        "cliente": "Zahyra Naranjo",
        "cedula": "1015074220",
        "telefono": "312 7181927",
        "equipo": "Samsung A34",
        "imei": "353434333222",
        "problema": "Pin de carga",
        "costo_rep": "25000",
        "costo_total": "70000",
        "estado": "En revisión",
        "fecha": "13/11/2026",
        "fecha_reparacion": "Pendiente",
        "foto": ""
    },
    {
        "id": "ORD-503",
        "cliente": "Eliana Maya",
        "cedula": "1015074221",
        "telefono": "3001234567",
        "equipo": "Samsung A34",
        "imei": "353434333233",
        "problema": "No enciende",
        "costo_rep": "50000",
        "costo_total": "120000",
        "estado": "Ingresado",
        "fecha": "13/11/2026",
        "fecha_reparacion": "Pendiente",
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
            if busqueda in o['telefono'].lower() or busqueda in o['cliente'].lower() or busqueda in o['id'].lower() or busqueda in o['cedula'].lower()
        ]
        if not ordenes:
            error = "No se encontró ninguna orden con ese número de teléfono, nombre o cédula."
            
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
    filtro = request.args.get('filtro', 'Todos')
    if filtro != 'Todos':
        ordenes_filtradas = [o for o in ordenes_db if o['estado'] == filtro]
    else:
        ordenes_filtradas = ordenes_db
    return render_template('admin.html', ordenes=ordenes_filtradas, filtro_actual=filtro)

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

        problema = request.form.get('problema')
        if problema == "Otro (Especificar en taller)":
            problema = request.form.get('problema_otro', 'Otro problema')

        nueva_orden = {
            "id": nuevo_id,
            "cliente": request.form.get('cliente'),
            "cedula": request.form.get('cedula', 'N/A'),
            "telefono": request.form.get('telefono'),
            "equipo": request.form.get('equipo'),
            "imei": request.form.get('imei', 'N/A'),
            "problema": problema,
            "costo_rep": request.form.get('costo_rep', '0'),
            "costo_total": request.form.get('costo_total', '0'),
            "estado": "Ingresado",
            "fecha": "13/11/2026",
            "fecha_reparacion": "Pendiente",
            "foto": foto_filename
        }
        ordenes_db.insert(0, nueva_orden)
        flash("Solicitud enviada con exito! Ya puedes consultar su estado.", "success")
        
        if session.get('admin'):
            return redirect(url_for('admin_panel'))
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error al registrar la orden: {e}", 500

@app.route('/actualizar-orden/<string:orden_id>', methods=['POST'])
def actualizar_orden(orden_id):
    if not session.get('admin'):
        return redirect(url_for('login_admin'))
    
    for o in ordenes_db:
        if o['id'] == orden_id:
            o['estado'] = request.form.get('estado', o['estado'])
            o['costo_rep'] = request.form.get('costo_rep', o['costo_rep'])
            o['costo_total'] = request.form.get('costo_total', o['costo_total'])
            if o['estado'] == 'Reparado' and o['fecha_reparacion'] == 'Pendiente':
                o['fecha_reparacion'] = '13/11/2026 11:01'
            break
            
    flash("Orden actualizada correctamente.", "success")
    return redirect(url_for('admin_panel'))

@app.route('/descargar-excel')
def descargar_excel():
    if not session.get('admin'):
        return redirect(url_for('login_admin'))
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Cliente', 'Cedula', 'Telefono', 'Equipo', 'IMEI', 'Problema', 'Costo Repuesto', 'Costo Total', 'Estado', 'Fecha Ingreso'])
    
    for o in ordenes_db:
        writer.writerow([o['id'], o['cliente'], o['cedula'], o['telefono'], o['equipo'], o['imei'], o['problema'], o['costo_rep'], o['costo_total'], o['estado'], o['fecha']])
        
    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment.csv; filename=reporte_ordenes_jd_tech.csv"}
    )

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
