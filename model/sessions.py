from marshmallow import post_load

from .transaction import Transaction, TransactionSchema
from .transaction_type import TransactionType


class Sessions(Transaction):
    def __init__(self, event, country, player_id):
        super(Sessions, self).__init__(event, country, player_id, TransactionType.SESSIONS)


class SessionsSchema(TransactionSchema):
    @post_load
    def parse_sessions(self, data):
        return Sessions(**data)



