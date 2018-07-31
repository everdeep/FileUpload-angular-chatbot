# coding=utf-8

from .entities.entity import Session, engine, Base
from .entities.example import Example

# generate database schema
Base.metadata.create_all(engine)

# start session
session = Session()

# check for existing data
examples = session.query(Example).all()

if len(examples) == 0:
    # create and persist dummy exam
    python_example = Example("SQLAlchemy Example", "This is a test example.", "script")
    session.add(python_example)
    session.commit()
    session.close()

    # reload exams
    exams = session.query(Example).all()

# show existing exams
print('### Examples:')
for example in examples:
    print(f'({example.id}) {example.title} - {example.description}')
