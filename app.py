from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


import os
import database as db
import traceback

import os
from openai import OpenAI
from dotenv import load_dotenv



base_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(base_dir, 'templates')
static_dir = os.path.join(base_dir, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
app.secret_key = 'natalia2006'

fecha = datetime.now().isoformat()

UPLOAD_FOLDER = 'static/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def extension_valida(nombre_archivo):
    return '.' in nombre_archivo and nombre_archivo.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------- API de comentarios ----------------
@app.route('/api/comentarios', methods=['GET', 'POST'])
def comentarios_api():
    cursor = db.database.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            if 'usuario_id' not in session:
                return jsonify({'error': 'No autenticado'}), 401

            data = request.get_json(force=True)  # <-- fuerza que sea JSON
            texto = data.get('texto', '').strip()
            if not texto:
                return jsonify({'error': 'Comentario vacío'}), 400

            # Obtener usuario
            cursor.execute("""
                SELECT u.nombre_completo, c.correo_electronico
                FROM usuarios u
                JOIN cuentas c ON u.id_usuario = c.id
                WHERE u.id_usuario = %s
            """, (session['usuario_id'],))
            usuario = cursor.fetchone()
            if not usuario:
                return jsonify({'error': 'Usuario no encontrado'}), 404

            nombre = usuario['nombre_completo']
            email = usuario['correo_electronico']

            # Insertar
            cursor.execute("INSERT INTO comentarios (nombre, email, texto) VALUES (%s, %s, %s)", (nombre, email, texto))
            db.database.commit()

            return jsonify({'nombre': nombre, 'texto': texto, 'fecha': datetime.now().isoformat()}), 201

        # GET comentarios
        cursor.execute("SELECT nombre, texto, fecha FROM comentarios ORDER BY fecha DESC")
        comentarios = cursor.fetchall()
        return jsonify(comentarios)

    except Exception as e:
        print("❌ Error:", e)
        traceback.print_exc()
        return jsonify({'error': 'Error interno en el servidor'}), 500

    finally:
        cursor.close()

# ---------------- Rutas de página ----------------
@app.route('/')
def home():
    if 'usuario_id' in session:
        cursor = db.database.cursor(dictionary=True)
        cursor.execute("SELECT nombre_completo, foto_perfil FROM usuarios WHERE id_usuario = %s", (session['usuario_id'],))
        datos = cursor.fetchone()
        cursor.close()

        if datos:  
            usuario = {
                'nombre_completo': datos['nombre_completo'],
                'foto_perfil': datos['foto_perfil']
            }
        else:
            usuario = None

        return render_template('PaginaPrincipal.html', usuario=usuario)

    # Si no hay sesión
    return render_template('PaginaPrincipal.html', usuario=None)

@app.route('/register')
def register():
    return render_template('CrearCuenta.html')

@app.route('/desayunos')
def desayunos():
    return render_template('Desayunos.html')

@app.route('/comidas')
def comidas():
    return render_template('Comidas.html')

@app.route('/cenas')
def cenas():
    return render_template('Cenas.html')

@app.route('/colaciones')
def colaciones():
    return render_template('Colaciones.html')

@app.route('/chat_usuario')
def chat_usuario(): 
    return render_template('ChatUsuario.html')

@app.route('/mostrar_registro')
def mostrar_registro():
    return render_template('CrearCuenta.html')

@app.route('/pacientes')
def pacientes():
    if 'usuario_id' not in session or session.get('rol') != 'nutriologo':
        return redirect(url_for('login'))
    return render_template('Pacientes.html')

@app.route('/pagina_nutriologo')
def pagina_nutriologo():
    if 'usuario_id' not in session or session.get('rol') != 'nutriologo':
        return redirect(url_for('login'))
    return render_template('PrincipalNutriologo.html')

@app.route('/logout')
def logout():
    session.clear()  
    return render_template('PaginaPrincipal.html') 

@app.route('/perfil_usuario')
def perfil_usuario():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    cursor = db.database.cursor(dictionary=True)

    cursor.execute("""
        SELECT u.nombre_completo, c.correo_electronico, u.ciudad_pais, 
               u.numero_telefono, u.foto_perfil
        FROM usuarios u
        JOIN cuentas c ON u.id_usuario = c.id
        WHERE u.id_usuario = %s
    """, (session['usuario_id'],))

    datos = cursor.fetchone()
    cursor.close()

    if not datos:
        return "Usuario no encontrado", 404

    usuario = {
        'nombre_completo': datos['nombre_completo'],
        'foto_perfil': datos['foto_perfil'],
        'correo': datos['correo_electronico'],
        'pais': datos['ciudad_pais'],
        'telefono': datos['numero_telefono']
    }

    return render_template('PerfilUsuario.html', usuario=usuario)



@app.route('/actualizar_perfil', methods=['POST'])
def actualizar_perfil():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

   
    nombre = request.form['nombre']
    correo = request.form['correo']
    ciudad = request.form['pais']
    telefono = request.form['telefono']
    nueva_contraseña = request.form['nueva_contraseña']
    foto = request.files.get('foto_perfil')

    cursor = db.database.cursor()

  
    if foto and foto.filename != '':
        from werkzeug.utils import secure_filename
        import os

        filename = secure_filename(foto.filename)
        ruta_guardado = os.path.join(app.static_folder, 'img', filename)
        foto.save(ruta_guardado)

        
        cursor.execute("UPDATE usuarios SET foto_perfil = %s WHERE id_usuario = %s", (filename, session['usuario_id']))

  
    if nueva_contraseña.strip():
        if len(nueva_contraseña) < 6:
            return "La contraseña debe tener al menos 6 caracteres"
        from werkzeug.security import generate_password_hash
        contraseña_segura = generate_password_hash(nueva_contraseña)
      
        cursor.execute("UPDATE cuentas SET contraseña = %s WHERE id = %s", (contraseña_segura, session['usuario_id']))


    cursor.execute("""
        UPDATE usuarios
        SET nombre_completo = %s, ciudad_pais = %s, numero_telefono = %s
        WHERE id_usuario = %s
    """, (nombre, ciudad, telefono, session['usuario_id']))

    cursor.execute("UPDATE cuentas SET correo_electronico = %s WHERE id = %s", (correo, session['usuario_id']))

    db.database.commit()
    cursor.close()

 
    session['usuario_nombre'] = nombre

    return redirect(url_for('perfil_usuario'))



@app.route('/PrincipalRegistrada')
def PrincipalRegistrada():
    if 'usuario_id' not in session or session.get('rol') != 'usuario':
        return redirect(url_for('login'))

    conexion = db.database.cursor(dictionary=True)
    conexion.execute("SELECT nombre_completo, foto_perfil FROM usuarios WHERE id_usuario = %s", (session['usuario_id'],))
    datos = conexion.fetchone()
    
    if datos:
        usuario = {
            'nombre': datos['nombre_completo'],
            'foto_perfil': datos['foto_perfil'] 
        }
    else:
        usuario = {
            'nombre': session.get('usuario_nombre'),
            'foto_perfil': None
        }

    return render_template('PrincipalRegistrada.html', usuario=usuario)
    



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo_electronico']
        contraseña = request.form['contraseña']

        cursor = db.database.cursor(dictionary=True)
        cursor.execute("SELECT * FROM cuentas WHERE correo_electronico = %s", (correo,))
        cuenta = cursor.fetchone()

        if cuenta and check_password_hash(cuenta['contraseña'], contraseña):
            session['usuario_id'] = cuenta['id']
            session['rol'] = cuenta['rol']

            if cuenta['rol'] == 'usuario':
                return redirect(url_for('PrincipalRegistrada'))
            elif cuenta['rol'] == 'nutriologo':
                return redirect(url_for('pagina_nutriologo'))
            elif cuenta['rol'] == 'admin':
                return redirect(url_for('dashboard_admin')) 

        else:
            return render_template('Login.html', error="Credenciales incorrectas")

    return render_template('Login.html')


@app.route('/registro_usuario', methods=['POST'])
def registro_usuario():
    correo = request.form['correo_electronico']
    contraseña = generate_password_hash(request.form['contraseña'])
    rol = 'usuario'
    nombre = request.form['nombre_completo']
    ciudad = request.form['ciudad_pais']
    telefono = request.form['numero_telefono']
    foto = request.files.get('foto_perfil')

    nombre_foto = None
    if foto and foto.filename:
        from werkzeug.utils import secure_filename
        nombre_foto = secure_filename(foto.filename)
        foto.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_foto))

    cursor = db.database.cursor()


    cursor.execute("INSERT INTO cuentas (correo_electronico, contraseña, rol) VALUES (%s, %s, %s)",
                   (correo, contraseña, rol))
    db.database.commit()
    id_cuenta = cursor.lastrowid


    cursor.execute("""INSERT INTO usuarios
        (id_usuario, nombre_completo, ciudad_pais, numero_telefono, foto_perfil)
        VALUES (%s, %s, %s, %s, %s)""",
        (id_cuenta, nombre, ciudad, telefono, nombre_foto))
    db.database.commit()
    cursor.close()

    return redirect(url_for('login'))

