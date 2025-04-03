from flask import Blueprint, render_template
from datetime import datetime

reportes_bp = Blueprint('reportes', __name__)

@reportes_bp.route('/reporte_ventas')
def reporte_ventas():
    fecha_hoy = datetime.today().strftime('%Y-%m-%d') 
    productos_vendidos = []
    total_general = 0
    message = ""

    from app import get_db_connection  

    username = "usuario"
    password = "contraseña"

    try:
        
        conn = get_db_connection(username, password) 
        cursor = conn.cursor()

        # Consulta para obtener las ventas agrupadas por producto
        cursor.execute('''
            SELECT 
    p.id_producto AS IdProducto,
    tp.nombre AS Categoria,
    p.nombre AS Codigo,
    CONCAT(p.nombre, ', ', p.peso_ml, ' ml, ', p.marca, ', ', p.concentracion) AS DescripcionCompleta,
    p.precio AS Precio,
    SUM(d.Cantidad) AS CantidadVendida,
    SUM(d.SubTotal) AS Total
    FROM Ventas v
    JOIN Detalle_Ventas d ON v.IDVenta = d.IDVenta
    JOIN Productos p ON d.IDProducto = p.id_producto
    JOIN Tipos_Productos tp ON p.tipo_producto_id = tp.id_tipo_producto
    WHERE CAST(v.FechaVenta AS DATE) = CAST(GETDATE() AS DATE)
    GROUP BY p.id_producto, tp.nombre, p.nombre, p.peso_ml, p.marca, p.concentracion, p.precio;

        ''')

        productos_vendidos = cursor.fetchall()

        # Calcular el total general de las ventas
        total_general = sum(producto.Total for producto in productos_vendidos)

        conn.commit()

    except Exception as e:
        message = f"Error al obtener el reporte: {str(e)}"

    finally:
        if conn:
            conn.close()

    return render_template('reportes_1.html', productos=productos_vendidos, fecha=fecha_hoy, message=message, total_general=total_general)
