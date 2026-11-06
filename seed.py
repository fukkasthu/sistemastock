"""Carga datos de ejemplo.

Uso:
    python seed.py           (solo si no hay productos)
    python seed.py --reset   (borra productos, movimientos, categorías y proveedores y recarga)
"""
import random
import sys
from datetime import datetime, timedelta

from app import create_app, db
from app.models import Usuario, Categoria, Proveedor, Producto, Movimiento

random.seed(42)

CATEGORIAS = ["Embalaje", "Equipos", "Seguridad (EPP)", "Oficina", "Limpieza"]

PROVEEDORES = [
    ("Embalajes del Sur", "Carolina Muñoz", "+56 9 1111 2222"),
    ("Distribuidora Andes", "Felipe Rojas", "+56 9 3333 4444"),
    ("Seguridad Total Ltda.", "Marcela Soto", "+56 9 5555 6666"),
    ("Oficina Express", "Ignacio Vargas", "+56 9 7777 8888"),
]

# (sku, nombre, precio CLP, stock mínimo, categoría, proveedor)
PRODUCTOS = [
    ("EMB-001", "Caja de cartón 40x30x30 cm", 850, 60, "Embalaje", "Embalajes del Sur"),
    ("EMB-002", "Cinta de embalaje transparente 48 mm", 1290, 40, "Embalaje", "Embalajes del Sur"),
    ("EMB-003", "Film stretch 50 cm x 300 m", 8900, 15, "Embalaje", "Embalajes del Sur"),
    ("EMB-004", "Bolsa de polietileno 30x40 cm (paquete 100)", 2490, 25, "Embalaje", "Embalajes del Sur"),
    ("EMB-005", "Esquinero de cartón 50 mm", 390, 80, "Embalaje", "Embalajes del Sur"),
    ("EMB-006", "Etiquetas térmicas 100x150 mm (rollo)", 5990, 20, "Embalaje", "Distribuidora Andes"),
    ("EQU-001", "Transpaleta manual 2.500 kg", 189990, 2, "Equipos", "Distribuidora Andes"),
    ("EQU-002", "Cuchillo cartonero profesional", 2990, 15, "Equipos", "Distribuidora Andes"),
    ("EQU-003", "Pistola de etiquetas 1 línea", 12990, 4, "Equipos", "Distribuidora Andes"),
    ("EQU-004", "Dispensador de cinta de embalaje", 4590, 8, "Equipos", "Distribuidora Andes"),
    ("EQU-005", "Carro plataforma 300 kg", 59990, 3, "Equipos", "Distribuidora Andes"),
    ("SEG-001", "Guantes de seguridad (par)", 1990, 30, "Seguridad (EPP)", "Seguridad Total Ltda."),
    ("SEG-002", "Casco de seguridad blanco", 4990, 10, "Seguridad (EPP)", "Seguridad Total Ltda."),
    ("SEG-003", "Chaleco reflectante", 3490, 12, "Seguridad (EPP)", "Seguridad Total Ltda."),
    ("SEG-004", "Zapatos de seguridad (par)", 29990, 6, "Seguridad (EPP)", "Seguridad Total Ltda."),
    ("SEG-005", "Lentes de seguridad transparentes", 1490, 25, "Seguridad (EPP)", "Seguridad Total Ltda."),
    ("SEG-006", "Faja lumbar", 9990, 6, "Seguridad (EPP)", "Seguridad Total Ltda."),
    ("OFI-001", "Resma de papel carta 500 hojas", 4290, 20, "Oficina", "Oficina Express"),
    ("OFI-002", "Marcador permanente negro", 690, 40, "Oficina", "Oficina Express"),
    ("OFI-003", "Carpeta archivadora oficio", 2190, 15, "Oficina", "Oficina Express"),
    ("OFI-004", "Etiquetas adhesivas blancas (caja)", 3290, 12, "Oficina", "Oficina Express"),
    ("LIM-001", "Escoba industrial", 3990, 8, "Limpieza", "Distribuidora Andes"),
    ("LIM-002", "Detergente industrial 5 L", 6990, 10, "Limpieza", "Distribuidora Andes"),
    ("LIM-003", "Bolsas de basura 80x110 cm (paquete 10)", 2990, 20, "Limpieza", "Distribuidora Andes"),
    ("LIM-004", "Paños multiuso (pack 10)", 3490, 12, "Limpieza", "Distribuidora Andes"),
]

