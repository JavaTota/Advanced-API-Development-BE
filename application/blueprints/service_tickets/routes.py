from flask import  request, jsonify
from marshmallow import ValidationError

from .schemas import service_ticket_schema, service_tickets_schema, service_ticket_update_schema
from application.models import  Inventory, Mechanic, ServiceTicket, ServiceTicketInventory, db
from . import service_ticket_bp
from application.extensions import limiter, cache
from application.utils.util import encode_token, token_required


@service_ticket_bp.route("/", methods=["POST"])
# @limiter.limit("5 per day")
@token_required
def create_service_ticket(current_id, current_role):
    try:
        service_ticket_data = request.json.copy()
        service_ticket_data["costumer_id"] = current_id
        service_ticket_data = service_ticket_schema.load(service_ticket_data)
        
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    if current_role != "costumer":
        return jsonify({"error": "Unauthorized"}), 403
    
   
    new_service_ticket = ServiceTicket(**service_ticket_data)
    db.session.add(new_service_ticket)
    db.session.commit()

    return service_ticket_schema.jsonify(new_service_ticket), 201


#========== Read ===========


@service_ticket_bp.route("/<int:service_ticket_id>", methods=["GET"])
@cache.cached(timeout=60)  # Cache this endpoint for 60 seconds
def get_service_ticket(service_ticket_id):
    try:
        service_ticket_data = db.session.get(ServiceTicket, service_ticket_id)
        
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    if not service_ticket_data:
        return jsonify({"error": "service_ticket not found"}), 404

    return service_ticket_schema.jsonify(service_ticket_data), 200


@service_ticket_bp.route("/", methods=["GET"])
@cache.cached(timeout=60)  # Cache this endpoint for 60 seconds
def get_service_tickets():
    try:
        service_tickets_data = db.session.query(ServiceTicket).all()
        
    except ValidationError as err:
        return jsonify(err.messages), 400

    return service_tickets_schema.jsonify(service_tickets_data), 200

@service_ticket_bp.route("/my_tickets", methods=["GET"])
@token_required
def get_my_tickets(current_id, current_role):
    try:
        tickets_data = db.session.query(ServiceTicket).filter(ServiceTicket.costumer_id == current_id).all()
    except ValidationError as err:
        return jsonify(err.messages), 400
    
    if current_role != "costumer":
        return jsonify({"error": "Unauthorized"}), 403

    return jsonify({
        "total": len(tickets_data),
        "tickets": service_tickets_schema.dump(tickets_data)
    }), 200


#========== Update ===========

@service_ticket_bp.route("/<int:ticket_id>/edit_parts/<int:inventory_id>", methods=["PUT"])
@token_required
def edit_parts(ticket_id, inventory_id):
    quantity = request.json.get("quantity")

    if quantity is None:
        return jsonify({"error": "quantity required"}), 400

    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        return jsonify({"error": "ticket not found"}), 404

    part = db.session.get(Inventory, inventory_id)
    if not part:
        return jsonify({"error": "Part not found"}), 404

    existing = db.session.query(ServiceTicketInventory).filter_by(
        service_ticket_id=ticket_id,
        inventory_id=inventory_id
    ).first()

    if existing:
        existing.quantity += quantity
        db.session.commit()
        return jsonify({"message": "Part updated"}), 200
    else:
        association = ServiceTicketInventory(
            service_ticket=ticket,
            inventory=part,
            quantity=quantity
        )
        db.session.add(association)

    db.session.commit()

    return jsonify({"message": "Part added"}), 200

@service_ticket_bp.route("/<int:service_ticket_id>/edit_mechanics", methods=["PUT"])
@token_required
def edit_service_ticket(service_ticket_id):
    try:
        service_ticket_edits = service_ticket_update_schema.load(request.json, partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400

    service_ticket = db.session.get(ServiceTicket, service_ticket_id)

    if not service_ticket:
        return jsonify({"error": "service_ticket not found"}), 404

    # Update the service ticket fields
    for mechanic_id in service_ticket_edits.get("add_mechanic_ids", []):
        mechanic = db.session.get(Mechanic, mechanic_id)
        if mechanic and mechanic not in service_ticket.mechanics:
            service_ticket.mechanics.append(mechanic)

    for mechanic_id in service_ticket_edits.get("remove_mechanic_ids", []):
        mechanic = db.session.get(Mechanic, mechanic_id)
        if mechanic and mechanic in service_ticket.mechanics:
            service_ticket.mechanics.remove(mechanic)

    db.session.commit()
    return service_ticket_schema.jsonify(service_ticket), 200


#========== Delete ===========


@service_ticket_bp.route("/<int:service_ticket_id>", methods=["DELETE"])
@limiter.limit("5 per year")
@token_required
def delete_service_ticket(current_id, current_role, service_ticket_id):
    service_ticket = db.session.get(ServiceTicket, service_ticket_id)

    if not service_ticket:
        return jsonify({"error": "service_ticket not found"}), 404

    db.session.delete(service_ticket)
    db.session.commit()

    return jsonify({"message": "service_ticket deleted"}), 200

