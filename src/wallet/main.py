import sys
import os
import json
from typing import List, Dict

import requests
import pprint

from urllib.parse import urljoin


pp = pprint.PrettyPrinter(indent=4)


NODE_URL = os.getenv('NODE_URL')


def get_transactions_for_account(account_address: str) -> List[Dict]:
    transactions = []

    url = urljoin(NODE_URL, 'blockchain')
    r = requests.get(url)

    r.raise_for_status()

    blockchain = json.loads(r.content)

    for block in blockchain:
        for transaction in block['data']['transactions']:
            if transaction['to'] == account_address:
                transactions.append(transaction)
            elif transaction['from'] == account_address:
                transactions.append(transaction)

    return transactions


def get_balance_for_account(transactions: List[Dict]):
    balance = 0.0

    for transaction in transactions:
        if transaction['to'] == account_address:
            balance += transaction['amount']
        elif transaction['from'] == account_address:
            balance -= transaction['amount']

    return balance


def send_money(account_address: str, to_address: str, amount: float, transaction_fee: float) -> None:
    if account_address == to_address:
        print('FROM and TO cannot be the same address.')
        return

    amount = float(amount)
    transaction_fee = float(transaction_fee)

    transactions = get_transactions_for_account(account_address)
    balance = get_balance_for_account(transactions)

    if balance - amount - transaction_fee > 0:

        url = urljoin(NODE_URL, 'transaction')

        r = requests.post(url, data=json.dumps({
            'from': account_address,
            'to': to_address,
            'amount': amount,
            'transaction_fee': transaction_fee
        }))

        r.raise_for_status()
        print(r.content.decode())


    else:
        print('Unfortunately the balance is insufficient.')
        return


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Please provide the <method> and <account_address>')
        exit(1)

    type = sys.argv[1]
    account_address = sys.argv[2]

    if type == 'get_balance':
        transactions = get_transactions_for_account(account_address)
        balance = get_balance_for_account(transactions)

        print(f'Current balance is: {balance}')
        print('Transactions:')
        pp.pprint(transactions)

    if type == 'send_money':
        if len(sys.argv) < 5:
            print('To send money, please provide the <to_address>, <amount> and <transaction_fee>')
            exit(1)

        to_address = sys.argv[3]
        amount = sys.argv[4]
        transaction_fee = sys.argv[5]

        send_money(account_address, to_address, amount, transaction_fee)
