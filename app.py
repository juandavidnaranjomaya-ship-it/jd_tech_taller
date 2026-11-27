import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client, Client

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "jd_tech_secreto_seguro_2026")

# Conexión con Supabase mediante HTTP estándar (Puerto 443)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY en Render.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/estado', methods=['GET', 'POST'])
def estado():
    ordenes = []
    error = None
    if request.method == 'POST':
        busqueda = request.form.get('busqueda', '').strip()
        try:
            response = supabase.table("ordenes").select("*").ilike("id", f"%{busqueda}%").execute()
            ordenes = response.data
            if not ordenes:
                error = "No se encontró ninguna orden con ese criterio."
        except Exception as e:
            error = f"Error al consultar la base de datos: {e}"
            
    return render_template('estado.html', ordenes=ordenes, error=error)

@app.route('/login-admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        password = request.form.get('password')
        
        # Validación únicamente con la contraseña (301023)
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
    
    ordenes = []
    try:
        response = supabase.table("ordenes").select("*").execute()
        ordenes = response.data
    except Exception as e:
        flash(f"Error cargando las órdenes: {e}", "danger")
        
    return render_template('admin.html', ordenes=ordenes)

@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/crear-orden', methods=['POST'])
def crear_orden():
    try:
        nueva_orden = {
            "cliente": request.form.get('cliente'),
            "equipo": request.form.get('equipo'),
            "problema": request.form.get('problema'),
            "estado": "Recibido"
        }
        # Inserción correcta en Supabase
        supabase.table("ordenes").insert(nueva_orden).execute()
        flash("¡Orden registrada con éxito!", "success")
        
        if session.get('admin'):
            return redirect(url_for('admin_panel'))
        return redirect(url_for('index'))
    except Exception as e:
        return f"Error al registrar la orden en la base de datos: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)
