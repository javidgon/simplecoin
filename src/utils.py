import copy
import os
import time
from pathlib import Path
from typing import List, Dict

import requests
import json
import sys

from urllib.parse import urljoin
from datetime import datetime

from .constants import PROOF_OF_WORK_TARGET_TIME_IN_SECONDS, DEFAULT_PROOF_OF_WORK_DIFFICULTY_LEVEL
from .block import Block


def create_genesis_block() -> Block:
    now = datetime.now()
    return Block(
        0,
        now.timestamp(),
        {
            'nonce': 1,
            'transactions': [
                {
                    'from': 'genesis',
                    'to': 'network',
                    'amount': 1000000000,  # Total amount of funds available in the network: 1000 millions,
                    'timestamp': now.timestamp()
                }
            ]
        },
        None
    )


def proof_of_work(
        blockchain: List[Block],
        transactions: List[Dict],
        difficulty_level_for_last_time: int = DEFAULT_PROOF_OF_WORK_DIFFICULTY_LEVEL,
        how_long_it_took_last_time: int = PROOF_OF_WORK_TARGET_TIME_IN_SECONDS) -> (Block, int, int):

    current_difficulty_level = difficulty_level_for_last_time
    if how_long_it_took_last_time > PROOF_OF_WORK_TARGET_TIME_IN_SECONDS + 10:
        current_difficulty_level = difficulty_level_for_last_time - 1
        print(f'Mining was too slow last time ({how_long_it_took_last_time} seconds)... setting difficulty to '
              f'{current_difficulty_level} (Previously was {difficulty_level_for_last_time})')
        sys.stdout.flush()

    elif how_long_it_took_last_time < PROOF_OF_WORK_TARGET_TIME_IN_SECONDS - 10:
        current_difficulty_level = difficulty_level_for_last_time + 1
        print(f'Mining was too fast last time  ({how_long_it_took_last_time} seconds)... setting difficulty to '
              f'{current_difficulty_level} (Previously was {difficulty_level_for_last_time})')
        sys.stdout.flush()
    else:
        print(f'Mining was perfect last time  ({how_long_it_took_last_time} seconds)... keeping difficulty on '
              f'{difficulty_level_for_last_time}')
        sys.stdout.flush()

    previous_block = blockchain[-1]

    previous_index = previous_block.index
    previous_nonce = previous_block.data['nonce']

    mined_block = Block(
        previous_index + 1,
        datetime.now().timestamp(),
        {
            'nonce': previous_nonce + 1,
            'transactions': transactions
        },
        previous_block
    )

    start = time.time()
    while not (mined_block.get_hash()[:current_difficulty_level] == '0' * current_difficulty_level):
        mined_block.data['nonce'] += 1

    end = time.time()
    return mined_block, current_difficulty_level, end - start


def get_blockchains_from_all_nodes(network_nodes_urls: List[str]) -> List[List[Block]]:
    blockchains_from_all_nodes = []

    for node_url in network_nodes_urls:
        url = urljoin(node_url, 'blockchain')
        try:
            r = requests.get(url)

            if r.status_code == 200:
                serialized_blockchain = json.loads(r.content)

                blockchains_from_all_nodes.append(unserialize_blockchain(serialized_blockchain))
            else:
                print(f'{node_url} is faulty. Please investigate.')
                sys.stdout.flush()

        except requests.exceptions.ConnectionError:
            print(f'{node_url} not available at this moment')
            sys.stdout.flush()

    return blockchains_from_all_nodes


def consensus(network_nodes_urls: List[str]) -> List[Block]:
    """
    Chooses the blockchain which is in a majority of nodes in the network.
    e.g., 1 Node < 2 Nodes

    :param network_nodes_urls: list of nodes in the network
    :return:
    """
    blockchains_from_all_nodes = get_blockchains_from_all_nodes(network_nodes_urls)
    if not blockchains_from_all_nodes:
        raise Exception('This node cannot find other nodes. Make sure that the URLs are correct.')

    blockchains_hashes_counter = {}

    for blockchain_from_a_node in blockchains_from_all_nodes:

        if blockchain_from_a_node:
            last_block_hash = blockchain_from_a_node[-1].get_hash()

            if last_block_hash not in blockchains_hashes_counter:
                blockchains_hashes_counter[last_block_hash] = 1
            else:
                blockchains_hashes_counter[last_block_hash] += 1

    # We get the "last hash" of the Blockchain with the most number of "votes".
    # Meaning, the blockchain which is used the most in the network.

    last_hash_with_the_most_votes_in_the_network = max(blockchains_hashes_counter, key=blockchains_hashes_counter.get)

    for blockchain_from_a_node in blockchains_from_all_nodes:
        if blockchain_from_a_node:

            # We return the blockchain with the last hash obtained above.
            if blockchain_from_a_node[-1].get_hash() == last_hash_with_the_most_votes_in_the_network:
                return blockchain_from_a_node

    raise Exception('Consensus wasn\'t reached')


