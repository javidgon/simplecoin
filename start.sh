#!/bin/bash

python -m src.node_miner &

FLASK_APP=src/node_server.py flask run --host=0.0.0.0 --port=5000