from time import sleep

from .utils import dockercompose_build, dockercompose_up, dockercompose_down, make_transaction, get_blockchain, \
    exit_and_fail, get_state


def test_multiple_transactions_to_different_nodes_are_added_consistently_to_the_blockchain():
    res = dockercompose_build()
    if not res:
        assert False

    res = dockercompose_up()
    if not res:
        assert False

    # Valid transactions
    r = make_transaction(
        'http://0.0.0.0:5001',
        'network',
        '000067bd199453edf94b560599dd812b82b4a1a8efc4d462e8813c765d2b7c75',
        3.0,
        0.1
    )

    if r.status_code != 201:
        exit_and_fail()

    sleep(100)

    r = make_transaction(
        'http://0.0.0.0:5002',
        'network',
        '000067bd199453edf94b560599dd812b82b4a1a8efc4d462e8813c765d2b7c75',
        4.0,
        0.2
    )

    if r.status_code != 201:
        exit_and_fail()


    sleep(100)

    r = get_blockchain(
        'http://0.0.0.0:5001',
    )

    if r.status_code != 200:
        exit_and_fail()

    blockchain_node1 = r.json()

    r = get_state(
        'http://0.0.0.0:5001',
    )

    if r.status_code != 200:
        exit_and_fail()

    state_node1 = r.json()

    assert state_node1['currently_mining'] == False
    assert len(state_node1['pending_transactions']) == 0
    assert len(state_node1['verified_transactions']) == 1
    assert len(state_node1['failing_transactions']) == 0
    assert state_node1['idx_last_block_mined'] == 1
    assert len(state_node1['all_miners_addresses_in_the_network']) == 3

    r = get_blockchain(
        'http://0.0.0.0:5002',
    )

    if r.status_code != 200:
        exit_and_fail()

    blockchain_node2 = r.json()

    r = get_state(
        'http://0.0.0.0:5002',
    )

    if r.status_code != 200:
        exit_and_fail()

    state_node2 = r.json()

    assert state_node2['currently_mining'] == False
    assert len(state_node2['pending_transactions']) == 0
    assert len(state_node2['verified_transactions']) == 1
    assert len(state_node2['failing_transactions']) == 0
    assert state_node2['idx_last_block_mined'] == 2
    assert len(state_node2['all_miners_addresses_in_the_network']) == 3

    r = get_blockchain(
        'http://0.0.0.0:5003',
    )

    if r.status_code != 200:
        exit_and_fail()

    blockchain_node3 = r.json()

    r = get_state(
        'http://0.0.0.0:5003',
    )

    if r.status_code != 200:
        exit_and_fail()

    state_node3 = r.json()

    assert state_node3['currently_mining'] == False
    assert len(state_node3['pending_transactions']) == 0
    assert len(state_node3['verified_transactions']) == 0
    assert len(state_node3['failing_transactions']) == 0
    assert state_node3['idx_last_block_mined'] == 0
    assert len(state_node3['all_miners_addresses_in_the_network']) == 3

    assert bool(blockchain_node1 == blockchain_node2 == blockchain_node3)

    blockchain = blockchain_node3

    assert len(blockchain) == 3

    genesis_block = blockchain[0]

    assert len(genesis_block['data']['transactions']) == 1
    assert genesis_block['data']['transactions'][0]['from'] == 'genesis'
    assert genesis_block['data']['transactions'][0]['to'] == 'network'
    assert genesis_block['data']['transactions'][0]['amount'] == 1000000000

    mid_block = blockchain[1]

    assert len(mid_block['data']['transactions']) == 2
    assert mid_block['data']['transactions'][0]['from'] == 'network'
    assert mid_block['data']['transactions'][0]['amount'] == 0.1

    assert mid_block['data']['transactions'][1]['from'] == 'network'
    assert mid_block['data']['transactions'][1]['to'] == '000067bd199453edf94b560599dd812b82b4a1a8efc4d462e8813c765d2b7c75'
    assert mid_block['data']['transactions'][1]['amount'] == 3.0

    last_block = blockchain[-1]

    assert last_block['data']['transactions'][0]['from'] == 'network'
    assert last_block['data']['transactions'][0]['amount'] == 0.2

    assert last_block['data']['transactions'][1]['from'] == 'network'
    assert last_block['data']['transactions'][1]['to'] == '000067bd199453edf94b560599dd812b82b4a1a8efc4d462e8813c765d2b7c75'
    assert last_block['data']['transactions'][1]['amount'] == 4.0


    res = dockercompose_down()
    if not res:
        assert False
