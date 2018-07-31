# coding=utf-8

from flask_cors import CORS
from flask import Flask, jsonify, request

from .entities.entity import Session, engine, Base
from .entities.example import Example, ExampleSchema

# creating the Flask application
app = Flask(__name__)
CORS(app)

# if needed, generate database schema
Base.metadata.create_all(engine)


@app.route('/examples')
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


@app.route('/examples', methods=['POST'])
def add_example():
    # mount example object
    posted_example = ExampleSchema(only=('title', 'description'))\
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
