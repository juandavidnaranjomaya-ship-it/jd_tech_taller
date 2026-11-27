import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client, Client

app = Flask(__name__)
# Clave secreta indispensable para el manejo de sesiones del panel de administrador
app.secret_key = os.environ.get("SECRET_KEY", "jd_tech_secreto_seguro_2026")

# Configuración y conexión con Supabase (vía HTTP/443 para evitar bloqueos en Render)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY en Render.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================================
# RUTAS PÚBLICAS Y DE CONSULTA
# ==========================================

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
            # Consulta en Supabase usando la API HTTP
            response = supabase.table("ordenes").select("*").ilike("id", f"%{busqueda}%").execute()
            ordenes = response.data
            if not ordenes:
                error = "No se encontró ninguna orden con ese criterio."
        except Exception as e:
            error = f"Error al consultar la base de datos: {e}"
            
    return render_template('estado.html', ordenes=ordenes, error=error)

# ==========================================
# RUTAS DE AUTENTICACIÓN Y ADMINISTRACIÓN
# ==========================================

@app.route('/login-admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        
        # Validación estricta con tu contraseña establecida (301023)
        if usuario == "admin" and password == "301023":
            session['admin'] = True
            return redirect(url_for('admin_panel'))
        else:
            flash("Usuario o contraseña incorrectos", "danger")
            
    return render_template('login_admin.html')

@app.route('/admin', methods=['GET'])
def admin_panel():
    # Seguridad: si no hay sesión activa, redirige al login
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

# ==========================================
# GESTIÓN DE ÓRDENES (CREAR / ACTUALIZAR)
# ==========================================

@app.route('/crear-orden', methods=['GET', 'POST'])
def crear_orden():
    if request.method == 'POST':
        try:
            nueva_orden = {
                "cliente": request.form.get('cliente'),
                "equipo": request.form.get('equipo'),
                "problema": request.form.get('problema'),
                "estado": "Recibido"
            }
            # Inserción en Supabase
            supabase.table("ordenes").insert(nueva_orden).execute()
            flash("¡Orden registrada con éxito!", "success")
            
            # Redirección inteligente según quién la cree
            if session.get('admin'):
                return redirect(url_for('admin_panel'))
            return redirect(url_for('index'))
        except Exception as e:
            return f"Error al registrar la orden en la base de datos: {e}", 500
            
    return render_template('crear_orden.html' if os.path.exists('templates/crear_orden.html') else 'index.html')

if __name__ == '__main__':
    app.run(debug=True)
