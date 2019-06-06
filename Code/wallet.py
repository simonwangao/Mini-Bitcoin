# -*- coding:utf-8 -*-
# Created by Ao Wang, 15300240004. All rights reserved.
# This file implements the wallet of the blockchain

import json
import pickle   # we use pickle to store and load data
import sys
import os
from urllib.parse import urlparse
import requests

from flask import Flask, jsonify, request
from ecdsa import SigningKey, VerifyingKey, SECP256k1

from block_chain import *
from utils import *

path = sys.path[0]
os.chdir(path)  # change to current directory


class Wallet(object):
    def __init__(self, key_gen=False, load_key=True):
        '''
        Initialize the wallet
        Default is to load existed keys
        User can choose to load exists keys in .pkl file
        '''
        self.pri_key = None                 # private key
        self.pub_key = None                 # public key
        self.address = None                 # wallet address

        self.blockchain = BlockChain()      # the block chain in this wallet
        self.peers = []                     # other wallet peers in the network, which are neighbors

        if key_gen is True and load_key is not True:
            self.generate_keys()
        if key_gen is not True and load_key is True:
            self.load_keys()
        if (key_gen is True and load_key is True) or \
            (key_gen is not True and load_key is not True):
            print ('key_gen and load_key can\'t have the same boolean value!')
            exit(0)

        if os.path.exists('database/blockchain.pkl') is True:
            with open('database/blockchain.pkl', 'rb') as file:
                self.blockchain = pickle.load(file)
        else:
            # the very first block
            block = get_empty_block()
            block['index'] = 0
            block['Blockheader']['hashPreBlock'] = 1
            self.blockchain.chain.append(block)
        
        # update to the newest chain
        self.resolve_conflicts()


    def store_chain(self):
        # store the Blockchain object
        with open('database/blockchain.pkl', 'wb') as file:
            pickle.dump(self.blockchain, file)

    
    def generate_keys(self):
        '''
        Generate keys and wallet address
        Use .to_string().hex() to get hex string from the object
        '''
        self.pri_key = SigningKey.generate(curve=SECP256k1) # protocol for Bitcoin
        with open ('database/pri_key.pem','w') as file:
            # use SSL standard to store key
            file.write(self.pri_key.to_pem().decode())
        
        self.pub_key = self.pri_key.get_verifying_key()
        with open('database/pub_key.pem','w') as file:
            # use SSL standard to store key
            file.write(self.pub_key.to_pem().decode())
        
        self.address = get_wallet_address(self.pub_key)
        with open('database/address.pkl', 'wb') as file:
            pickle.dump(self.address, file)
        
        print ('Current wallet address: %s'%self.address)
    

    def load_keys(self):
        # load keys and address from existed files
        if os.path.exists('database/pri_key.pem') is not True \
            or os.path.exists('database/pub_key.pem') is not True \
            or os.path.exists('database/address.pkl') is not True:
            self.generate_keys()
        else:
            self.pri_key = SigningKey.from_pem(open('database/pri_key.pem').read())
            self.pub_key = VerifyingKey.from_pem(open('database/pub_key.pem').read())
            with open('database/address.pkl', 'rb') as file:
                self.address = pickle.load(file)
            print ('Current wallet address: %s'%self.address)
    

    def get_balance(self):
        '''
        Get the remaining balance of this wallet
        :return balance: <float> the balance
        '''
        self.resolve_conflicts()    # update
        balance = 0.0

        # check the output only
        # even if all the coins are transfered to others,
        # we transfer 0.0 to ourself, which is easier to calculate balance
        for block in self.blockchain.chain:
            block_amount = self.get_block_balance(block)
            balance += block_amount
        return balance
    

    def get_block_balance(self, block):
        '''
        Get the output balance from the input block of this wallet
        :param block: input block
        :return amount: <float> the output amount
        '''
        amount = 0.0
        flag = False
        lis = block['Transaction']['out']
        for dic in lis:
            if dic['address'] == self.address:
                flag = True
                break
        
        if flag is False:
            # has nothing to do with me
            return amount
        else:
            if len(lis) == 1:
                # reward of mining
                amount += lis[0]['value']
            else:
                if lis[0]['from_address'] == self.address:
                    # transfer to others
                    for dic in lis:
                        if dic['address'] != self.address:
                            amount -= dic['value']
                else:
                    # transfer to me
                    for dic in lis:
                        if dic['address'] == self.address:
                            amount += dic['value']
        return amount


    def get_transaction_input_blocks(self, amount):
        '''
        Get a list of blocks acting as the input of a transaction with my coins
        :param amount: <float> the needed amount
        :return block_dict: <dict> the dict of blocks and balance or None
        '''
        balance = 0.0
        block_dict = {}

        # check the output only
        for block in self.blockchain.chain:
            pre_balance = balance
            block_balance = self.get_block_balance(block)
            if block_balance != 0.0:
                balance += block_balance
                block_str = str(block)
                block_dict[block_str] = block_balance   # use str as hash key
            if pre_balance < amount and balance >= amount:
                return block_dict
        
        if balance < amount:
            return None # coins not enough
    

    def peer_register(self, address):
        """
        Add a new peer to the list of peers
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """

        parsed_url = urlparse(address)
        self.peers.append(parsed_url.netloc)
        self.peers = list( set(self.peers) )    # delete the duplicate ones


    def resolve_conflicts(self):
        """
        This is our Consensus Algorithm, it resolves conflicts.
        Replace my chain with the longest one
        :return: <bool> True if our chain was replaced, False if not
        """
        neighbors = self.peers
        new_chain = None

        max_length = len(self.blockchain.chain)

        for node in neighbors:
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.blockchain.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        
        if new_chain:
            assert self.blockchain.valid_chain(new_chain) == True
            self.blockchain.chain = new_chain
            self.store_chain()  # store the new one
            return True
        return False



if __name__ == '__main__':
    pass
