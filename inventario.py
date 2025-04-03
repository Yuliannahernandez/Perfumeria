from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime

inventario_bp = Blueprint('inventario', __name__)

@inventario_bp.route('/agregar_producto', methods=['GET', 'POST'])
def agregar_producto():
    message = ""
    tipos_productos = []  # Para almacenar los tipos de productos
    productos = []  # Para almacenar los productos del inventario
    
    from app import get_db_connection 

    username = "usuario"
    password = "contraseña"

    try:
       
        conn = get_db_connection(username, password) 
        cursor = conn.cursor()

        if request.method == 'POST':
            nombre = request.form['nombre']
            descripcion = request.form['descripcion']
            peso_ml = request.form['peso_ml']
            marca = request.form['marca']
            concentracion = request.form['concentracion']
            precio = request.form['precio']
            tipo_producto_id = request.form['tipo_producto_id']
            existencia_estantes = request.form['existencia_estantes']
            existencia_bodega = request.form['existencia_bodega']
           

            cursor.execute("SELECT TOP 1 id_producto FROM Productos ORDER BY id_producto DESC")
            ultimo_producto = cursor.fetchone()

            if ultimo_producto:
       
                nuevo_id = ultimo_producto[0] + 1
            else:
             
                nuevo_id = 1

            id_producto = nuevo_id

    
            cursor.execute("""
                INSERT INTO Productos ( nombre, descripcion, peso_ml, marca, concentracion, precio, tipo_producto_id, existencia_estantes, existencia_bodega)
                VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ( nombre, descripcion, peso_ml, marca, concentracion, precio, tipo_producto_id, existencia_estantes, existencia_bodega))

            conn.commit()
            message = "Producto agregado exitosamente."


        cursor.execute("SELECT id_tipo_producto, nombre FROM Tipos_Productos")
        tipos_productos = cursor.fetchall()

        # Consultamos todos los productos en inventario
        cursor.execute("""
            SELECT id_producto, nombre, descripcion, precio, existencia_estantes, existencia_bodega
            FROM Productos
        """)
        productos = cursor.fetchall()

                # Agregamos el símbolo de colones a los precios
        for i, producto in enumerate(productos):
            precio_colones = producto[3]  
            productos[i] = list(producto)
            productos[i][3] = "₡{:,.2f}".format(precio_colones)  # Formateamos el precio con símbolo de colones


    except Exception as e:
        message = f"Error al agregar producto: {str(e)}"
    finally:
        if conn:
            conn.close()

    return render_template('agregar_producto.html', tipos_productos=tipos_productos, productos=productos, message=message)

@inventario_bp.route('/ver_producto', methods=['GET', 'POST'])
def ver_producto():
    message = ""
    productos_por_tipo = {}  
    search_id = request.args.get('search_id', '').strip()

    from app import get_db_connection  

   
    username = "usuario"
    password = "contraseña"

    if request.method == 'POST':
        search_id = request.form['search_id']
    
    try:
        
        conn = get_db_connection(username, password)
        cursor = conn.cursor()

        
        if search_id:
            cursor.execute("""
                SELECT p.id_producto, p.nombre, p.descripcion, p.precio, p.existencia_estantes, p.existencia_bodega, tp.nombre AS tipo_producto
                FROM Productos p
                JOIN tipos_productos tp ON p.tipo_producto_id = tp.id_tipo_producto
                LEFT JOIN productos_inactivos pi ON p.id_producto = pi.id_producto
                WHERE pi.id_producto IS NULL AND (p.id_producto LIKE ? OR p.nombre LIKE ?)
            """, ('%' + search_id + '%', '%' + search_id + '%'))
        else:
            
            cursor.execute("""
                SELECT p.id_producto, p.nombre, p.descripcion, p.precio, p.existencia_estantes, p.existencia_bodega, tp.nombre AS tipo_producto
                FROM Productos p
                JOIN tipos_productos tp ON p.tipo_producto_id = tp.id_tipo_producto
                LEFT JOIN productos_inactivos pi ON p.id_producto = pi.id_producto
                WHERE pi.id_producto IS NULL
            """)

        productos = cursor.fetchall()

        # Agrupar los productos por tipo
        for producto in productos:
            tipo_producto = producto[6]  
            if tipo_producto not in productos_por_tipo:
                productos_por_tipo[tipo_producto] = []
            productos_por_tipo[tipo_producto].append({
                'id_producto': producto[0],
                'nombre': producto[1],
                'descripcion': producto[2],
                'precio': "₡{:,.2f}".format(producto[3]),
                'existencia_estantes': producto[4],
                'existencia_bodega': producto[5]
            })
    
    except Exception as e:
        message = f"Error al obtener productos: {str(e)}"
    finally:
        if conn:
            conn.close()

    return render_template('ver_producto.html', productos_por_tipo=productos_por_tipo, message=message, search_id=search_id)



@inventario_bp.route('/modificar_producto/<int:id>', methods=['GET', 'POST'])
def modificar_producto(id):
    message = ""
    producto = None
    tipos_productos = []  
    
    from app import get_db_connection 

   
    username = "usuario"
    password = "contraseña"

    try:

        conn = get_db_connection(username, password)
        cursor = conn.cursor()

   
        cursor.execute("SELECT * FROM Productos WHERE id_producto = ?", (id,))
        producto = cursor.fetchone()

        if not producto:
            message = "Producto no encontrado."
            return redirect(url_for('inventario.ver_producto'))

        cursor.execute("SELECT id_tipo_producto, nombre FROM Tipos_Productos")
        tipos_productos = cursor.fetchall()

        if request.method == 'POST':
            nombre = request.form['nombre']
            descripcion = request.form['descripcion']
            peso_ml = request.form['peso_ml']
            marca = request.form['marca']
            concentracion = request.form['concentracion']
            precio = request.form['precio']
            tipo_producto_id = request.form['tipo_producto_id']
            existencia_estantes = request.form['existencia_estantes']
            existencia_bodega = request.form['existencia_bodega']

            # Actualizar en la base de datos
            cursor.execute("""
                UPDATE Productos 
                SET nombre = ?, descripcion = ?, peso_ml = ?, marca = ?, concentracion = ?, precio = ?, 
                    tipo_producto_id = ?, existencia_estantes = ?, existencia_bodega = ?
                WHERE id_producto = ?
            """, (nombre, descripcion, peso_ml, marca, concentracion, precio, tipo_producto_id, existencia_estantes, existencia_bodega, id))

            conn.commit()
            message = "Producto actualizado correctamente."
            return redirect(url_for('inventario.ver_producto'))

    except Exception as e:
        message = f"Error al modificar producto: {str(e)}"
    finally:
        if conn:
            conn.close()

    return render_template('modificar_producto.html', producto=producto, tipos_productos=tipos_productos, message=message)
from flask import request, jsonify

@inventario_bp.route('/eliminar_producto/<int:id>', methods=['POST'])
def eliminar_producto(id):
    message = ""

    from app import get_db_connection  

    username = "usuario"
    password = "contraseña"

    try:

        conn = get_db_connection(username, password)
        cursor = conn.cursor()


        cursor.execute("SELECT * FROM Productos WHERE id_producto = ?", (id,))
        producto = cursor.fetchone()

        if not producto:
            message = "Producto no encontrado."
            return redirect(url_for('inventario.ver_productos'))


        cursor.execute("SELECT * FROM productos_inactivos WHERE id_producto = ?", (id,))
        inactivo = cursor.fetchone()

        if inactivo:
            message = "El producto ya está inactivo."
        else:
            # Insertar el producto en la tabla de productos inactivos
            cursor.execute("INSERT INTO productos_inactivos (id_producto) VALUES (?)", (id,))
            conn.commit()
            message = "Producto marcado como inactivo."

    except Exception as e:
        message = f"Error al marcar producto como inactivo: {str(e)}"
    finally:
        if conn:
            conn.close()

  
    return redirect(url_for('inventario.ver_producto', message=message))