@app.route('/registro_nutriologo', methods=['POST'])
def registro_nutriologo():
    correo = request.form['correo_electronico']
    contraseña = generate_password_hash(request.form['contraseña'])
    rol = 'nutriologo'
    nombre = request.form['nombre_completo']
    cedula = request.form['cedula_profesional']
    especialidad = request.form['especialidad']
    formacion = request.form['formacion']
    experiencia = request.form['experiencia']
    modalidad = request.form['modalidad_atencion']
    costo = request.form['costo_cita']
    ciudad = request.form['ciudad_pais']
    telefono = request.form['numero_telefono']
    foto = request.files.get('foto_perfil')

    nombre_foto = None
    if foto and foto.filename:
        from werkzeug.utils import secure_filename
        nombre_foto = secure_filename(foto.filename)
        foto.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_foto))

    cursor = db.database.cursor()

 
    cursor.execute("INSERT INTO cuentas (correo_electronico, contraseña, rol) VALUES (%s, %s, %s)",
                   (correo, contraseña, rol))
    db.database.commit()
    id_cuenta = cursor.lastrowid

  
    cursor.execute("""INSERT INTO nutriologos (
        id_nutriologo, nombre_completo, cedula_profesional, especialidad,
        formacion, experiencia, modalidad_atencion, costo_cita,
        ciudad_pais, numero_telefono, foto_perfil, estado)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        id_cuenta, nombre, cedula, especialidad,
        formacion, experiencia, modalidad, costo,
        ciudad, telefono, nombre_foto, 'pendiente'  
    ))
    db.database.commit()
    cursor.close()

    return redirect(url_for('login'))

# ---------------- Rutas de Usuario ----------------

@app.route('/nutriologos')
def nutriologos(): 
    cursor = db.database.cursor(dictionary=True)
    cursor.execute("SELECT * FROM nutriologos WHERE estado = 'aprobado'")
    nutris = cursor.fetchall()
    cursor.close()

    usuario = None
    if 'usuario_id' in session:
        cursor = db.database.cursor(dictionary=True)
        cursor.execute("SELECT nombre_completo, foto_perfil FROM usuarios WHERE id_usuario = %s", (session['usuario_id'],))
        usuario = cursor.fetchone()
        cursor.close()

    return render_template('Nutriologos.html', nutriologos=nutris, usuario=usuario)

# ---------------- Rutas de administración ----------------

@app.route('/admin')
def dashboard_admin():
    if 'usuario_id' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))

    cursor = db.database.cursor(dictionary=True)

    cursor.execute("SELECT id_nutriologo, nombre_completo FROM nutriologos WHERE estado = 'pendiente'")
    nutriologos_pendientes = cursor.fetchall()

    cursor.execute("SELECT id_nutriologo, nombre_completo FROM nutriologos WHERE estado = 'aprobado'")
    nutriologos_aprobados = cursor.fetchall()

    cursor.execute("""
        SELECT usuarios.id_usuario, usuarios.nombre_completo
        FROM usuarios
        JOIN cuentas ON usuarios.id_usuario = cuentas.id
        WHERE cuentas.rol = 'usuario'
    """)
    usuarios = cursor.fetchall()

    return render_template("GestionDeUsuariosAD.html", 
        nutriologos_pendientes=nutriologos_pendientes,
        nutriologos_aprobados=nutriologos_aprobados,
        usuarios=usuarios
    )




@app.route('/admin/aprobar_nutriologo/<int:id>', methods=['POST'])
def aprobar_nutriologo(id):
    cursor = db.database.cursor()
    cursor.execute("UPDATE nutriologos SET estado = 'aprobado' WHERE id_nutriologo = %s", (id,))
    db.database.commit()
    return redirect(url_for('dashboard_admin'))

@app.route('/admin/rechazar_nutriologo/<int:id>', methods=['POST'])
def rechazar_nutriologo(id):
    cursor = db.database.cursor()
    cursor.execute("UPDATE nutriologos SET estado = 'rechazado' WHERE id_nutriologo = %s", (id,))
    db.database.commit()
    return redirect(url_for('dashboard_admin'))

@app.route('/admin/eliminar_usuario/<int:id>', methods=['POST'])
def eliminar_usuario(id):
    cursor = db.database.cursor()
    cursor.execute("DELETE FROM cuentas WHERE id = %s", (id,))
    db.database.commit()
    return redirect(url_for('dashboard_admin'))




# ------- IA -------------


@app.route("/chatbot", methods=["POST"])
def chatbot():
    try:
        data = request.get_json()
        mensaje_usuario = data.get("mensaje", "").strip()

        if not mensaje_usuario:
            return jsonify({"respuesta": "No escribiste ningún mensaje."}), 400

        respuesta = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres una nutrióloga profesional, empática y clara. "
                        "Solo puedes responder preguntas relacionadas con nutrición, alimentación saludable, "
                        "hábitos alimenticios y temas de salud relacionados con la comida. "
                        "Si el usuario pregunta sobre otro tema, amablemente redirígelo a hablar de nutrición. "
                        "Tus respuestas deben ser breves, útiles y fáciles de entender (máximo 3 párrafos breves)."
                        "Recuerdale que no puedes dar diagnósticos médicos ni sustituir la consulta con un profesional de la salud. "
                        "Si el usuario pregunta por un diagnóstico o tratamieto médico, dile que consulte a un médico calificado. "
                        "Siempre recuerdale que la información que le das es general y no sustituye una consulta médica. "
                        "Tambien recomiendale que consulte a un nutriologo de nuestra pagina para un plan personalizado. "
                    )
                },
                {"role": "user", "content": mensaje_usuario}
            ],
            max_tokens=300,  # Limita la longitud de la respuesta (aprox. 2-3 párrafos)
            temperature=0.7   # Creatividad moderada
        )

        texto_respuesta = respuesta.choices[0].message.content.strip()
        return jsonify({"respuesta": texto_respuesta})

    except Exception as e:
        print("❌ Error en /chatbot:", e)
        return jsonify({"respuesta": "Ocurrió un error al procesar la respuesta de la IA."}), 500
    

# ---------------- Rutas de Nutriologos ----------------

@app.route('/panel_nutriologo')
def panel_nutriologo():
            if 'usuario_id' not in session:
                return redirect(url_for('login'))
            nutriologo_id = obtener_id_nutriologo(session['usuario_id'])  
            return render_template('CalendarioNutriologo.html', nutriologoID=nutriologo_id)

from flask import g
import mysql.connector

def obtener_id_nutriologo(cuenta_id):
        connection = mysql.connector.connect(
            host="metro.proxy.rlwy.net",
            port=55118,
            user="root",
            password="HEtZjfQwnLVHjxxLgeFOrehvsjXcTxoG",
            database="railway"
        )
        cursor = connection.cursor(dictionary=True)

            # Como id_nutriologo = cuentas.id
        query = "SELECT id_nutriologo FROM nutriologos WHERE id_nutriologo = %s"
        cursor.execute(query, (cuenta_id,))
        resultado = cursor.fetchone()

        cursor.close()
        connection.close()

        if resultado:
            return resultado['id_nutriologo']
        else:
            return None

@app.route('/guardar_disponibilidad', methods=['POST'])
def guardar_disponibilidad():
            data = request.get_json()
            nutriologo_id = data.get('nutriologo_id')
            horarios = data.get('horarios')  
            if not nutriologo_id or not horarios:
                return jsonify({'status': 'error', 'message': 'Datos incompletos'}), 400
            cursor = db.database.cursor()
            try:   
                cursor.execute("DELETE FROM disponibilidad WHERE nutriologo_id = %s", (nutriologo_id,))

                for h in horarios:
                    fecha = h['fecha']
                    hora = h['hora']
                    cursor.execute("""
                        INSERT INTO disponibilidad (nutriologo_id, fecha, hora, disponible)
                        VALUES (%s, %s, %s, %s)
                    """, (nutriologo_id, fecha, hora, True))

                db.database.commit()
                cursor.close()
                return jsonify({'status': 'success'}), 200

            except Exception as e:
                db.database.rollback()
                cursor.close()
                return jsonify({'status': 'error', 'message': str(e)}), 500





if __name__ == '__main__':
    app.run()

