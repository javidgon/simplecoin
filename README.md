# Simplecoin

[![Build Status](https://travis-ci.org/javidgon/simplecoin.svg?branch=master)](https://travis-ci.org/javidgon/simplecoin)

Simplecoin is a "simple" (just 2 main files), yet quite "feature-complete" blockchain implementation in Python that tries to replicate other mainstream digital-coins
 for "learning purposes". Due to the fact that it get inspiration from multiple coins (and approaches), it doesn't aim to be 100% "realistic".
 
Originally inspired by the great Gerald Nash's [post](https://medium.com/crypto-currently/lets-build-the-tiniest-blockchain-e70965a248b).


## Features

* Multi-node network resistant to outages of certain nodes.
* Persistent blockchain and node's state (one file per node)
* Functional "Proof of Work" implementation with dynamic difficulty.
* Intelligent "concensus" between nodes to detect and replace "corrupted/tampered blockchains".
* Integrity check of account's balance before processing a transaction.
* Automatic validation of Blockchain per node.
* Automatic propagation of blockchain among all nodes in the network.
* Implementation of "Mining Fee" per transaction.
* Functional Wallet implementation.


## Limitations

* For consistency reasons, only 1 node in the network can mine at the same time.
* Addresses are, at the moment, not checked as valid SHA256 hashes (any string can be an address)


## How does it work

> Please note, each Node contains a `server` and a `miner` processes

1. Client makes a transaction request to any node of the network (by using the `Wallet` or a simple `api request`)
2. Transaction is received and stored by the node's server in the `pending_transactions` state.
3. After a certain amount of time, the node's miner will start running (it runs periodically).
4. The miner will look for consensus in the network, meaning, that it will look by the `Blockchain` shared by a majority 
of nodes. The selected one, will replace his current `Blockchain` (if it differs)
5. The miner will `mine` a "simplecoin" by creating a new `Block` (using the `Proof of Work`), and will attach all the node's `pending_transactions` to it.
6. In addition to all the `pending_transactions`, the miner will add `transaction_fee` transactions (each original transaction will have a `transaction_fee` transaction associated).
7. The miner will add the newly created `Block` (with all the transactions attached) to his `Blockchain`.
8. The miner will propagate the new `Blockchain` to all the nodes in the network.
9. All the nodes will update their own `Blockchains` with the new `Blockchain` sent by the targeted node.


## Proof of Work

The proof of work is pretty simple. It looks for hashes for new Blocks that start by `0000...` (4 zeroes at the initial difficulty). If so, it considers it a valid `Block`
for the network.


## How to build the Network locally

> It requires Docker (and Docker-compose for the "multi-node" version)

#### Single Node
> Please notice that at the start of the Blockchain, only the "network" account will have funds (1000 Millions).
For this reason, your first transaction should be FROM this account.

```python
docker build -t simplecoin .
```

```python
docker run -e NODE_URL=http://0.0.0.0:5000 -e MINER_ACCOUNT_ADDRESS=0faf32a51f4e2b02d2e4c6132c5ef40bac4d075a513bd834d1010ae684f69bff -p 5001:5000 simplecoin
```

That's it! It should work now if you create a new transaction (sha256 values specified in the request are examples):

```bash
curl "http://0.0.0.0:5001/transaction" \
     -H "Content-Type: application/json" \
     -d '{"from": "network", "to":"000067bd199453edf94b560599dd812b82b4a1a8efc4d462e8813c765d2b7c75", "amount": 3.0, "transaction_fee": 0.1}'
```

Please notice that the transaction will get scheduled. This means that you will need to wait a few minutes until the miner picks it up and adds a new Block to the Blockchain. Afterwards, you should be able to inspect it by running:

```bash
curl "http://0.0.0.0:5001/blockchain"
```

#### Multi Node
> Please notice that at the start of the Blockchain, only the "network" account will have funds (1000 Millions).
For this reason, your first transaction should be FROM this account.

```python
docker-compose build
```

```python
docker-compose up
```

This will create 3 nodes. Each reachable by the following ports: `5001`, `5002` and `5003`. You can now make a transaction to any node, and it will be propagated
to all the network (sha256 values specified in the request are examples):

```bash
curl "http://0.0.0.0:5001/transaction" \
     -H "Content-Type: application/json" \
     -d '{"from": "network", "to":"000067bd199453edf94b560599dd812b82b4a1a8efc4d462e8813c765d2b7c75", "amount": 3.0, "transaction_fee": 0.1}'
```


## Wallet

> It requires Python 3.7+

```python
cd wallet
```

```python
pipenv install
```

The wallet includes the following basic functionality:
* **get_balance**:  e.g., `python main.py get_balance <from_address>`

```python
# (sha256 values specified here are examples)

NODE_URL=http://0.0.0.0:5001 python main.py get_balance 000067bd199453edf94b560599dd812b82b4a1a8efc4d462e8813c765d2b7c75
```

* **send_money**: e.g., `python main.py send_money <from_address> <to_address> <amount> <transaction_fee>`
```python
# (sha256 values specified here are examples)

NODE_URL=http://0.0.0.0:5001 python main.py send_money network 000067bd199453edf94b560599dd812b82b4a1a8efc4d462e8813c765d2b7c75 2.0 0.1
```

## Tests

> It requires `docker-compose`
```python
pytest
```

## TODO

* Create a Queue to better do a "round-robin" among different nodes


## LICENSE

MIT