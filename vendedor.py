from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime

vendedores_bp = Blueprint('vendedor', __name__)

# Ruta para agregar un vendedor
@vendedores_bp.route('/agregar_vendedor', methods=['GET', 'POST'])
def agregar_vendedor():
    message = ""
    vendedores = []
    from app import get_db_connection

    username = "usuario"
    password = "contraseña"

    try:
        conn = get_db_connection(username, password)
        cursor = conn.cursor()

        if request.method == 'POST':
            nombre = request.form['nombre_completo']
            celular = request.form['celular']
            correo = request.form['correo']
            estado = "Activo"  # Activo por defecto
            fecha_ingreso = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cuenta_vendedor = request.form['cuenta_vendedor']  # Se agrega el campo cuenta_vendedor

            # Consultar el último IDVendedor y sumarle 1 para obtener el siguiente
            cursor.execute("SELECT TOP 1 IDVendedor FROM Vendedores ORDER BY IDVendedor DESC")
            ultimo_vendedor = cursor.fetchone()

            if ultimo_vendedor and ultimo_vendedor[0].isdigit():
                # Si el último IDVendedor es numérico, sumamos 1
                nuevo_id = int(ultimo_vendedor[0]) + 1
            else:
                # Si no hay vendedores, comenzamos con 1
                nuevo_id = 1

            # Generar el nuevo IDVendedor como número
            id_vendedor = nuevo_id

            # Inserción en la base de datos, agregando CuentaVendedor
            cursor.execute("""
                INSERT INTO Vendedores (IDVendedor, NombreVendedor, Celular, Correo, Estado, FechaIngreso, CuentaVendedor)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (id_vendedor, nombre, celular, correo, estado, fecha_ingreso, cuenta_vendedor))  # Se agrega CuentaVendedor

            conn.commit()
            message = "Vendedor agregado exitosamente."

        cursor.execute("SELECT IDVendedor, NombreVendedor, Celular, Correo, Estado FROM Vendedores")
        vendedores = cursor.fetchall()

    except Exception as e:
        message = f"Error al agregar vendedor: {str(e)}"
    finally:
        conn.close()

    return render_template('agregar_vendedor.html', vendedores=vendedores, message=message)

# Ruta para ver todos los vendedores
@vendedores_bp.route('/ver_vendedores')
def ver_vendedores():
    message = ""
    vendedores = []
    search_id = request.args.get('search_id', '').strip()
    from app import get_db_connection

    username = "usuario"
    password = "contraseña"

    try:
        conn = get_db_connection(username, password)
        cursor = conn.cursor()

        # Consultar todos los vendedores
        if search_id:
            # Filtrar por IDVendedor si se proporcionó el filtro
            cursor.execute("SELECT IDVendedor, NombreVendedor,FechaIngreso, Celular, Correo, Estado, CuentaVendedor FROM Vendedores WHERE IDVendedor LIKE ?", ('%' + search_id + '%',))
        else:
            # Si no hay filtro, traer todos los vendedores
            cursor.execute("SELECT IDVendedor, NombreVendedor,FechaIngreso, Celular, Correo, Estado, CuentaVendedor FROM Vendedores")
        vendedores = cursor.fetchall()

    except Exception as e:
        message = f"Error al obtener los vendedores: {str(e)}"
    finally:
        conn.close()

    return render_template('ver_vendedores.html', vendedores=vendedores, message=message, search_id=search_id)

# Ruta para modificar un vendedor
@vendedores_bp.route('/modificar_vendedor/<int:id_vendedor>', methods=['GET', 'POST'])
def modificar_vendedor(id_vendedor):
    message = ""
    vendedor = []
    from app import get_db_connection

    username = "usuario"
    password = "contraseña"

    try:
        conn = get_db_connection(username, password)
        cursor = conn.cursor()

        # Consultar el vendedor a modificar
        cursor.execute("SELECT * FROM Vendedores WHERE IDVendedor = ?", (id_vendedor,))
        vendedor = cursor.fetchone()

        if request.method == 'POST':
            nombre = request.form['nombre_completo']
            celular = request.form['celular']
            correo = request.form['correo']
            estado = request.form['estado']
            cuenta_vendedor = request.form['cuenta_vendedor']  # Se agrega el campo cuenta_vendedor

            # Actualizar en la base de datos, añadiendo CuentaVendedor
            cursor.execute("""
                UPDATE Vendedores 
                SET NombreVendedor = ?, Celular = ?, Correo = ?, Estado = ?, CuentaVendedor = ?
                WHERE IDVendedor = ?
            """, (nombre, celular, correo, estado, cuenta_vendedor, id_vendedor))  # Se agrega CuentaVendedor

            conn.commit()
            message = "Vendedor modificado exitosamente."
            return redirect(url_for('vendedor.ver_vendedores'))

    except Exception as e:
        message = f"Error al modificar el vendedor: {str(e)}"
    finally:
        conn.close()

    return render_template('modificar_vendedor.html', vendedor=vendedor, message=message)


# Ruta para cambiar el estado de un vendedor
@vendedores_bp.route('/cambiar_estado_vendedor/<int:id_vendedor>', methods=['GET', 'POST'])
def cambiar_estado_vendedor(id_vendedor):
    message = ""
    from app import get_db_connection

    username = "usuario"
    password = "contraseña"

    try:
        conn = get_db_connection(username, password)
        cursor = conn.cursor()

        # Obtener el estado actual del vendedor
        cursor.execute("SELECT Estado FROM Vendedores WHERE IDVendedor = ?", (id_vendedor,))
        vendedor = cursor.fetchone()
        
        if vendedor:
            nuevo_estado = 'Inactivo' if vendedor[0] == 'Activo' else 'Activo'
            cursor.execute("UPDATE Vendedores SET Estado = ? WHERE IDVendedor = ?", (nuevo_estado, id_vendedor))
            conn.commit()
            message = f"Vendedor cambiado a {nuevo_estado} correctamente."
        else:
            message = "Vendedor no encontrado."

    except Exception as e:
        message = f"Error al actualizar el estado del vendedor: {str(e)}"
    finally:
        conn.close()

    return redirect(url_for('vendedor.ver_vendedores', message=message))



