from flask import Blueprint, render_template, request
from datetime import datetime

reporte_ventas_vendedor_bp = Blueprint('reporte_ventas_vendedor', __name__)

@reporte_ventas_vendedor_bp.route('/reporte_ventas_vendedor', methods=['GET', 'POST'])
def reporte_ventas_vendedor():
    fecha_hoy = datetime.today().strftime('%d/%m/%Y') 
    vendedores = []
    ventas_por_vendedor = []
    total_general = 0
    message = ""

    from app import get_db_connection 

    username = "usuario"
    password = "contraseña"

    conn = None 

    try:
        conn = get_db_connection(username, password)
        cursor = conn.cursor()


        cursor.execute('''
            SELECT DISTINCT v.NombreVendedor
            FROM Ventas venta
            JOIN Vendedores v ON venta.IDVendedor = v.IDVendedor
            WHERE CAST(venta.FechaVenta AS DATE) = CAST(GETDATE() AS DATE)
            ORDER BY v.NombreVendedor ASC;
        ''')
        vendedores = sorted(set(row[0] for row in cursor.fetchall()))

        vendedor_inicial = request.form.get('vendedor_inicial')
        vendedor_final = request.form.get('vendedor_final') or vendedor_inicial

        if vendedor_inicial:
            # Consulta para obtener las ventas por vendedor en el rango seleccionado
            cursor.execute('''
                SELECT 
                    p.id_producto, 
                    p.nombre AS producto, 
                    p.descripcion, 
                    CAST(p.precio AS FLOAT) AS precio, 
                    dv.cantidad AS cantidad_vendida, 
                    (dv.cantidad * p.precio) AS total_vendido,
                    v.NombreVendedor
                FROM Ventas venta
                JOIN Detalle_Ventas dv ON venta.IDVenta = dv.IDVenta
                JOIN Productos p ON dv.IDProducto = p.id_producto
                JOIN Vendedores v ON venta.IDVendedor = v.IDVendedor
                WHERE CAST(venta.FechaVenta AS DATE) = CAST(GETDATE() AS DATE)
                AND v.NombreVendedor BETWEEN ? AND ?
                ORDER BY v.NombreVendedor, p.nombre;
            ''', (vendedor_inicial, vendedor_final))

            ventas_por_vendedor = [
                (row[0], row[1], row[2], row[3], row[4], row[5], row[6])
                for row in cursor.fetchall()
            ]

            # Calcular el total general de ventas por vendedor
            total_general = sum(row[5] for row in ventas_por_vendedor)

        else:
            message = "Seleccione al menos un vendedor para generar el reporte."

        conn.commit()

    except Exception as e:
        message = f"Error al obtener el reporte de ventas por vendedor: {str(e)}"
    finally:
        if conn:
            conn.close()

    return render_template(
        'reporte_ventas_vendedor.html',
        vendedores=vendedores,
        ventas=ventas_por_vendedor,
        fecha=fecha_hoy,
        message=message,
        total_general=total_general
    )
