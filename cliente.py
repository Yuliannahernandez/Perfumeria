from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime

clientes_bp = Blueprint('cliente', __name__)

# Ruta para agregar un cliente
@clientes_bp.route('/agregar_cliente', methods=['GET', 'POST'])
def agregar_cliente():
    message = ""
    tipos_clientes = [] 
    clientes = []
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

        cursor.execute("SELECT IDCliente, NombreCompleto, Contacto, Correo FROM Clientes")
        clientes = cursor.fetchall()

    except Exception as e:
        message = f"Error al agregar cliente: {str(e)}"
    finally:
        conn.close()

    return render_template('agregar_cliente.html', tipos_clientes=tipos_clientes, clientes=clientes, message=message)

# Ruta para ver todos los clientes
@clientes_bp.route('/ver_clientes')
def ver_clientes():
    message = ""
    clientes = []
    search_id = request.args.get('search_id', '').strip()
    from app import get_db_connection

    username = "usuario"
    password = "contraseña"

    try:
        conn = get_db_connection(username, password)
        cursor = conn.cursor()

        # Consultar todos los clientes
        if search_id:
            # Filtrar por IDCliente si se proporcionó el filtro
            cursor.execute("SELECT IDCliente, NombreCompleto, Contacto, Correo, Estado FROM Clientes WHERE IDCliente LIKE ?", ('%' + search_id + '%',))
        else:
            # Si no hay filtro, traer todos los clientes
            cursor.execute("SELECT IDCliente, NombreCompleto, Contacto, Correo, Estado FROM Clientes")
        clientes = cursor.fetchall()

    except Exception as e:
        message = f"Error al obtener los clientes: {str(e)}"
    finally:
        conn.close()

    return render_template('ver_clientes.html', clientes=clientes,message=message,search_id=search_id)

# Ruta para modificar un cliente
@clientes_bp.route('/modificar_cliente/<int:id_cliente>', methods=['GET', 'POST'])
def modificar_cliente(id_cliente):
    message = ""
    tipos_clientes = [] 
    cliente = []
    from app import get_db_connection

    username = "usuario"
    password = "contraseña"

    try:
        conn = get_db_connection(username, password)
        cursor = conn.cursor()

        # Consultar el cliente a modificar
        cursor.execute("SELECT * FROM Clientes WHERE IDCliente = ?", (id_cliente,))
        cliente = cursor.fetchone()

        if request.method == 'POST':
            nombre = request.form['nombre_completo']
            contacto = request.form['contacto']
            correo = request.form['correo']
            tipo_cliente = request.form['tipo_cliente']
            estado = request.form['estado']
            
            # Actualizar en la base de datos
            cursor.execute("""
                UPDATE Clientes 
                SET NombreCompleto = ?, Contacto = ?, Correo = ?, IDTipo = ?, Estado = ?
                WHERE IDCliente = ?
            """, (nombre, contacto, correo, tipo_cliente, estado, id_cliente))

            conn.commit()
            message = "Cliente modificado exitosamente."
            return redirect(url_for('cliente.ver_clientes'))

        cursor.execute("SELECT IDTipo, Descripcion FROM TipoCliente")
        tipos_clientes = cursor.fetchall()

    except Exception as e:
        message = f"Error al modificar el cliente: {str(e)}"
    finally:
        conn.close()

    return render_template('modificar_cliente.html', cliente=cliente, tipos_clientes=tipos_clientes, message=message)

# Ruta para eliminar un cliente
@clientes_bp.route('/eliminar_cliente/<int:id_cliente>', methods=['GET', 'POST'])
def eliminar_cliente(id_cliente):
    message = ""
    from app import get_db_connection

    username = "usuario"
    password = "contraseña"

    try:
        conn = get_db_connection(username, password)
        cursor = conn.cursor()

        # Obtener el estado actual del cliente
        cursor.execute("SELECT Estado FROM Clientes WHERE IDCliente = ?", (id_cliente,))
        cliente = cursor.fetchone()
        
        if cliente:
            nuevo_estado = 'Inactivo' if cliente[0] == 'Activo' else 'Activo'
            cursor.execute("UPDATE Clientes SET Estado = ? WHERE IDCliente = ?", (nuevo_estado, id_cliente))
            conn.commit()
            message = f"Cliente cambiado a {nuevo_estado} correctamente."
        else:
            message = "Cliente no encontrado."

    except Exception as e:
        message = f"Error al actualizar el estado del cliente: {str(e)}"
    finally:
        conn.close()

    return redirect(url_for('cliente.ver_clientes', message=message))
