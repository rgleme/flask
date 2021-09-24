from itertools import count
from typing import Optional, List
from flask import Flask, request, jsonify
from flask_pydantic_spec import (
    FlaskPydanticSpec, Response, Request
)
from pydantic import BaseModel, Field
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage

server = Flask(__name__)
spec = FlaskPydanticSpec('flask', title='Person Records API')
spec.register(server)
database = TinyDB(storage=MemoryStorage)
c = count()

class QueryPerson(BaseModel):
    id: Optional[int]
    name: Optional[str]
    age: Optional[int]

class Person(BaseModel):
    id: Optional[int] = Field(default_factory=lambda: next(c))
    name: Optional[str]
    age: Optional[int]

class People(BaseModel):
    people: List[Person]
    count: int

@server.get('/people')
@spec.validate(
    query=QueryPerson,
    resp=Response(HTTP_200=People)
)
def search_people():
    """Return one or more person from DataBase, by Querystring."""
    query = request.context.query.dict(exclude_none=True)
    all_people = database.search(
        Query().fragment(query)
    )
    return jsonify(
        People(
            people=all_people,
            count=len(all_people)
        ).dict()
    )

@server.get('/people/<int:id>')
@spec.validate(resp=Response(HTTP_200=Person))
def search_person(id):
    """Return one person from Database by ID."""
    try:
        person = database.search(Query().id == id)[0]
    except IndexError:
        return {'message': 'Person not found!'}, 404
    return jsonify(person)


@server.post('/people')
@spec.validate(
    body=Request(Person), resp=Response(HTTP_201=Person)
)
def insert_person():
    """Insert one person's record in the Database."""
    body = request.context.body.dict()
    database.insert(body)
    return body


@server.put('/people/<int:id>')
@spec.validate(
    body=Request(Person), resp=Response(HTTP_201=Person)
)
def change_person(id):
    """Change one person's record in the Database."""
    Person = Query()
    body = request.context.body.dict()
    database.update(body, Person.id == id)
    return jsonify(body)


@server.delete('/people/<int:id>')
@spec.validate(resp=Response('HTTP_204'))
def delete_person(id):
    """Remove one person's record in the Database."""
    database.remove(Query().id == id)
    return jsonify({})

server.run()