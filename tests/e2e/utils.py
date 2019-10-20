import os
import subprocess
from time import sleep

import requests
import json

from urllib.parse import urljoin


FILE_PATH = os.path.dirname(os.path.abspath(__file__))


def dockercompose_build() -> bool:
    cmd_args = ['docker-compose', 'build']

    p = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()

    return not bool(p.returncode)


def dockercompose_up() -> bool:
    cmd_args = ['docker-compose', '-f', os.path.join(FILE_PATH, '..', '..', 'docker-compose.yml'),
                '-f', os.path.join(FILE_PATH, '..', '..', 'docker-compose.yml'), 'up', '-d']

    p = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    sleep(5)

    return not bool(p.returncode)


def dockercompose_down() -> bool:

    cmd_args = ['docker-compose', 'down']

    p = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p.communicate()

    return not bool(p.returncode)


def make_transaction(url, account_address, to_address, amount, transaction_fee):
    url = urljoin(url, 'transaction')

    r = requests.post(url, data=json.dumps({
        'from': account_address,
        'to': to_address,
        'amount': amount,
        'transaction_fee': transaction_fee
    }))

    return r


def get_blockchain(url):
    url = urljoin(url, 'blockchain')
    r = requests.get(url)

    return r


def get_state(url):
    url = urljoin(url, 'state')
    r = requests.get(url)

    return r


def exit_and_fail():
    dockercompose_down()
    assert False
