import hashlib as hasher
import json
import pprint
from datetime import datetime

from flask import Flask, request

from .utils import (
    create_genesis_block,
    serialize_block, unserialize_blockchain,
    save_blockchain_into_file, load_blockchain_from_file,
    load_state_from_file, save_state_into_file,
    is_posted_transaction_valid,
    is_posted_blockchain_valid, set_up_env_vars)

pp = pprint.PrettyPrinter(indent=4)

app = Flask(__name__)

miner_account_address, node_url, network_nodes_urls = set_up_env_vars()


@app.route('/transaction', methods=['POST'])
def create_transaction():
    state = load_state_from_file(miner_account_address)

    transaction = json.loads(request.data)

    if not transaction or not is_posted_transaction_valid(transaction):
        return 'Transaction is invalid. Please make sure that all the attributes are provided and that the ' \
               '"transaction fee" is at least 0.01', 400

    # Generate Transaction ID
    sha = hasher.sha256()

    transaction['timestamp'] = datetime.now().timestamp()

    sha.update(json.dumps({
        'from': transaction['from'],
        'to': transaction['to'],
        'amount': transaction['amount'],
        'timestamp': transaction['timestamp']
    }).encode())

    transaction_id = sha.hexdigest()

    state['pending_transactions'].append(transaction)
    save_state_into_file(state, miner_account_address)

    return f'Transaction ID: {transaction_id}', 201


@app.route('/blockchain', methods=['GET'])
def get_blockchain():
    blockchain = load_blockchain_from_file(miner_account_address)

    if not blockchain:
        # If the Blockchain is empty, we initialize it with the genesis block.
        blockchain.append(create_genesis_block())
        save_blockchain_into_file(blockchain, miner_account_address)

    return json.dumps([serialize_block(block) for block in blockchain]), 200


@app.route('/blockchain', methods=['PUT'])
def update_blockchain():
    # TODO: HTTP_HOST is not the most secure way to check the provenance.
    headers = request.headers.environ

    if 'HTTP_HOST' not in headers or not any(headers['HTTP_HOST'] in node_url for node_url in network_nodes_urls):
        return 'Unknown sender.', 401

    serialized_blockchain = json.loads(request.data)

    if not is_posted_blockchain_valid(serialized_blockchain):
        return 'Invalid blockchain.', 400

    blockchain = unserialize_blockchain(serialized_blockchain)

    save_blockchain_into_file(blockchain, miner_account_address)

    return json.dumps(serialized_blockchain), 202


@app.route('/state', methods=['GET'])
def get_state():
    return json.dumps(load_state_from_file(miner_account_address)), 200