def mine_coin(
        blockchain: List[Block],
        verified_transactions: List[Dict],
        miner_account_address: str,
        difficulty_level_last_block: int,
        mining_time_last_block: int
) -> (Block, int, int):
    transactions = []

    for transaction in verified_transactions:
        # Mining Fee Transaction
        transactions.append({
            'from': transaction['from'],
            'to': miner_account_address,
            'amount': transaction['transaction_fee'],
            'timestamp': transaction['timestamp']
        })

        # Original Transaction
        transactions.append({
            'from': transaction['from'],
            'to': transaction['to'],
            'amount': transaction['amount'],
            'timestamp': transaction['timestamp']
        })

    mined_block, current_difficulty_level, current_mining_time = proof_of_work(
        blockchain, transactions, difficulty_level_last_block, mining_time_last_block)

    return mined_block, current_difficulty_level, current_mining_time


def propagate_blockchain_in_network(blockchain: List[Block], network_nodes_urls: List[str], miner_account_address: str) -> None:
    serialized_blockchain = json.dumps([serialize_block(block) for block in blockchain])

    for node_url in network_nodes_urls:
        url = urljoin(node_url, 'blockchain')

        try:
            r = requests.put(url, data=serialized_blockchain, headers={'Miner-Address': miner_account_address})

            if r.status_code != 202:
                print(f'{node_url} is faulty. Please investigate.')
                sys.stdout.flush()

        except requests.exceptions.ConnectionError:
            print(f'{node_url} not available at this moment')
            sys.stdout.flush()


def serialize_block(block: Block) -> Dict:
    return {
        'index': block.index,
        'timestamp': block.timestamp,
        'data': block.data,
        'previous_hash': block.previous_hash
    }


def unserialize_blockchain(serialized_blockchain: List[Dict]) -> List[Block]:
    unserialized_blockchain = []

    previous_block = None
    for serialized_block in serialized_blockchain:

        block = Block(
            serialized_block['index'],
            serialized_block['timestamp'],
            serialized_block['data'],
            previous_block=previous_block
        )

        unserialized_blockchain.append(block)

        previous_block = block

    return unserialized_blockchain


def save_blockchain_into_file(blockchain: List[Block], miner_account_address: str) -> None:
    miner_folder_path = Path(f'miners/{miner_account_address}')

    if not miner_folder_path.exists():
        miner_folder_path.mkdir(parents=True)

    filepath = miner_folder_path / 'blockchain.txt'

    with open(filepath, 'w') as f:
        f.write(json.dumps([serialize_block(block) for block in blockchain]))


def load_blockchain_from_file(miner_account_address: str):
    miner_folder_path = Path(f'miners/{miner_account_address}')

    if not miner_folder_path.exists():
        miner_folder_path.mkdir(parents=True)

    filepath = miner_folder_path / 'blockchain.txt'

    if not filepath.exists():
        return []

    with open(filepath, 'r') as f:
        serialized_blockchain = json.loads(f.read())

        return unserialize_blockchain(serialized_blockchain)


def save_state_into_file(state: Dict, miner_account_address: str) -> None:
    miner_folder_path = Path(f'miners/{miner_account_address}')

    if not miner_folder_path.exists():
        miner_folder_path.mkdir(parents=True)

    filepath = miner_folder_path / 'state.txt'

    with open(filepath, 'w') as f:
        f.write(json.dumps(state))


