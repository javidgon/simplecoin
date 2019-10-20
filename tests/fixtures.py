from datetime import datetime

from src.block import Block


BLOCK_GENESIS = Block(
    0,
    datetime.now(),
    {
        'nonce': 1,
        'transactions': [
            {
                'from': 'genesis',
                'to': 'network',
                'amount': 1000000000  # Total amount of funds available in the network: 1000 millions
            }
        ]
    },
    None
)


BLOCK_1 = Block(
    0,
    datetime.now(),
    {
        'nonce': 1,
        'transactions': [
            {
                'from': 'network',
                'to': 'eve',
                'amount': 10
            }
        ]
    },
    BLOCK_GENESIS
)


BLOCKCHAIN = [BLOCK_GENESIS, BLOCK_1]


TRANSACTION_1 = {
    'from': 'eve',
    'to': 'bob',
    'amount': 5.0,
    'transaction_fee': 1.0
}


TRANSACTION_2 = {
    'from': 'bob',
    'to': 'john',
    'amount': 10.0,
    'transaction_fee': 1.0
}