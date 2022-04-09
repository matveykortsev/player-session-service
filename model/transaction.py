import datetime as dt
from uuid import uuid4

from marshmallow import Schema, fields


class Transaction:
    def __init__(self, event, country, player_id, type):
        self.event = event
        self.country = country
        self.player_id = player_id
        self.session_id = uuid4()
        self.ts = dt.datetime.now()
        self.type = type


class TransactionSchema(Schema):
    event = fields.Str()
    country = fields.Str()
    player_id = fields.Str()
    session_id = fields.UUID()
    ts = fields.Date()
    type = fields.Str()

