from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required
from sqlalchemy import func
from app import db
from app.forms import CategoriaForm, ProveedorForm
from app.models import Categoria, Proveedor

bp = Blueprint("catalogos", __name__)


# ---------- Categorías ----------
@bp.route("/categorias", methods=["GET", "POST"])
@login_required
def categorias():
    form = CategoriaForm()
    if form.validate_on_submit():
        nombre = form.nombre.data.strip()
        if Categoria.query.filter(func.lower(Categoria.nombre) == nombre.lower()).first():
            flash("Esa categoría ya existe.", "warning")
        else:
            db.session.add(Categoria(nombre=nombre))
            db.session.commit()
            flash("Categoría creada.", "success")
            return redirect(url_for("catalogos.categorias"))
    items = Categoria.query.order_by(Categoria.nombre).all()
    return render_template("catalogos/categorias.html", form=form, items=items)


@bp.route("/categorias/<int:id>/editar", methods=["GET", "POST"])
@login_required
def categoria_editar(id):
    c = db.get_or_404(Categoria, id)
    form = CategoriaForm(obj=c)
    if form.validate_on_submit():
        nombre = form.nombre.data.strip()
        repetida = Categoria.query.filter(
            func.lower(Categoria.nombre) == nombre.lower(), Categoria.id != c.id
        ).first()
        if repetida:
            flash("Ya existe otra categoría con ese nombre.", "warning")
        else:
            c.nombre = nombre
            db.session.commit()
            flash("Categoría actualizada.", "success")
            return redirect(url_for("catalogos.categorias"))
    return render_template(
        "catalogos/form.html",
        form=form,
        titulo="Editar categoría",
        volver=url_for("catalogos.categorias"),
    )


@bp.route("/categorias/<int:id>/eliminar", methods=["POST"])
@login_required
def categoria_eliminar(id):
    c = db.get_or_404(Categoria, id)
    if c.productos:
        flash("No se puede eliminar: tiene productos asociados.", "warning")
    else:
        db.session.delete(c)
        db.session.commit()
        flash("Categoría eliminada.", "info")
    return redirect(url_for("catalogos.categorias"))


# ---------- Proveedores ----------
@bp.route("/proveedores", methods=["GET", "POST"])
@login_required
def proveedores():
    form = ProveedorForm()
    if form.validate_on_submit():
        nombre = form.nombre.data.strip()
        if Proveedor.query.filter(func.lower(Proveedor.nombre) == nombre.lower()).first():
            flash("Ese proveedor ya existe.", "warning")
        else:
            db.session.add(
                Proveedor(
                    nombre=nombre,
                    contacto=(form.contacto.data or "").strip() or None,
                    telefono=(form.telefono.data or "").strip() or None,
                )
            )
            db.session.commit()
            flash("Proveedor creado.", "success")
            return redirect(url_for("catalogos.proveedores"))
    items = Proveedor.query.order_by(Proveedor.nombre).all()
    return render_template("catalogos/proveedores.html", form=form, items=items)


@bp.route("/proveedores/<int:id>/editar", methods=["GET", "POST"])
@login_required
def proveedor_editar(id):
    p = db.get_or_404(Proveedor, id)
    form = ProveedorForm(obj=p)
    if form.validate_on_submit():
        nombre = form.nombre.data.strip()
        repetido = Proveedor.query.filter(
            func.lower(Proveedor.nombre) == nombre.lower(), Proveedor.id != p.id
        ).first()
        if repetido:
            flash("Ya existe otro proveedor con ese nombre.", "warning")
        else:
            p.nombre = nombre
            p.contacto = (form.contacto.data or "").strip() or None
            p.telefono = (form.telefono.data or "").strip() or None
            db.session.commit()
            flash("Proveedor actualizado.", "success")
            return redirect(url_for("catalogos.proveedores"))
    return render_template(
        "catalogos/form.html",
        form=form,
        titulo="Editar proveedor",
        volver=url_for("catalogos.proveedores"),
    )


@bp.route("/proveedores/<int:id>/eliminar", methods=["POST"])
@login_required
def proveedor_eliminar(id):
    p = db.get_or_404(Proveedor, id)
    if p.productos:
        flash("No se puede eliminar: tiene productos asociados.", "warning")
    else:
        db.session.delete(p)
        db.session.commit()
        flash("Proveedor eliminado.", "info")
    return redirect(url_for("catalogos.proveedores"))