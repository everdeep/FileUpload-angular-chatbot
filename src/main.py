# coding=utf-8

import random

from flask_cors import CORS
from flask import Flask, jsonify, request
from .auth import AuthError, requires_auth

from .entities.entity import Session, engine, Base

#== Example entity - to be deleted in production ===
from .entities.example import Example, ExampleSchema
#===================================================

# creating the Flask application
app = Flask(__name__)
CORS(app)

# if needed, generate database schema
Base.metadata.create_all(engine)

phrases = [
    "you suck, don't talk to me...",
    "do you have ligma or something?",
    "go commit not alive",
    "you're a punk",
    "leave me alone pls",
    "Oi don't talk smack, otherwise you get a whack",
    "do you want to buy some drugs?",
    "do I seem intelligent to you?",
    "have I been repeated myself lately?",
    "I feel like my vocabulary is a bit small",
    "hey, do you think I pass the turing test?",
    "yes",
    "no"
]

#===================================================
#   Manual shutdown
#===================================================

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

#===================================================
#   Chatbot API routes
#===================================================

@app.route('/response', methods=['POST'])
@requires_auth
def get_response():
    message = request.get_json()['value']
    print('Received from chatbot:', message)
    index = random.randrange(13)
    return jsonify({'value': phrases[index]})


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

#===================================================
#   EXAMPLE GET REQUEST WITH DATABASE ACCESS
#===================================================
@app.route('/examples')
@requires_auth
def get_examples():
    # fetching from the database
    session = Session()
    example_objects = session.query(Example).all()

    # transforming into JSON-serializable objects
    schema = ExampleSchema(many=True)
    examples = schema.dump(example_objects)

    # serializing as JSON
    session.close()
    return jsonify(examples.data)


#===================================================
#   EXAMPLE POST REQUEST WITH DATABASE ACCESS
#===================================================
@app.route('/examples', methods=['POST'])
def add_example():
    # mount example object
    posted_example = ExampleSchema(only=('title', 'description')) \
        .load(request.get_json())

    example = Example(**posted_example.data, created_by="HTTP post request")

    # persist example
    session = Session()
    session.add(example)
    session.commit()

    # return created example
    new_example = ExampleSchema().dump(example).data
    session.close()
    return jsonify(new_example), 201

#===================================================
