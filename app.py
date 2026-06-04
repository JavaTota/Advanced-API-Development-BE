from application import create_app

from application.models import db

app = create_app('ProductionConfig')

with app.app_context():
    db.create_all()
    # db.drop_all()