def load_state_from_file(miner_account_address: str) -> Dict:
    miner_folder_path = Path(f'miners/{miner_account_address}')

    if not miner_folder_path.exists():
        miner_folder_path.mkdir(parents=True)

    filepath = miner_folder_path / 'state.txt'

    if not filepath.exists():
        return {
            'miner_account_address': miner_account_address,
            'currently_mining': False,
            'pending_transactions': [],
            'failing_transactions': [],
            'verified_transactions': [],
            'idx_last_block_mined': 0,
            'difficulty_level_for_last_block_mined': DEFAULT_PROOF_OF_WORK_DIFFICULTY_LEVEL,
            'mining_time_for_last_block_mined': PROOF_OF_WORK_TARGET_TIME_IN_SECONDS,
            'all_miners_addresses_in_the_network': [miner_account_address]
        }

    with open(filepath, 'r') as f:
        return json.loads(f.read())


def get_states_from_all_other_nodes(node_url: str, network_nodes_urls: List[str]) -> List[Dict]:
    states_from_all_nodes = []

    # We don't want to check our own node.
    other_nodes_url = copy.copy(network_nodes_urls)
    other_nodes_url.remove(node_url)

    for node_url in other_nodes_url:
        url = urljoin(node_url, 'state')
        try:
            r = requests.get(url)

            if r.status_code == 200:
                fetched_state = json.loads(r.content)
                states_from_all_nodes.append(fetched_state)

                # In case we find a node "currently mining" we return fast, as we don't need further information
                # at this point.
                if fetched_state['currently_mining']:
                    break

            else:
                print(f'{node_url} is faulty. Please investigate.')
                sys.stdout.flush()

        except requests.exceptions.ConnectionError:
            print(f'{node_url} not available at this moment')
            sys.stdout.flush()

    return states_from_all_nodes


def is_any_other_node_currently_mining(states_from_all_nodes: List[Dict]) -> bool:
    for state_for_a_node in states_from_all_nodes:
        if state_for_a_node['currently_mining']:
            return True

    return False


def is_posted_transaction_valid(transaction: Dict) -> bool:
    return all([
        transaction.get('to'),
        transaction.get('from'),
        transaction.get('amount', 0.0) > 0.0,
        transaction.get('transaction_fee', 0.0) >= 0.01
    ])


def is_posted_blockchain_valid(serialized_blockchain: List[Dict]) -> bool:
    # TODO: Check whether all the blocks have the valid structure.
    return all([
        isinstance(serialized_blockchain, List),
        len(serialized_blockchain) > 0  # It has at least 1 block (Genesis Block)
    ])


def has_account_enough_funds(blockchain: List[Block], transaction: Dict) -> bool:
    from_account = transaction['from']
    amount = transaction['amount']
    transaction_fee = transaction['transaction_fee']

    balance = 0.0

    for block in blockchain:
        for tx in block.data['transactions']:
            if tx['to'] == from_account:
                balance += tx['amount']

            elif tx['from'] == from_account:
                balance -= tx['amount']

    return bool((balance - amount - transaction_fee) >= 0.0)


def set_up_env_vars() -> (str, str, List[str]):
    miner_account_address = os.getenv('MINER_ACCOUNT_ADDRESS')

    if not miner_account_address:
        print('Please set the "MINER_ACCOUNT_ADDRESS" env var')
        exit(1)

    node_url = os.getenv('NODE_URL')

    if not node_url:
        print('Please set the "NODE_URL" env var')
        exit(1)

    network_nodes_urls = os.getenv('NETWORK_NODES_URLS')

    if network_nodes_urls:
        network_nodes_urls = [node for node in network_nodes_urls.split(',')]

        if node_url not in network_nodes_urls:
            network_nodes_urls.append(node_url)
    else:
        network_nodes_urls = [node_url]

    return miner_account_address, node_url, network_nodes_urls


def get_latest_block_mining_info_from_states(states_from_all_nodes: List[Dict]) -> (int, int, int):
    state_with_info_about_last_block = sorted(
        states_from_all_nodes, key=lambda k: k['idx_last_block_mined'], reverse=True)[0]

    return (
        state_with_info_about_last_block['idx_last_block_mined'],
        state_with_info_about_last_block['difficulty_level_for_last_block_mined'],
        state_with_info_about_last_block['mining_time_for_last_block_mined'],
    )
