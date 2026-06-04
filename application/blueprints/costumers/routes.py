from sqlalchemy import select
from flask import  request, jsonify
from marshmallow import ValidationError

from .schemas import costumer_schema, costumers_schema, login_schema

from application.models import Costumer, db
from . import costumer_bp
from application.extensions import limiter,cache
from application.utils.util import encode_token, token_required


#========== Authentication ===========

@costumer_bp.route("/login", methods=['POST'])
def login():
    try:
        credentials = login_schema.load(request.json)# we use the login schema to validate the incoming data, which only requires email and password fields
        email = credentials['email']
        password = credentials['password']
        
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    query = select(Costumer).where(Costumer.email == email) 
    user = db.session.execute(query).scalars().first() #Query user table for a user with this email

    if user and user.password == password: #if we have a user associated with the username and the password is correct, validate the password
        auth_token = encode_token(user.id, "costumer") #generate an auth token with the user's id as the payload

        response = {
            "status": "success",
            "message": "Successfully Logged In",
            "auth_token": auth_token
        }
        return jsonify(response), 200
    else:
        return jsonify({'messages': "Invalid email or password"}), 401


#========= Create ===========

@costumer_bp.route("/", methods=["POST"])
# @limiter.limit("5 per day")
def create_costumer():
    try:
        costumer_data = costumer_schema.load(request.json)
        
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    new_costumer = Costumer(**costumer_data)
    db.session.add(new_costumer)
    db.session.commit()

    return costumer_schema.jsonify(new_costumer), 201


#========== Read ===========


@costumer_bp.route("/<int:costumer_id>", methods=["GET"])
@cache.cached(timeout=60)  # Cache this endpoint for 60 seconds
def get_costumer(costumer_id):
    try:
        costumer_data = db.session.get(Costumer, costumer_id)
        
    except ValidationError as err:
        return jsonify(err.messages), 400
     

    return costumer_schema.jsonify(costumer_data), 200


@costumer_bp.route("/", methods=["GET"])
# @cache.cached(timeout=60)  # Cache this endpoint for 60 seconds
def get_costumers():
    try:
        page = request.args.get("page", default=1, type=int)
        per_page = request.args.get("per_page", default=10, type=int)

        query = db.select(Costumer)
        paginated_costumers = db.paginate(query, page=page, per_page=per_page)

        if not paginated_costumers.items:
            return jsonify({"message": "No costumers found"}), 404

    except ValidationError as err:
        return jsonify(err.messages), 400
     
    
    return costumers_schema.jsonify(paginated_costumers), 200



#========== Update ===========


@costumer_bp.route("/", methods=["PUT"])
@limiter.limit("5 per month")
@token_required
def update_costumer(current_id, current_role):
    try:
        costumer_data = costumer_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400

    costumer = db.session.get(Costumer, current_id)
    if not costumer:
        return jsonify({"error": "Costumer not found"}), 404
    
    if current_role != "costumer":
        return jsonify({"error": "Unauthorized"}), 403

    for key, value in costumer_data.items():
        setattr(costumer, key, value)

    db.session.commit()
    return costumer_schema.jsonify(costumer), 200


#========== Delete ===========

#DELETE WITHOUT TOKEN
# @costumer_bp.route("/<int:costumer_id>", methods=["DELETE"])
# def delete_costumer(costumer_id):
#     query = select(Costumer).where(Costumer.id == costumer_id)
#     costumer = db.session.execute(query).scalars().first()
#     if not costumer:
#         return jsonify({"error": "Costumer not found"}), 404

#     db.session.delete(costumer)
#     db.session.commit()
#     return jsonify({"message": "Costumer deleted"}), 200

#DELETE WITH TOKEN
@costumer_bp.route("/", methods=["DELETE"])
# @limiter.limit("5 per year")
@token_required
def delete_costumer(current_id, current_role):
    query = select(Costumer).where(Costumer.id == current_id)
    costumer = db.session.execute(query).scalars().first()
    if not costumer:
        return jsonify({"error": "Costumer not found"}), 404
    
    if current_role != "costumer":
        return jsonify({"error": "Unauthorized"}), 403

    db.session.delete(costumer)
    db.session.commit()
    return jsonify({"message": "Costumer deleted"}), 200

