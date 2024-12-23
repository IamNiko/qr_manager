from app import app, db

if __name__ == '__main__':
    with app.app_context():
        # Crear todas las tablas si no existen
        db.create_all()
    app.run(debug=True)
    