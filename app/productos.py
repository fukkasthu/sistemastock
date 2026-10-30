from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_
from app import db
from app.forms import ProductoForm
from app.models import Producto, Categoria, Proveedor, Movimiento

bp = Blueprint("productos", __name__, url_prefix="/productos")


def _cargar_opciones(form):
    form.categoria_id.choices = [(0, "— Sin categoría —")] + [
        (c.id, c.nombre) for c in Categoria.query.order_by(Categoria.nombre)
    ]
    form.proveedor_id.choices = [(0, "— Sin proveedor —")] + [
        (p.id, p.nombre) for p in Proveedor.query.order_by(Proveedor.nombre)
    ]


@bp.route("/")
@login_required
def lista():
    q = request.args.get("q", "").strip()
    solo_bajo = request.args.get("bajo") == "1"
    page = request.args.get("page", 1, type=int)

    query = Producto.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Producto.nombre.ilike(like), Producto.sku.ilike(like)))
    if solo_bajo:
        query = query.filter(Producto.stock_actual <= Producto.stock_minimo)

    pagination = query.order_by(Producto.nombre).paginate(page=page, per_page=10, error_out=False)
    return render_template("productos/lista.html", pagination=pagination, q=q, solo_bajo=solo_bajo)


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    form = ProductoForm()
    _cargar_opciones(form)
    if form.validate_on_submit():
        sku = form.sku.data.strip()
        if Producto.query.filter_by(sku=sku).first():
            form.sku.errors = list(form.sku.errors) + ["Ya existe un producto con ese SKU."]
        else:
            p = Producto(
                sku=sku,
                nombre=form.nombre.data.strip(),
                precio=form.precio.data,
                stock_actual=form.stock_actual.data,
                stock_minimo=form.stock_minimo.data,
                categoria_id=form.categoria_id.data or None,
                proveedor_id=form.proveedor_id.data or None,
            )
            db.session.add(p)
            db.session.flush()
            # Si parte con stock, queda registrado como movimiento (trazabilidad)
            if p.stock_actual > 0:
                db.session.add(
                    Movimiento(
                        producto_id=p.id,
                        usuario_id=current_user.id,
                        tipo="entrada",
                        cantidad=p.stock_actual,
                        nota="Stock inicial",
                    )
                )
            db.session.commit()
            flash("Producto creado.", "success")
            return redirect(url_for("productos.lista"))
    return render_template("productos/form.html", form=form, titulo="Nuevo producto", editando=False)


@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
def editar(id):
    p = db.get_or_404(Producto, id)
    form = ProductoForm(obj=p)
    del form.stock_actual  # el stock solo cambia mediante movimientos
    _cargar_opciones(form)
    if request.method == "GET":
        form.categoria_id.data = p.categoria_id or 0
        form.proveedor_id.data = p.proveedor_id or 0

    if form.validate_on_submit():
        sku = form.sku.data.strip()
        repetido = Producto.query.filter(Producto.sku == sku, Producto.id != p.id).first()
        if repetido:
            form.sku.errors = list(form.sku.errors) + ["Ya existe un producto con ese SKU."]
        else:
            p.sku = sku
            p.nombre = form.nombre.data.strip()
            p.precio = form.precio.data
            p.stock_minimo = form.stock_minimo.data
            p.categoria_id = form.categoria_id.data or None
            p.proveedor_id = form.proveedor_id.data or None
            db.session.commit()
            flash("Producto actualizado.", "success")
            return redirect(url_for("productos.lista"))
    return render_template("productos/form.html", form=form, titulo="Editar producto", editando=True)


@bp.route("/<int:id>/eliminar", methods=["POST"])
@login_required
def eliminar(id):
    p = db.get_or_404(Producto, id)
    if p.movimientos:
        flash("No se puede eliminar: el producto tiene movimientos registrados.", "warning")
    else:
        db.session.delete(p)
        db.session.commit()
        flash("Producto eliminado.", "info")
    return redirect(url_for("productos.lista"))