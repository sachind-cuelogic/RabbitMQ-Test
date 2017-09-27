from flask_mongoalchemy import MongoAlchemy

db = MongoAlchemy()

class Base(db.Document):
    created_at = db.CreatedField()
    updated_at = db.ModifiedField()

class Domains(Base):
    company = db.StringField()
    domain = db.StringField()
    source = db.StringField()

class Websites(Base):
    company = db.StringField()
    website = db.StringField()
    source = db.StringField()
