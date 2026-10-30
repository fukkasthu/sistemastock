from datetime import datetime, timedelta
from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func
from app import db
from app.models import Producto, Categoria, Movimiento

bp = Blueprint("main", __name__)


def _clp(valor):
    return "$" + f"{valor:,.0f}".replace(",", ".")


@bp.route("/")
@login_required
def index():
    # ---- KPIs ----
    total_productos = db.session.query(func.count(Producto.id)).scalar() or 0
    unidades = db.session.query(func.coalesce(func.sum(Producto.stock_actual), 0)).scalar()
    valor = db.session.query(
        func.coalesce(func.sum(Producto.stock_actual * Producto.precio), 0)
    ).scalar()
    bajo_stock = (
        Producto.query.filter(Producto.stock_actual <= Producto.stock_minimo)
        .order_by(Producto.stock_actual)
        .all()
    )

    # ---- Movimientos de los últimos 7 días ----
    hoy = datetime.utcnow().date()
    dias = [hoy - timedelta(days=i) for i in range(6, -1, -1)]
    desde = datetime.combine(dias[0], datetime.min.time())
    filas = (
        db.session.query(func.date(Movimiento.fecha), Movimiento.tipo, func.sum(Movimiento.cantidad))
        .filter(Movimiento.fecha >= desde)
        .group_by(func.date(Movimiento.fecha), Movimiento.tipo)
        .all()
    )
    totales = {(str(f), t): int(c) for f, t, c in filas}
    mov_labels = [d.strftime("%d-%m") for d in dias]
    mov_entradas = [totales.get((str(d), "entrada"), 0) for d in dias]
    mov_salidas = [totales.get((str(d), "salida"), 0) for d in dias]

    # ---- Stock por categoría ----
    cats = (
        db.session.query(
            func.coalesce(Categoria.nombre, "Sin categoría"),
            func.coalesce(func.sum(Producto.stock_actual), 0),
        )
        .select_from(Producto)
        .outerjoin(Categoria, Producto.categoria_id == Categoria.id)
        .group_by(Categoria.nombre)
        .all()
    )
    cat_labels = [c[0] for c in cats]
    cat_values = [int(c[1]) for c in cats]

    # ---- Top 5 productos con más salidas (30 días) ----
    hace30 = datetime.utcnow() - timedelta(days=30)
    top = (
        db.session.query(Producto.nombre, func.sum(Movimiento.cantidad))
        .join(Movimiento, Movimiento.producto_id == Producto.id)
        .filter(Movimiento.tipo == "salida", Movimiento.fecha >= hace30)
        .group_by(Producto.id, Producto.nombre)
        .order_by(func.sum(Movimiento.cantidad).desc())
        .limit(5)
        .all()
    )
    top_labels = [t[0] for t in top]
    top_values = [int(t[1]) for t in top]

    ultimos = Movimiento.query.order_by(Movimiento.fecha.desc()).limit(5).all()

    return render_template(
        "index.html",
        total_productos=total_productos,
        unidades=int(unidades),
        valor=_clp(valor),
        bajo_stock=bajo_stock,
        mov_labels=mov_labels,
        mov_entradas=mov_entradas,
        mov_salidas=mov_salidas,
        cat_labels=cat_labels,
        cat_values=cat_values,
        top_labels=top_labels,
        top_values=top_values,
        ultimos=ultimos,
    )