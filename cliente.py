from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime

clientes_bp = Blueprint('cliente', __name__)

@clientes_bp.route('/agregar_cliente', methods=['GET', 'POST'])
def agregar_cliente():
    message = ""
    tipos_clientes = [] 
    from app import get_db_connection

    username = "usuario"
    password = "contraseña"

    try:
        conn = get_db_connection(username, password)
        cursor = conn.cursor()

        if request.method == 'POST':
            nombre = request.form['nombre_completo']
            contacto = request.form['contacto']
            correo = request.form['correo']
            tipo_cliente = request.form['tipo_cliente']
            estado = "Activo"  # Activo por defecto
            fecha_creacion = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Consultar el último IDCliente y sumarle 1 para obtener el siguiente
            cursor.execute("SELECT TOP 1 IDCliente FROM Clientes ORDER BY IDCliente DESC")
            ultimo_cliente = cursor.fetchone()

            if ultimo_cliente:
                # Asegurarse de que el valor es un número
                if isinstance(ultimo_cliente[0], str):
                    # Si el IDCliente tiene formato 'CLxxxx', extraemos solo el número
                    ultimo_id = int(ultimo_cliente[0][2:])  # Omite las dos primeras letras y toma el número
                    nuevo_id = ultimo_id + 1
                else:
                    # Si el valor de IDCliente es numérico, simplemente sumamos 1
                    nuevo_id = ultimo_cliente[0] + 1
            else:
                # Si no hay clientes, comenzar con 6
                nuevo_id = 6

            # Generar el nuevo IDCliente como número
            id_cliente = nuevo_id

            # Inserción en la base de datos
            cursor.execute("""
                INSERT INTO Clientes (IDCliente, NombreCompleto, Contacto, Correo, IDTipo, Estado, FechaCreacion)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (id_cliente, nombre, contacto, correo, tipo_cliente, estado, fecha_creacion))

            conn.commit()
            message = "Cliente agregado exitosamente."

        cursor.execute("SELECT IDTipo, Descripcion FROM TipoCliente")
        tipos_clientes = cursor.fetchall()

    except Exception as e:
        message = f"Error al agregar cliente: {str(e)}"
    finally:
        conn.close()

    return render_template('agregar_cliente.html', tipos_clientes=tipos_clientes, message=message)
