from flask import Blueprint, current_app
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy(current_app)

modulo_bbdd = Blueprint("modulo_bbdd", __name__, static_folder="static", template_folder="templates")


class User(db.Model, UserMixin):
    '''
    Tabla de usuarios de la base de datos:
        - id: Identificador único del usuario
        - username: Nombre de usuario
        - email: Correo electrónico del usuario
        - password_hash: Hash de la contraseña del usuario
    '''
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(60), unique=True)
    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
        }


db.create_all()


class Modelo(db.Model):
    '''
    Tabla de modelos de la base de datos:
        - id: Identificador único del modelo
        - nombre: Nombre del modelo
        - creador: Nombre del usuario que ha creado el modelo
        - fecha_creacion: Fecha de creación del modelo
        - compartir: Código para compartir el modelo
        - publico: Indica si el modelo es público o no
    '''
    __tablename__ = 'modelos'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    creador = db.Column(db.String(100))
    fecha_creacion = db.Column(db.String(100))
    compartir = db.Column(db.String(100), unique=True)
    publico = db.Column(db.Boolean)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'creador': self.creador,
            'fecha_creacion': self.fecha_creacion,
            'compartir': self.compartir,
            'publico': self.publico
        }


db.create_all()


class Permisos(db.Model):
    '''
    Tabla de permisos de acceso a los modelos de la base de datos:
        - id_modelo: Identificador único del modelo
        - id_usuario: Identificador único del usuario
    '''
    __tablename__ = 'permisos'
    id_modelo = db.Column(db.Integer, db.ForeignKey('modelos.id'))
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    modelo = db.relationship("Modelo", backref=backref("modelos", uselist=False))
    usuario = db.relationship("User", backref=backref("usuarios", uselist=False))

    __table_args__ = (
        db.PrimaryKeyConstraint(
            id_modelo, id_usuario,
        ),
    )

    @property
    def serialize(self):
        return {
            'id_modelo': self.id_modelo,
            'id_usuario': self.id_usuario,
        }


db.create_all()


@modulo_bbdd.route('/modulo_bbdd/test')
def modulo_bbdd_test():
    db.create_all()

    return 'OK'
