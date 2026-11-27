import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "jd_tech_secreto_seguro_2026"

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Base de datos simulada en memoria usando la cédula como clave principal
ordenes_db = [
    {
        "cedula": "1015074219",
        "cliente": "Eliana Maya",
        "telefono": "313 5760462",
        "equipo": "Samsung A34",
        "imei": "3534343332",
        "problema": "Cambio de pantalla",
        "costo_rep": "50000",
        "costo_total": "120000",
        "ganancia": 70000,
        "estado": "Reparado",
        "fecha_ingreso": "10/11/2026",
        "fecha_reparacion": "13/11/2026",
        "dias_restantes": 27,
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
            if busqueda in o['cedula'].lower() or busqueda in o['telefono'].lower() or busqueda in o['cliente'].lower()
        ]
        if not ordenes:
            error = "No se encontro ninguna orden con ese numero de cedula o telefono."
            
    return render_template('estado.html', ordenes=ordenes, error=error)

@app.route('/login-admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == "301023":
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash("Contrasena incorrecta", "danger")
            
    return render_template('login_admin.html')

@app.route('/admin', methods=['GET'])
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('login_admin'))
    
    hoy = datetime.now().date()
    for o in ordenes_db:
        if o['estado'] == 'Reparado' and o.get('fecha_rep_obj'):
            f_rep = o['fecha_rep_obj']
            dias_pasados = (hoy - f_rep).days
            o['dias_restantes'] = max(0, 30 - dias_pasados)
        elif o['estado'] != 'Reparado':
            o['dias_restantes'] = '-'

    return render_template('admin.html', ordenes=ordenes_db)

@app.route('/crear-orden', methods=['POST'])
def crear_orden():
    try:
        cedula_original = request.form.get('cedula_original', '').strip()
        cedula = request.form.get('cedula', '').strip()
        cliente = request.form.get('cliente', '').strip()
        telefono = request.form.get('telefono', '').strip()
        equipo = request.form.get('equipo', '').strip()
        imei = request.form.get('imei', 'N/A').strip()
        
        problema_sel = request.form.get('problema', '').strip()
        problema_otro = request.form.get('problema_otro', '').strip()
        problema = problema_otro if problema_sel == 'Otro' and problema_otro else problema_sel
        
        costo_rep_str = request.form.get('costo_rep', '0').strip()
        costo_total_str = request.form.get('costo_total', '0').strip()
        
        costo_rep = int(costo_rep_str) if costo_rep_str.isdigit() else 0
        costo_total = int(costo_total_str) if costo_total_str.isdigit() else 0
        ganancia = costo_total - costo_rep

        foto_filename = ""
        if 'foto' in request.files:
            file = request.files['foto']
            if file and file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                foto_filename = filename

        # Si se esta editando una orden existente mediante la cedula original
        if cedula_original:
            for o in ordenes_db:
                if o['cedula'] == cedula_original:
                    o['cedula'] = cedula if cedula else o['cedula']
                    o['cliente'] = cliente
                    o['telefono'] = telefono
                    o['equipo'] = equipo
                    if imei and imei != 'N/A':
                        o['imei'] = imei
                    o['problema'] = problema
                    o['costo_rep'] = str(costo_rep)
                    o['costo_total'] = str(costo_total)
                    o['ganancia'] = ganancia
                    if foto_filename:
                        o['foto'] = foto_filename
            flash(f"Orden de la cedula {cedula} actualizada correctamente", "success")
        else:
            # Validar si ya existe la cedula
            for o in ordenes_db:
                if o['cedula'] == cedula:
                    flash(f"Ya existe una orden registrada con la cedula {cedula}", "danger")
                    return redirect(url_for('admin_panel') if session.get('admin') else url_for('index'))

            fecha_ingreso_str = datetime.now().strftime('%d/%m/%Y')
            nueva_orden = {
                "cedula": cedula,
                "cliente": cliente,
                "telefono": telefono,
                "equipo": equipo,
                "imei": imei if imei else 'N/A',
                "problema": problema,
                "costo_rep": str(costo_rep),
                "costo_total": str(costo_total),
                "ganancia": ganancia,
                "estado": "Recibido",
                "fecha_ingreso": fecha_ingreso_str,
                "fecha_reparacion": "Pendiente",
                "fecha_rep_obj": None,
                "dias_restantes": '-',
                "foto": foto_filename
            }
            ordenes_db.append(nueva_orden)
            flash(f"Orden registrada con exito para la cedula {cedula}", "success")
        
        if session.get('admin'):
            return redirect(url_for('admin_panel'))
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error al procesar la orden: {e}", 500

@app.route('/actualizar-masivo', methods=['POST'])
def actualizar_masivo():
    if not session.get('admin'):
        return redirect(url_for('login_admin'))
    
    try:
        for o in ordenes_db:
            ced = o['cedula']
            nuevo_estado = request.form.get(f'estado_{ced}')
            if nuevo_estado:
                if nuevo_estado == 'Reparado' and o['estado'] != 'Reparado':
                    o['fecha_reparacion'] = datetime.now().strftime('%d/%m/%Y %H:%M')
                    o['fecha_rep_obj'] = datetime.now().date()
                    o['dias_restantes'] = 30
                o['estado'] = nuevo_estado
                
        flash("Estados actualizados correctamente", "success")
    except Exception as e:
        flash(f"Error al actualizar: {e}", "danger")
        
    return redirect(url_for('admin_panel'))

@app.route('/eliminar-orden/<string:cedula>', methods=['POST'])
def eliminar_orden(cedula):
    if not session.get('admin'):
        return redirect(url_for('login_admin'))
    
    global ordenes_db
    ordenes_db = [o for o in ordenes_db if o['cedula'] != cedula]
    flash(f"Orden de la cedula {cedula} eliminada correctamente", "success")
    return redirect(url_for('admin_panel'))

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
