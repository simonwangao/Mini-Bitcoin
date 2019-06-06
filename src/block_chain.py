# -*- coding:utf-8 -*-
# Created by Ao Wang, 15300240004. All rights reserved.
# This file implements the blockchain, which can be stored in every wallet.

import hashlib
import json
import pickle   # we use pickle to store and load data

from ecdsa import SigningKey, VerifyingKey, SECP256k1

from Merkle_Tree import *
from utils import *

class BlockChain(object):
    def __init__(self):
        self.chain = []         # the list of block chains
    

    @staticmethod
    def hash(block):
        '''
        create a SHA-256 hash of a Block
        :param block: <dict> Block
        :return: <str>
        '''
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    

    def proof_of_work(self):
        """
        Simple Proof of Work Algorithm:
            - Find a number p' such that hash(pp') contains leading 4 zeroes
        :return: <int>
        """

        proof = 0
        rand = int(get_random_256(), 16)    # TODO: change to last block's hash?
        while self.valid_proof(rand, proof) is False:
            proof += 1

        return proof
    

    @staticmethod
    def valid_proof(rand, proof):
        """
        Validates the Proof: whether hash(last_proof, proof) contain 4 leading zeroes
        Can be changed to flexible version
        :param rand: <int> a random number
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """

        guess = f'{rand}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'
    

    @property
    def last_block(self):
        '''
        Returns the last Block in the chain
        '''
        return self.chain[-1]
    

    def valid_chain(self, chain):
        '''
        Check whether the input chain is valid
        '''
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            last_block = chain[current_index-1]

            # check the previous hash
            if block['Blockheader']['hashPreBlock'] != self.hash(last_block):
                return False
            
            # check the Merkle root
            lis = chain[:current_index]
            mt = Merkle_Tree(lis)
            mt.create_tree()
            if mt.get_root_transaction() != block['Blockheader']['hashMerkleRoot']:
                return False
            
            # check the signature
            for dic in block['Transaction']['in']:
                if dic['sig'] != 'system':  # not from mining
                    #signature = dic['sig']
                    signature = bytes(bytearray.fromhex(dic['sig']))    # get from str
                    # dic['pub_key']
                    vk = VerifyingKey.from_string(bytes(bytearray.fromhex(dic['pub_key'])), curve=SECP256k1)    # we store str to transfer via HTTP
                    
                    # this transaction's signature
                    temp = {}
                    temp['hash'] = dic['prev_out']['hash']
                    temp['n'] = dic['prev_out']['n']
                    ha = hashlib.sha256(json.dumps(temp, sort_keys=True).encode()).hexdigest()
                    if vk.verify(signature, ha.encode()) is not True:
                        return False
                        
            current_index += 1
        
        return True