NOTAS_SALIDA = ["Despacho pedido", "Pedido cliente", "Uso interno", "Reposición de sucursal"]
NOTAS_ENTRADA = ["Recepción de proveedor", "Compra mensual", "Reposición de stock"]

# Productos que terminarán bajo el stock mínimo (para las alertas del dashboard)
BAJOS = {2, 8, 14, 20}


def main():
    reset = "--reset" in sys.argv
    app = create_app()
    with app.app_context():
        admin = Usuario.query.order_by(Usuario.id).first()
        if admin is None:
            print("Primero registra un usuario en http://127.0.0.1:5000/registro y vuelve a ejecutar.")
            return

        if reset:
            Movimiento.query.delete()
            Producto.query.delete()
            Categoria.query.delete()
            Proveedor.query.delete()
            db.session.commit()
        elif Producto.query.count() > 0:
            print("Ya hay productos. Usa 'python seed.py --reset' para reemplazarlos por los datos de ejemplo.")
            return

        cats = {n: Categoria(nombre=n) for n in CATEGORIAS}
        provs = {n: Proveedor(nombre=n, contacto=c, telefono=t) for n, c, t in PROVEEDORES}
        db.session.add_all(list(cats.values()) + list(provs.values()))

        ahora = datetime.utcnow()
        inicio = ahora - timedelta(days=30)
        total_mov = 0

        def mov(p, tipo, cant, fecha, nota):
            db.session.add(
                Movimiento(producto=p, usuario=admin, tipo=tipo, cantidad=cant, nota=nota, fecha=fecha)
            )

        for i, (sku, nombre, precio, minimo, cat, prov) in enumerate(PRODUCTOS):
            p = Producto(
                sku=sku, nombre=nombre, precio=precio, stock_actual=0, stock_minimo=minimo,
                categoria=cats[cat], proveedor=provs[prov],
            )
            db.session.add(p)

            stock = random.randint(minimo * 4, minimo * 10)
            mov(p, "entrada", stock, inicio, "Stock inicial")
            total_mov += 1

            eventos = sorted(
                inicio + timedelta(days=1, seconds=random.randint(0, 28 * 24 * 3600))
                for _ in range(random.randint(8, 16))
            )
            for fecha in eventos:
                if random.random() < 0.3:
                    cant = random.randint(minimo * 2, minimo * 6)
                    stock += cant
                    mov(p, "entrada", cant, fecha, random.choice(NOTAS_ENTRADA))
                    total_mov += 1
                elif stock > 0:
                    cant = random.randint(1, min(stock, max(1, minimo * 2)))
                    stock -= cant
                    mov(p, "salida", cant, fecha, random.choice(NOTAS_SALIDA))
                    total_mov += 1

            # Ajuste final: algunos productos quedan bajo el mínimo, el resto sobre él
            if i in BAJOS:
                objetivo = random.randint(0, max(0, minimo - 1))
                if stock > objetivo:
                    mov(p, "salida", stock - objetivo, ahora - timedelta(hours=random.randint(1, 20)), "Despacho pedido")
                    stock = objetivo
                    total_mov += 1
            elif stock <= minimo:
                cant = minimo * 3
                mov(p, "entrada", cant, ahora - timedelta(hours=random.randint(1, 20)), "Recepción de proveedor")
                stock += cant
                total_mov += 1

            p.stock_actual = stock

        db.session.commit()
        print(f"Listo: {len(PRODUCTOS)} productos, {total_mov} movimientos, {len(BAJOS)} con bajo stock.")


if __name__ == "__main__":
    main()