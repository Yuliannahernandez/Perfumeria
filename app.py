from flask import Flask, request, redirect, session, render_template, flash, send_from_directory, url_for
import pyodbc
import os
from dotenv import load_dotenv
from decimal import Decimal
from cliente import clientes_bp 
from inventario import inventario_bp


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "clave_secreta")


# Función para obtener la conexión a la base de datos
def get_db_connection(username, password):
    try:
        conn_str = (
            f'DRIVER={{SQL Server}};'
            f'SERVER={os.getenv("DB_SERVER")};'
            f'DATABASE={os.getenv("DB_DATABASE")};'
        )
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print("Error de conexión:", e)
        return None

def get_user_role(username, conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT Tipo_Usuario FROM Tabla_Usuarios WHERE Nombre_Usuario = ?", (username,))
        row = cursor.fetchone()
        if row:
            tipo_usuario = row[0]
            roles = {1: "admin", 2: "auditoria", 3: "General"}
            return roles.get(tipo_usuario, None)
        return None
    except pyodbc.Error as e:
        print(f"Error en consulta de usuario: {e}")
        return None
    


@app.route('/images/<filename>')
def serve_image(filename):
    images_folder = os.path.join(app.root_path, 'images')  
    return send_from_directory(images_folder, filename)

# Ruta de inicio de sesión
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db_connection(username, password)
        if conn:
            role = get_user_role(username, conn)
            conn.close()
            if role:
                session["user"] = username
                session["role"] = role  
                image_path = f"/images/{role}.jpg"  
                return render_template("welcome.html", role=role, image_path=image_path) 
            else:
                flash("Usuario no registrado", "danger")
        else:
            flash("Credenciales incorrectas o error de conexión", "danger")

    return render_template("login.html")


@app.route("/admin")
def admin():
    if "user" in session and session.get("role") == "admin":
        return "Bienvenido, Admin"
    return redirect("/")

@app.route("/auditoria")
def auditoria():
    if "user" in session and session.get("role") == "auditoria":
        return "Bienvenido, Auditoría"
    return redirect("/")

@app.route("/General")
def General():
    if "user" in session and session.get("role") == "General":
        return "Bienvenido, Usuario General"
    return redirect("/")

# Cerrar sesión
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    return redirect("/")

@app.route('/principal')
def principal():
    return render_template('principal.html')


from decimal import Decimal

@app.route('/nueva_factura', methods=['GET', 'POST'])
def nueva_factura():
    username = "usuario"  
    password = "contraseña"  

    conn = get_db_connection(username, password)
    cursor = conn.cursor()

    cursor.execute("SELECT IDCliente, NombreCompleto FROM Clientes WHERE Estado = 'Activo'")
    clientes = cursor.fetchall()

    cursor.execute("SELECT IDVendedor, NombreVendedor FROM Vendedores WHERE Estado = 'Activo'")
    vendedores = cursor.fetchall()

    cursor.execute("SELECT id_producto, nombre, precio FROM productos WHERE existencia_estantes > 0")
    productos = cursor.fetchall()

    cursor.execute("SELECT id_pago, descripcion FROM formas_pago")
    formas_pago = cursor.fetchall()

    conn.close()

    return render_template(
        'nueva_factura.html',
        clientes=clientes,
        vendedores=vendedores,
        productos=productos,
        formas_pago=formas_pago
    )
@app.route('/guardar_factura', methods=['POST'])
def guardar_factura():
    cliente_id = request.form['cliente']
    vendedor_id = request.form['vendedor']
    forma_pago_id = request.form['forma_pago']
    descuento = request.form.get('descuento', 0)

    try:
        username = "usuario"
        password = "contraseña"
        conn = get_db_connection(username, password)
        cursor = conn.cursor()

        # Obtener el próximo ID de venta personalizado
        cursor.execute("SELECT COALESCE(MAX(IDVenta), 0) + 1 FROM Ventas")
        id_venta = cursor.fetchone()[0]

        # Insertar la venta en "Ventas"
        cursor.execute(
            """
            INSERT INTO Ventas 
            (IDCliente, IDVendedor, IDFormaPago, Descuento, SubTotal, Total, Estado, TotalFactura)
            VALUES (?, ?, ?, ?, 0, 0, '1', 0)
            """,
            (cliente_id, str(vendedor_id), forma_pago_id, descuento)
        )

        # Inicializar los totales
        subtotal_total = Decimal(0)
        descuento_aplicado_total = Decimal(0)
        subtotal_con_descuento_total = Decimal(0)
        iva_total = Decimal(0)
        total_total = Decimal(0)

        # Insertar detalles de productos en un solo ciclo
        i = 1
        while True:
            producto_id = request.form.get(f'producto_{i}')
            cantidad = request.form.get(f'cantidad_{i}')
            if not producto_id or not cantidad:
                break  # Salir si no hay más productos

            producto_id = int(producto_id)
            cantidad = int(cantidad)

            # Obtener precio unitario del producto
            cursor.execute("SELECT precio FROM Productos WHERE id_producto = ?", (producto_id,))
            precio_unitario = cursor.fetchone()
            if precio_unitario is None:
                return f"Producto con ID {producto_id} no encontrado", 404

            precio_unitario = precio_unitario[0]
            subtotal = precio_unitario * cantidad
            descuento_aplicado = (subtotal * Decimal(descuento)) / Decimal(100)
            subtotal_con_descuento = subtotal - descuento_aplicado
            iva = subtotal_con_descuento * Decimal('0.13')
            total = subtotal_con_descuento + iva

            # Acumular totales
            subtotal_total += subtotal
            descuento_aplicado_total += descuento_aplicado
            subtotal_con_descuento_total += subtotal_con_descuento
            iva_total += iva
            total_total += total

            # Insertar producto en Detalle_Ventas
            cursor.execute(
                """
                INSERT INTO Detalle_Ventas (IDVenta, IDProducto, Cantidad, PrecioUnitario, SubTotal)
                VALUES (?, ?, ?, ?, ?)
                """,
                (id_venta, producto_id, cantidad, precio_unitario, subtotal)
            )

            i += 1  # Continuar con el siguiente producto

        # Actualizar totales de la factura
        cursor.execute(
            """
            UPDATE Ventas
            SET SubTotal = ?, Total = ?, TotalFactura = ?,DescuentoAplicado = ?,SubTotalConDescuento = ?,IVA = ?
            WHERE IDVenta = ?
            """,
            (subtotal_total, total_total, total_total,descuento_aplicado_total,subtotal_con_descuento_total,iva_total, id_venta)
        )

        conn.commit()

    except Exception as e:
        print(f"Error al guardar la factura: {e}")
        return f"Error al guardar la factura: {e}", 500  
    finally:
        conn.close()

    return redirect(url_for('factura_confirmada', id_venta=id_venta))

@app.route('/factura_confirmada', methods=['GET'])
def factura_confirmada():
    id_venta = request.args.get('id_venta')

    if not id_venta:
        return "ID de la venta no proporcionado", 400  

    username = "usuario"  
    password = "contraseña"

    try:
        conn = get_db_connection(username, password)
        cursor = conn.cursor()

        # Obtener los datos de la venta
        cursor.execute('SELECT * FROM Ventas WHERE IDVenta = ?', (id_venta,))
        venta = cursor.fetchone()

        if not venta:
            return "Factura no encontrada", 404  

        # Obtener información del cliente
        cursor.execute('SELECT * FROM Clientes WHERE IDCliente = ?', (venta[1],))
        cliente = cursor.fetchone()

        # Obtener información del vendedor
        cursor.execute('SELECT * FROM Vendedores WHERE IDVendedor = ?', (venta[2],))
        vendedor = cursor.fetchone()

        # Obtener información de la forma de pago
        cursor.execute('SELECT * FROM Formas_Pago WHERE id_pago = ?', (venta[3],))
        forma_pago = cursor.fetchone()

        # Obtener productos comprados desde Detalle_Ventas
        cursor.execute(''' 
            SELECT 
                p.nombre AS NombreProducto,
                dv.Cantidad,
                dv.PrecioUnitario,
                dv.SubTotal
            FROM 
                Detalle_Ventas dv
            JOIN 
                Productos p ON dv.IDProducto = p.id_producto
            WHERE 
                dv.IDVenta = ?
        ''', (id_venta,))

        productos = cursor.fetchall()

        productos_separados = [
            {
                'nombre': producto[0], 
                'cantidad': producto[1],
                'precio': producto[2],  
                'subtotal': producto[3]  
            }
            for producto in productos
        ]

        if not productos_separados:
            return "No se encontraron productos para esta venta.", 404

        # Obtener los totales desde la tabla Ventas
        subtotal = Decimal(venta[5])  
        descuento_aplicado = Decimal(venta[8])  
        subtotal_con_descuento = Decimal(venta[9])  
        iva = Decimal(venta[10])  
        total_con_iva = Decimal(venta[11])  

        conn.close()

        return render_template(
            'factura_confirmada.html',
            id_venta=id_venta,
            venta=venta,
            cliente=cliente,
            vendedor=vendedor,
            forma_pago=forma_pago,
            productos=productos_separados,
            subtotal=subtotal,
            descuento=descuento_aplicado,
            subtotal_con_descuento=subtotal_con_descuento,
            iva=iva,
            total_con_iva=total_con_iva
        )

    except Exception as e:
        print(f"Error al obtener la factura: {e}")
        return f"Error al obtener la factura: {e}", 500 
    

@app.route('/eliminar_factura', methods=['GET', 'POST'])
def eliminar_factura():
    message = None  
    factura_id = None
    if request.method == 'POST':
        factura_id = request.form['factura_id']

        username = "usuario"  
        password = "contraseña"

        try:
            conn = get_db_connection(username, password)
            cursor = conn.cursor()

            # Actualizar el estado de la factura a "Inactiva"
            cursor.execute("UPDATE Ventas SET Estado = 2 WHERE IDVenta = ?", (factura_id,))
            conn.commit()

            message = f"Factura {factura_id} marcada como inactiva correctamente."
        except Exception as e:
            message = f"Error al actualizar la factura: {str(e)}"
        finally:
            conn.close()

    return render_template('eliminar_factura.html', message=message)

   
# Ruta para crear una nueva factura
@app.route('/nueva', methods=['GET', 'POST'])
def nueva():
    if request.method == 'POST':
      
        pass
    return render_template('nueva.html')



@app.route('/reimprimir_factura', methods=['GET', 'POST'])
def reimprimir_factura():
    if request.method == 'POST':
        id_venta = request.form.get('id_venta')  # ID de la venta que el usuario quiere reimprimir

        if not id_venta:
            return render_template('reimprimir_factura.html', mensaje="Por favor ingrese un ID de factura")

        username = "usuario"  
        password = "contraseña"  

        try:
            conn = get_db_connection(username, password)
            cursor = conn.cursor()

            # Obtener los datos de la venta
            cursor.execute('SELECT * FROM Ventas WHERE IDVenta = ?', (id_venta,))
            venta = cursor.fetchone()

            if not venta:
                return render_template('reimprimir_factura.html', mensaje="Factura no encontrada")

            # Obtener información del cliente
            cursor.execute('SELECT * FROM Clientes WHERE IDCliente = ?', (venta[1],))
            cliente = cursor.fetchone()

            # Obtener información del vendedor
            cursor.execute('SELECT * FROM Vendedores WHERE IDVendedor = ?', (venta[2],))
            vendedor = cursor.fetchone()

            # Obtener información de la forma de pago
            cursor.execute('SELECT * FROM Formas_Pago WHERE id_pago = ?', (venta[3],))
            forma_pago = cursor.fetchone()

            # Obtener productos comprados desde Detalle_Ventas
            cursor.execute('''
                SELECT 
                    p.nombre AS NombreProducto,
                    dv.Cantidad,
                    dv.PrecioUnitario,
                    dv.SubTotal
                FROM 
                    Detalle_Ventas dv
                JOIN 
                    Productos p ON dv.IDProducto = p.id_producto
                WHERE 
                    dv.IDVenta = ?
            ''', (id_venta,))

            productos = cursor.fetchall()

            productos_separados = [
                {
                    'nombre': producto[0], 
                    'cantidad': producto[1],
                    'precio': producto[2],  
                    'subtotal': producto[3]  
                }
                for producto in productos
            ]

            if not productos_separados:
                return render_template('reimprimir_factura.html', mensaje="No se encontraron productos para esta venta.")

            # Obtener los totales desde la tabla Ventas
            subtotal = Decimal(venta[5])  
            descuento_aplicado = Decimal(venta[8])  
            subtotal_con_descuento = Decimal(venta[9])  
            iva = Decimal(venta[10])  
            total_con_iva = Decimal(venta[11])  

            conn.close()

            return render_template(
                'factura_confirmada.html',
                id_venta=id_venta,
                venta=venta,
                cliente=cliente,
                vendedor=vendedor,
                forma_pago=forma_pago,
                productos=productos_separados,
                subtotal=subtotal,
                descuento=descuento_aplicado,
                subtotal_con_descuento=subtotal_con_descuento,
                iva=iva,
                total_con_iva=total_con_iva
            )

        except Exception as e:
            print(f"Error al obtener la factura: {e}")
            return f"Error al obtener la factura: {e}", 500

    return render_template('reimprimir_factura.html')

# Ruta para terminar una factura
@app.route('/terminar_factura', methods=['GET', 'POST'])
def terminar_factura():
    if request.method == 'POST':
     return redirect(url_for('principal'))
        
    return render_template('terminar_factura.html')

app.register_blueprint(clientes_bp, url_prefix='/cliente') 

app.register_blueprint(inventario_bp, url_prefix='/inventario') 

if __name__ == "__main__":
    app.run(debug=True, port=5001)
