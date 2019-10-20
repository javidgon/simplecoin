import json

import requests

from .utils import dockercompose_build, dockercompose_up, dockercompose_down, \
    exit_and_fail


def test_transaction_if_an_attribute_is_missing():
    res = dockercompose_build()
    if not res:
        assert False

    res = dockercompose_up()
    if not res:
        assert False

    r = requests.post('http://0.0.0.0:5001/transaction', data=json.dumps({
        'to': 'network',
        'amount': 2.0,
        'transaction_fee': 0.1
    }))

    if r.status_code != 400:
        exit_and_fail()

    r = requests.post('http://0.0.0.0:5001/transaction', data=json.dumps({
        'from': '000067bd199453edf94b560599dd812b82b4a1a8efc4d462e8813c765d2b7c75',
        'amount': 2.0,
        'transaction_fee': 0.1
    }))

    if r.status_code != 400:
        exit_and_fail()

    r = requests.post('http://0.0.0.0:5001/transaction', data=json.dumps({
        'to': 'network',
        'from': '000067bd199453edf94b560599dd812b82b4a1a8efc4d462e8813c765d2b7c75',
        'transaction_fee': 0.1
    }))

    if r.status_code != 400:
        exit_and_fail()

    r = requests.post('http://0.0.0.0:5001/transaction', data=json.dumps({
        'to': 'network',
        'from': '000067bd199453edf94b560599dd812b82b4a1a8efc4d462e8813c765d2b7c75',
        'amount': 2.0,
    }))

    if r.status_code != 400:
        exit_and_fail()

    r = requests.post('http://0.0.0.0:5001/transaction', data=json.dumps({
        'to': 'network',
        'from': '000067bd199453edf94b560599dd812b82b4a1a8efc4d462e8813c765d2b7c75',
        'amount': 2.0,
        'transaction_fee': 0.001

    }))

    if r.status_code != 400:
        exit_and_fail()

    res = dockercompose_down()
    if not res:
        assert False
