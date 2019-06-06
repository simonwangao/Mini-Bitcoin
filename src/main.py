# -*- coding:utf-8 -*-
# Created by Ao Wang, 15300240004. All rights reserved.
# This file implements the operations on P2P network by using HTTP protocol

import hashlib
import json
import sys
import os
from argparse import ArgumentParser
import threading
import requests

# disable Flask's output
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from flask import Flask, jsonify, request

from block_chain import *
from utils import *
from wallet import *
from Merkle_Tree import *

path = sys.path[0]
os.chdir(path)  # change to current directory


app = Flask(__name__)


# the instance of the wallet
my_wallet = Wallet()

@app.route('/mine', methods=['GET'])
def mine():
    '''
    Mine a block. Reward is 5.0 coins.
    '''
    my_wallet.resolve_conflicts()   # update from peers
    assert my_wallet.blockchain.valid_chain(my_wallet.blockchain.chain) == True
    last_block = my_wallet.blockchain.last_block

    proof = my_wallet.blockchain.proof_of_work()    # do the calculation

    # create a new block
    block = get_empty_block()
    block['index'] = last_block['index'] + 1
    block['Blockheader']['hashPreBlock'] = my_wallet.blockchain.hash(last_block)

    mt = Merkle_Tree(my_wallet.blockchain.chain)
    mt.create_tree()
    block['Blockheader']['hashMerkleRoot'] = mt.get_root_transaction()

    trans_in = get_trans_in(n=5.0, sig='system')
    block['Transaction']['in'].append(trans_in)

    trans_out = get_trans_out(value=5.0, address=my_wallet.address, from_address='system')
    block['Transaction']['out'].append(trans_out)

    temp={}
    temp['in'] = block['Transaction']['in']
    temp['out'] = block['Transaction']['out']
    block['Transaction']['hash'] = hashlib.sha256(json.dumps(temp, sort_keys=True).encode()).hexdigest()

    my_wallet.blockchain.chain.append(block)
    my_wallet.store_chain()

    response = {
        'message': 'Mining succeed',
        'index': block['index'],
        'amount': '5.0',
    }
    return jsonify(response), 200


# even if all the coins are transfered to others,
# we transfer 0.0 to ourself, which is easier to calculate balance

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    '''
    A new transfer from current wallet
    Use Postman to transfer parameters
    Parameters transfered to Postman:
    {
        "value":    ,
        "address":  ""
    }
    '''
    my_wallet.resolve_conflicts()
    assert my_wallet.blockchain.valid_chain(my_wallet.blockchain.chain) == True
    last_block = my_wallet.blockchain.last_block

    values = request.get_json()
    # Check that the required fields are in the POST'ed data
    required = ['value', 'address']
    if not all(k in values for k in required):
        return 'Missing values', 400
    
    balance = my_wallet.get_balance()
    amount = values['value']
    if balance < amount:
        # balance is not enough
        return 'Balance not enough', 403
    
    # the new block
    new_block = get_empty_block()
    new_block['index'] = last_block['index'] + 1
    new_block['Blockheader']['hashPreBlock'] = my_wallet.blockchain.hash(last_block)
    mt = Merkle_Tree(my_wallet.blockchain.chain)
    mt.create_tree()
    new_block['Blockheader']['hashMerkleRoot'] = mt.get_root_transaction()

    # get the blocks for input
    block_dict = my_wallet.get_transaction_input_blocks(amount)
    # deploy tran_in
    coins = 0.0
    for block_str in block_dict:    # key is str
        block = eval(block_str)
        if coins + block_dict[block_str] < amount:  # all the coins in the block
            n = block_dict[block_str]
        else:   # part of the coins
            n = amount - coins
        coins += block_dict[block_str]

        pre_hash = block['Transaction']['hash']
        temp = {}
        temp['hash'] = pre_hash
        temp['n'] = n

        ha = hashlib.sha256(json.dumps(temp, sort_keys=True).encode()).hexdigest()
        sig = my_wallet.pri_key.sign(ha.encode()).hex() # str, use private key to sign the hash
        pub_key = my_wallet.pub_key.to_string().hex()   # str
        
        trans_in = get_trans_in(pre_hash=pre_hash, n=n, sig=sig, pub_key=pub_key)   # dict
        new_block['Transaction']['in'].append(trans_in) # add the input
    
    trans_out_1 = get_trans_out(value=amount, address=values['address'], from_address=my_wallet.address)
    trans_out_2 = get_trans_out(value=coins-amount, address=my_wallet.address, from_address=my_wallet.address)    # coins-amount (maybe 0.0) to my wallet
    new_block['Transaction']['out'].append(trans_out_1)
    new_block['Transaction']['out'].append(trans_out_2)

    # get the transaction hash
    temp={}
    temp['in'] = new_block['Transaction']['in']
    temp['out'] = new_block['Transaction']['out']
    new_block['Transaction']['hash'] = hashlib.sha256(json.dumps(temp, sort_keys=True).encode()).hexdigest()

    my_wallet.blockchain.chain.append(new_block)
    my_wallet.store_chain() # store the chain

    addr = values['address']
    response = {'message': f'{amount} coins has been transfered to {addr}.'}
    return jsonify(response), 201


