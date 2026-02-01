"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, Character
# from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints


@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/user', methods=['GET'])
def handle_hello():
    # [{obj con metadata},{},{}]
    users = User.query.all()
    return jsonify([u.serialize() for u in users]), 200


@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({'msg': 'No llegó data'})

    email = data.get('email')
    name = data.get('name')
    password = data.get('password')
    is_active = data.get('is_active')

    if not email or not name or not password or not is_active:
        return jsonify({'msg': 'Necesitamos todos los valores'})

    new_user = User(
        email=email,
        name=name,
        password=password,
        is_active=is_active
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'new_user': new_user.serialize()}), 201


@app.route('/user/<int:user_id>', methods=['GET'])
def get_single_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'No encontramos un usuario con ese id'}), 404

    return jsonify({'user': user.serialize()}), 200


@app.route('/users/favorites/<int:user_id>', methods=['GET'])
def get_user_favorites(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'No encontramos un usuario con ese id'})

    fav_planets = user.planets
    fav_planets_serialized = [p.serialize() for p in fav_planets]

    fav_people = user.favorites_people
    fav_people_serialized = [people.serialize() for people in fav_people]

    return jsonify({'fav_planets':  fav_planets_serialized, 'fav_people':   fav_people_serialized}), 200


@app.route('/people', methods=['GET'])
def inicio():

    people = Character.query.all()

    return jsonify([character.serialize() for character in people]), 200


@app.route('/people/<int:character_id>', methods=['GET'])
def get_single_character(character_id):
    character_single = Character.query.get(character_id)
    if not character_single:
        return jsonify({'msg': 'No encontramos un personaje con ese id'}), 404

    return jsonify({'character': character_single.serialize()}), 200


@app.route('/planet', methods=['GET'])
def get_all_planets():

    planets = Planet.query.all()

    return jsonify([planet.serialize() for planet in planets]), 200


@app.route('/planet/<int:planet_id>', methods=['GET'])
def get_single_planet(planet_id):
    planet_single = Planet.query.get(planet_id)
    if not planet_single:
        return jsonify({'msg': 'No encontramos un planeta con ese id'}), 404
    return jsonify({'planet': planet_single.serialize()}), 200


@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    data = request.get_json()

    if not data or 'user_id' not in data:
        return jsonify({'msg': 'Se requiere user_id en el body'}), 400

    user_id = data.get('user_id')

    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'No encontramos un usuario con ese id'}), 404

    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({'msg': 'No encontramos un planeta con ese id'}), 404

    if planet in user.planets:
        return jsonify({'msg': 'El planeta ya está en favoritos'}), 400

    user.planets.append(planet)
    db.session.commit()

    return jsonify({'msg': 'Planeta agregado a favoritos', 'planet': planet.serialize()}), 201


@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_people(people_id):
    data = request.get_json()

    if not data or 'user_id' not in data:
        return jsonify({'msg': 'Se requiere user_id en el body'}), 400

    user_id = data.get('user_id')

    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'No encontramos un usuario con ese id'}), 404

    character = Character.query.get(people_id)
    if not character:
        return jsonify({'msg': 'No encontramos un personaje con ese id'}), 404

    if character in user.favorites_people:
        return jsonify({'msg': 'El personaje ya está en favoritos'}), 400

    user.favorites_people.append(character)
    db.session.commit()

    return jsonify({'msg': 'Personaje agregado a favoritos', 'character': character.serialize()}), 201


@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    data = request.get_json()

    if not data or 'user_id' not in data:
        return jsonify({'msg': 'Se requiere user_id en el body'}), 400

    user_id = data.get('user_id')

    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'No encontramos un usuario con ese id'}), 404

    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({'msg': 'No encontramos un planeta con ese id'}), 404

    if planet not in user.planets:
        return jsonify({'msg': 'El planeta no está en favoritos'}), 400

    user.planets.remove(planet)
    db.session.commit()

    return jsonify({'msg': 'Planeta eliminado de favoritos'}), 200


@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_people(people_id):
    data = request.get_json()

    if not data or 'user_id' not in data:
        return jsonify({'msg': 'Se requiere user_id en el body'}), 400

    user_id = data.get('user_id')

    user = User.query.get(user_id)
    if not user:
        return jsonify({'msg': 'No encontramos un usuario con ese id'}), 404

    character = Character.query.get(people_id)
    if not character:
        return jsonify({'msg': 'No encontramos un personaje con ese id'}), 404

    if character not in user.favorites_people:
        return jsonify({'msg': 'El personaje no está en favoritos'}), 400

    user.favorites_people.remove(character)
    db.session.commit()

    return jsonify({'msg': 'Personaje eliminado de favoritos'}), 200


# def algo():

    # recupero la info de la db
    # data =
    # chequeo si lo que se supone que recupere tiene algo
    # si no,. respondo con un error al cliente
    # si esta bien envio la lista de lo que me pidieron.

# this only runs if `$ python src/app.py` is executed
# if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
