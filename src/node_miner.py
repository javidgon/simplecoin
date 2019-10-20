import copy
import os
import pprint
import sys
import time
import random

import schedule

from src.constants import MAX_NUM_TRANSACTIONS_PER_BLOCK
from .utils import (
    propagate_blockchain_in_network,
    load_state_from_file, save_state_into_file,
    is_any_other_node_currently_mining, consensus,
    has_account_enough_funds, get_states_from_all_other_nodes,
    set_up_env_vars, mine_coin, get_latest_block_mining_info_from_states)

pp = pprint.PrettyPrinter(indent=4)


def mine():
    miner_account_address, node_url, network_nodes_urls = set_up_env_vars()

    print(f'*** RUNNING MINER: {miner_account_address} *** (Running every {how_many_seconds_until_next_mining} seconds)')
    sys.stdout.flush()

    state = load_state_from_file(miner_account_address)

    states_from_all_other_nodes = get_states_from_all_other_nodes(node_url, network_nodes_urls)
    state['all_miners_addresses_in_the_network'] = [
        s['miner_account_address'] for s in states_from_all_other_nodes + [state]
    ]
    save_state_into_file(state, miner_account_address)

    pending_transactions = state['pending_transactions']

    if not pending_transactions:
        print('No pending transactions... exiting.')
        sys.stdout.flush()
        return

    state['currently_mining'] = True
    save_state_into_file(state, miner_account_address)

    if is_any_other_node_currently_mining(states_from_all_other_nodes):
        print('One or more Nodes are currently mining. Please wait a few seconds until they are finished.')
        sys.stdout.flush()

        state['currently_mining'] = False
        save_state_into_file(state, miner_account_address)

        return

    # We get, by consensus (majority), the most prevalent blockchain in the network.
    blockchain = consensus(network_nodes_urls)

    # We are going to iterate over this list later, so we copy it
    transactions_to_be_processed = copy.copy(state['pending_transactions'])
    # We give priorities to transactions with higher transaction fee
    transactions_to_be_processed = sorted(
        transactions_to_be_processed, key=lambda k: k['transaction_fee'], reverse=True)

    verified_transactions = []
    for transaction in transactions_to_be_processed[:MAX_NUM_TRANSACTIONS_PER_BLOCK]:
        state['pending_transactions'].remove(transaction)

        if not has_account_enough_funds(blockchain, transaction):
            state['failing_transactions'].append(transaction)

            save_state_into_file(state, miner_account_address)

            print('Unfortunately the "FROM" account doesn\'t have enough funds. '
                  f'The transaction {transaction} will be ignored.')
            sys.stdout.flush()

        else:
            state['verified_transactions'].append(transaction)

            verified_transactions.append(transaction)

    if verified_transactions:
        last_block_idx, difficulty_level_last_block, mining_time_last_block = get_latest_block_mining_info_from_states(
            states_from_all_other_nodes + [state])

        mined_block, current_difficulty_level, current_mining_time = mine_coin(
            blockchain, verified_transactions, miner_account_address, difficulty_level_last_block, mining_time_last_block)

        state['idx_last_block_mined'] = last_block_idx + 1
        state['difficulty_level_for_last_block_mined'] = current_difficulty_level
        state['mining_time_for_last_block_mined'] = current_mining_time

        blockchain.append(mined_block)

        propagate_blockchain_in_network(blockchain, network_nodes_urls, miner_account_address)

        print(f'Block {mined_block.get_hash()} (Idx: {last_block_idx + 1}) was mined successfully (Took {current_mining_time} seconds with difficulty level of {current_difficulty_level})')
        sys.stdout.flush()

    state['currently_mining'] = False
    save_state_into_file(state, miner_account_address)


# So two Miners don't "collide" (start mining at the same time)
how_many_seconds_until_next_mining = int(os.getenv('MINER_SLEEP_TIME_IN_SECONDS', random.randint(50, 70)))
schedule.every(how_many_seconds_until_next_mining).seconds.do(mine)


while True:
    schedule.run_pending()
    time.sleep(1)
