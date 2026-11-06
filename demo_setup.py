"""Prepara la demo en el arranque: crea el usuario demo y carga los datos de ejemplo."""
from app import create_app, db
from app.models import Usuario


def asegurar_usuario_demo():
    app = create_app()
    with app.app_context():
        if Usuario.query.count() == 0:
            u = Usuario(nombre="Cuenta Demo", email="demo@sistemastock.app", rol="admin")
            u.set_password("demo1234")
            db.session.add(u)
            db.session.commit()
            print("Usuario demo creado.")


if __name__ == "__main__":
    asegurar_usuario_demo()
    import seed

    seed.main()