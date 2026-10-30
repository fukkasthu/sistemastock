from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.forms import MovimientoForm
from app.models import Producto, Movimiento

bp = Blueprint("movimientos", __name__, url_prefix="/movimientos")


@bp.route("/")
@login_required
def lista():
    page = request.args.get("page", 1, type=int)
    tipo = request.args.get("tipo", "")
    query = Movimiento.query
    if tipo in ("entrada", "salida"):
        query = query.filter_by(tipo=tipo)
    pagination = query.order_by(Movimiento.fecha.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    return render_template("movimientos/lista.html", pagination=pagination, tipo=tipo)


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    form = MovimientoForm()
    form.producto_id.choices = [
        (p.id, f"{p.sku} — {p.nombre} (stock: {p.stock_actual})")
        for p in Producto.query.order_by(Producto.nombre)
    ]
    if request.method == "GET" and request.args.get("producto", type=int):
        form.producto_id.data = request.args.get("producto", type=int)

    if form.validate_on_submit():
        p = db.session.get(Producto, form.producto_id.data)
        cantidad = form.cantidad.data
        if p is None:
            flash("Producto no válido.", "danger")
        elif form.tipo.data == "salida" and cantidad > p.stock_actual:
            flash(f"Stock insuficiente: quedan {p.stock_actual} unidades.", "danger")
        else:
            p.stock_actual += cantidad if form.tipo.data == "entrada" else -cantidad
            db.session.add(
                Movimiento(
                    producto_id=p.id,
                    usuario_id=current_user.id,
                    tipo=form.tipo.data,
                    cantidad=cantidad,
                    nota=(form.nota.data or "").strip() or None,
                )
            )
            db.session.commit()
            flash(f"Movimiento registrado. Stock actual: {p.stock_actual}.", "success")
            return redirect(url_for("movimientos.lista"))
    return render_template("movimientos/form.html", form=form)