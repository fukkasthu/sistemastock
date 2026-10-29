from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    rol = db.Column(db.String(20), default="operador")  # admin / operador

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Usuario, int(user_id))


class Categoria(db.Model):
    __tablename__ = "categorias"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), unique=True, nullable=False)
    productos = db.relationship("Producto", back_populates="categoria")


class Proveedor(db.Model):
    __tablename__ = "proveedores"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    contacto = db.Column(db.String(120))
    telefono = db.Column(db.String(30))
    productos = db.relationship("Producto", back_populates="proveedor")


class Producto(db.Model):
    __tablename__ = "productos"
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(40), unique=True, nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    precio = db.Column(db.Float, default=0)
    stock_actual = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=5)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"))
    proveedor_id = db.Column(db.Integer, db.ForeignKey("proveedores.id"))

    categoria = db.relationship("Categoria", back_populates="productos")
    proveedor = db.relationship("Proveedor", back_populates="productos")
    movimientos = db.relationship("Movimiento", back_populates="producto")

    @property
    def bajo_stock(self):
        return self.stock_actual <= self.stock_minimo


class Movimiento(db.Model):
    __tablename__ = "movimientos"
    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"))
    tipo = db.Column(db.String(10), nullable=False)  # entrada / salida
    cantidad = db.Column(db.Integer, nullable=False)
    nota = db.Column(db.String(200))
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    producto = db.relationship("Producto", back_populates="movimientos")
    usuario = db.relationship("Usuario")