import mysql.connector
from werkzeug.security import generate_password_hash

# Conexión a la base de datos
database = mysql.connector.connect(
    host="metro.proxy.rlwy.net",
    port=55118,
    user="root",
    password="HEtZjfQwnLVHjxxLgeFOrehvsjXcTxoG",
    database="railway"
)

cursor = database.cursor()

# Datos del admin
correo = 'admin@smartbites.com'
contraseña = generate_password_hash('admin123')  
rol = 'admin'

# Insertar en la tabla de cuentas
cursor.execute("""
    INSERT INTO cuentas (correo_electronico, contraseña, rol)
    VALUES (%s, %s, %s)
""", (correo, contraseña, rol))

database.commit()
cursor.close()
database.close()

print("✅ Admin creado correctamente")