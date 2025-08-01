import mysql.connector

database = mysql.connector.connect(
    host="metro.proxy.rlwy.net",
    port=55118,
    user="root",
    password="HEtZjfQwnLVHjxxLgeFOrehvsjXcTxoG",
    database="railway"
)




def ensure_tables():
    cursor = database.cursor()
    cursor.execute("""
CREATE TABLE IF NOT EXISTS comentarios (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nombre VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL,
  texto TEXT NOT NULL,
  fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
""")
    database.commit()
    cursor.close()

# Al final de tu conexión, llama a:
ensure_tables()


