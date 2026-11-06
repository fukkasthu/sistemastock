import csv
import io
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, Response, url_for
from flask_login import login_required
from sqlalchemy import func

from app.models import Movimiento, Producto, Categoria

bp = Blueprint("reportes", __name__, url_prefix="/reportes")


def _fecha(valor):
    try:
        return datetime.strptime(valor, "%Y-%m-%d")
    except (TypeError, ValueError):
        return None


def _seguro(valor):
    # Evita que Excel interprete textos como fórmulas (=, +, -, @)
    if isinstance(valor, str) and valor[:1] in ("=", "+", "-", "@"):
        return "'" + valor
    return valor


def _filtrar():
    desde = _fecha(request.args.get("desde"))
    hasta = _fecha(request.args.get("hasta"))
    tipo = request.args.get("tipo", "")
    categoria_id = request.args.get("categoria", type=int)

    query = Movimiento.query.join(Producto)
    if desde:
        query = query.filter(Movimiento.fecha >= desde)
    if hasta:
        query = query.filter(Movimiento.fecha < hasta + timedelta(days=1))
    if tipo in ("entrada", "salida"):
        query = query.filter(Movimiento.tipo == tipo)
    if categoria_id:
        query = query.filter(Producto.categoria_id == categoria_id)
    return query, tipo, categoria_id


def _csv_response(nombre, encabezado, filas):
    buffer = io.StringIO()
    # ";" y BOM para que Excel en español abra bien columnas y tildes
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(encabezado)
    writer.writerows(filas)
    return Response(
        "\ufeff" + buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={nombre}"},
    )


@bp.route("/")
@login_required
def index():
    query, tipo, categoria_id = _filtrar()

    movimientos = query.order_by(Movimiento.fecha.desc()).limit(200).all()
    total_filas = query.count()

    totales = {"entrada": 0, "salida": 0}
    resumen = query.with_entities(Movimiento.tipo, func.sum(Movimiento.cantidad)).group_by(Movimiento.tipo).all()
    for t, total in resumen:
        totales[t] = int(total or 0)

    f_desde = request.args.get("desde", "")
    f_hasta = request.args.get("hasta", "")
    params = {
        k: v
        for k, v in {"desde": f_desde, "hasta": f_hasta, "tipo": tipo, "categoria": categoria_id or ""}.items()
        if v
    }

    return render_template(
        "reportes/index.html",
        movimientos=movimientos,
        total_filas=total_filas,
        totales=totales,
        categorias=Categoria.query.order_by(Categoria.nombre).all(),
        f_desde=f_desde,
        f_hasta=f_hasta,
        f_tipo=tipo,
        f_categoria=categoria_id,
        exportar_url=url_for("reportes.exportar_movimientos", **params),
    )


@bp.route("/movimientos.csv")
@login_required
def exportar_movimientos():
    query, _, _ = _filtrar()
    filas = [
        [
            m.fecha.strftime("%Y-%m-%d %H:%M"),
            _seguro(m.producto.sku),
            _seguro(m.producto.nombre),
            m.tipo,
            m.cantidad,
            _seguro(m.usuario.nombre if m.usuario else ""),
            _seguro(m.nota or ""),
        ]
        for m in query.order_by(Movimiento.fecha.desc()).all()
    ]
    return _csv_response(
        "movimientos.csv",
        ["Fecha", "SKU", "Producto", "Tipo", "Cantidad", "Usuario", "Nota"],
        filas,
    )


@bp.route("/inventario.csv")
@login_required
def exportar_inventario():
    filas = []
    for p in Producto.query.order_by(Producto.nombre).all():
        filas.append(
            [
                _seguro(p.sku),
                _seguro(p.nombre),
                _seguro(p.categoria.nombre if p.categoria else ""),
                _seguro(p.proveedor.nombre if p.proveedor else ""),
                round(p.precio),
                p.stock_actual,
                p.stock_minimo,
                round(p.precio * p.stock_actual),
                "Bajo stock" if p.bajo_stock else "OK",
            ]
        )
    return _csv_response(
        "inventario.csv",
        ["SKU", "Producto", "Categoría", "Proveedor", "Precio", "Stock", "Stock mínimo", "Valor total", "Estado"],
        filas,
    )