@app.route('/balance', methods=['GET'])
def get_balance():
    '''
    Get the balance of this wallet
    '''
    balance = my_wallet.get_balance()
    response = {'message': f'My balance is {balance} coins'}
    return jsonify(response), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    '''
    Get the full chain of this wallet
    '''
    response = {
        'chain': my_wallet.blockchain.chain,
        'length': len(my_wallet.blockchain.chain),
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    """
    Register other nodes for my wallet
    Input:
    {
        "nodes": [""]
    }
    :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
    :return: None
    """
    values = request.get_json()
    nodes = values.get('nodes') # get from the input of Postman
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    
    for node in nodes:
        my_wallet.peer_register(node)
    
    response = {
        'message': 'New peer nodes have been added',
        'total_nodes': list(my_wallet.peers),
    }
    return jsonify(response), 201


@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    '''
    Our consensus algorithm.
    '''
    replaced = my_wallet.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': my_wallet.blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': my_wallet.blockchain.chain
        }

    return jsonify(response), 200


@app.route('/address', methods=['GET'])
def get_address():
    '''
    Get the address of this wallet.
    '''
    response = {
        'message': f'My wallet address is {my_wallet.address}',
    }
    return jsonify(response), 201


@app.route('/nodes/neighbors', methods=['GET'])
def get_neighbors():
    '''
    Get the peer neighbors of this wallet
    '''
    response = {
        'message': f'My peers are {my_wallet.peers}',
    }
    return jsonify(response), 201




# Use commands to automatically send HTTP requests
def Mine(port):
    # port is an integer
    url = 'http://127.0.0.1:' + str(port) + '/mine'
    response = requests.get(url)
    print(response.text)


def New_transaction(port, value, address):
    url = 'http://127.0.0.1:' + str(port) + '/transactions/new'
    params = {"value": value, "address": address}
    params = json.dumps(params)
    headers = {"Content-type": "application/json", "Accept": "raw"}
    response = requests.post(url, data=params, headers=headers)
    dic = response.json()
    print (dic['message'])


def Get_balance(port):
    url = 'http://127.0.0.1:' + str(port) + '/balance'
    response = requests.get(url)
    dic = response.json()
    print (dic['message'])


def Full_chain(port):
    url = 'http://127.0.0.1:' + str(port) + '/chain'
    response = requests.get(url)
    print(response.text)


def Register_nodes(port, addr_lis):
    url = 'http://127.0.0.1:' + str(port) + '/nodes/register'
    params = {"nodes": addr_lis}
    params = json.dumps(params)
    headers = {"Content-type": "application/json", "Accept": "raw"}
    response = requests.post(url, data=params, headers=headers).text
    print (response)


def Consensus(port):
    url = 'http://127.0.0.1:' + str(port) + '/nodes/resolve'
    response = requests.get(url)
    dic = response.json()
    print (dic['message'])



def Get_address(port):
    url = 'http://127.0.0.1:' + str(port) + '/address'
    response = requests.get(url)
    dic = response.json()
    print (dic['message'])


def Get_neighbors(port):
    url = 'http://127.0.0.1:' + str(port) + '/nodes/neighbors'
    response = requests.get(url)
    dic = response.json()
    print (dic['message'])


def run_flask_app(port):
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'    # disable Flask's output
    app.run(host='127.0.0.1', port=port)

def main():
    '''
    The main function of this program
    '''
    neighbors_list = []
    # Manually register neighbors first
    while True:
        neighbor = input('Input the address of neighbor (Eg. http://192.168.0.5:5000). \nPress ENTER to stop: ')
        if neighbor == '':
            break
        neighbors_list.append(neighbor)
    Register_nodes(port, neighbors_list)

    # Input commands
    while True:
        print ('\n')
        command = input('Input your operation command. Enter help or -h for help: ')
        if command == 'help' or command == '-h':
            print ('mine / -m:\t\tMine a new block for this wallet.')
            print ('transaction / -t:\tTransfer coins to another address.')
            print ('balance / -b:\t\tGet the balance of this wallet.')
            print ('chain / -c:\t\tGet the full chain of this wallet.')
            print ('resolve / -r:\t\tResolve the blockchain conflicts.')
            print ('address / -a:\t\tGet the address of this wallet.')
            print ('neighbors / -n:\t\tGet the peer neighbors of this wallet.')
            print ('peer_register / -p:\tRegister new peer neighbors.')
            continue
        
        if command == 'mine' or command == '-m':
            Mine(port)
            continue
        
        if command == 'transaction' or command == '-t':
            try:
                value = input('Input the transfer value: ')
                address = input('Input the target wallet address: ')
                New_transaction(port, float(value), address)
                continue
            except:
                print ('Error: balance not enough!')
        
        if command == 'balance' or command == '-b':
            Get_balance(port)
            continue
        
        if command == 'chain' or command == '-c':
            Full_chain(port)
            continue
        
        if command == 'resolve' or command == '-r':
            Consensus(port)
            continue
        
        if command == 'address' or command == '-a':
            Get_address(port)
            continue
        

        if command == 'neighbors' or command == '-n':
            Get_neighbors(port)
            continue
        

        if command == 'peer_register' or command == '-p':
            neighbors_list = []
            while True:
                neighbor = input('Input the address of neighbor (Eg. http://192.168.0.5:5000). \nPress ENTER to stop: ')
                if neighbor == '':
                    break
                neighbors_list.append(neighbor)
            Register_nodes(port, neighbors_list)
            continue


if __name__ == '__main__':
    # input the port from the begining
    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=10000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port    # get the port

    print ('\n')
    threads = []
    t1 = threading.Thread(target=run_flask_app, args=(port,))
    threads.append(t1)
    t2 = threading.Thread(target=main)
    threads.append(t2)

    for t in threads:
        #t.setDaemon(True)
        t.start()
    
