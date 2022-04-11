from marshmallow import post_load

from .transaction import Transaction, TransactionSchema
from .transaction_type import TransactionType


class Sessions(Transaction):
    def __init__(self, event, player_id, country=None):
        super(Sessions, self).__init__(event, player_id, country)


class SessionsSchema(TransactionSchema):
    @post_load
    def parse_sessions(self, data, **kwargs):
        return Sessions(**data)



