# -*- coding:utf-8 -*-
# Created by Ao Wang, 15300240004. All rights reserved.
# This file implements necessary methods needed by the blockchain and wallet

import random
import hashlib
import base58
from time import time

def get_empty_block():
    # Create an empty block
    block = {}
    block['index'] = None   # the index of the block

    # the block header
    block['Blockheader'] = {}
    block['Blockheader']['hashPreBlock'] = None     # the hash of previous block
    block['Blockheader']['hashMerkleRoot'] = None   # the root of the Merkle tree
    block['Blockheader']['timestamp'] = time()      # the time stamp


    # the transactions part
    block['Transaction'] = {}
    trans = block['Transaction']
    trans['hash'] = None    # the transaction ID: hash of this transaction
    trans['in'] = []        # the inputs of the transaction
    trans['out'] = []       # the outputs of the transaction
    return block


def get_trans_in(pre_hash=None, n=None, sig=None, pub_key=None):
    '''
    Create an empty input of a transaction
    :param pre_hash: <str> the hash of the input transaction
    :param n: <float> the input amount
    :param sig: <str> the signature
    :param pub_key: the public key
    :return res: <dict> an empty input of transaction
    '''
    res = {}
    res['prev_out'] = {}
    res['prev_out']['hash'] = pre_hash  #
    res['prev_out']['n'] = n            #

    res['sig'] = sig                    #
    res['pub_key'] = pub_key            #
    return res


def get_trans_out(value=None, address=None, from_address=None):
    '''
    Create an empty output of a transaction
    :param value: <float> the output value
    :param address: <str> the address of target wallet
    :param from_address: <str> the address where the coins come from
    :return res: <dict> an empty output of a transaction
    '''
    res = {}
    res['value'] = value
    res['address'] = address
    res['from_address'] = from_address
    return res


def get_random_256():
    '''
    Get a random 256-bit integer
    :return: <str>
    '''
    low = int('0x0000000000000000000000000000000000000000000000000000000000000001', 16)
    up = int('0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141', 16)
    res = random.randint(low, up)
    return hex(res)[2:]


def get_wallet_address(pub_key):
    '''
    Generate the wallet address by using the public key
    Following Bitcoin protocol
    :param pub_key: <class 'ecdsa.keys.VerifyingKey'>
    :return address: <str>
    '''
    pub_string = pub_key.to_string()
    # the first SHA-256
    temp = hashlib.sha256(pub_string).hexdigest()
    # RIPEMD-160
    ha = hashlib.new('ripemd160')
    ha.update(temp.encode())
    addr = '00' + ha.hexdigest()
    # two rounds SHA-256
    temp = hashlib.sha256(addr.encode()).hexdigest()
    temp = hashlib.sha256(temp.encode()).hexdigest()
    address =  addr + temp[:8]  # add checksum
    address = base58.b58encode( bytes(bytearray.fromhex(address)) ).decode('utf-8') # !
    return address



if __name__ == '__main__':
    pass
