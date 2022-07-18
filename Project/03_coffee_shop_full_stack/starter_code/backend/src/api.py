import os
from threading import ExceptHookArgs
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks')
def retrieve_drinks():
    all_drinks = Drink.query.order_by(Drink.id).all()
    formatted_drinks = [drink.short() for drink in all_drinks]
    print(formatted_drinks)
    if len(formatted_drinks) == 0:
        abort(404)
    return jsonify({
        "success": True,
        "drinks": formatted_drinks
    })

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail', methods=["GET"])
@requires_auth('get:drinks-detail')
def retrieve_details(jwt):
    all_drinks = Drink.query.order_by(Drink.id).all()
    formatted_drinks = [drink.long() for drink in all_drinks]
    if len(formatted_drinks) == 0:
        abort(404)
    return jsonify({
        "success": True,
        "drinks": formatted_drinks
    })


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''

@app.route('/drinks', methods=["POST"])
@requires_auth('post:drinks')
def create_drink(payload):
    body = request.get_json()
    print(body)
    try:
        new_drink_title  = body.get("title", None)
        new_drink_recipe = body.get("recipe", None)

        print(type(new_drink_recipe))

        if isinstance(new_drink_recipe, dict):
            new_drink_recipe = [new_drink_recipe]

        drink_recipe = json.dumps(new_drink_recipe)
        new_drink = Drink(title=new_drink_title, recipe=drink_recipe)
        formatted_drinks = [new_drink.long()]
        new_drink.insert()

        return jsonify({
            "success": True,
            "drinks": formatted_drinks
        })

    except:
        abort(422)

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks/<int:drink_id>", methods=["PATCH"])
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):
    body = request.get_json()
    try:
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()
        if drink is None:
                abort(404)

        if "title" in body:
                drink.title = body.get("title")

        if "recipe" in body:
                drink.recipe = json.dumps(body.get("recipe"))

        drink.update()

        return jsonify(
                {
                    "success": True,
                }
            )
    except: 
        abort(400)

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks/<int:drink_id>", methods=["DELETE"])
@requires_auth('delete:drinks')
def delete_drink(payload, drink_id):
    try:
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

        if drink is None: 
            abort(404)

        drink.delete()

        return jsonify({
            "success": True,
            "deleted" : drink.id
        })
    except:
        abort(422)


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": 'Unathorized'
    }), 401


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": 'Internal Server Error'
    }), 500


'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''
@app.errorhandler(404)
def not_found(error):
    return (
        jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
            }),
        404,
    )

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''

@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code
