# -*- coding:utf-8 -*-
# Created by Ao Wang, 15300240004. All rights reserved.
# This file implements Merkle Tree.

import hashlib
import json
from collections import OrderedDict

class Merkle_Node(object):
    def __init__(self, parent=None, transaction=None, lchild=None, rchild=None):
        self.parent = parent
        self.transaction = transaction
        self.lchild = lchild
        self.rchild = rchild


class Merkle_Tree(object):
    def __init__(self, transaction_list=[]):
        self.transaction_list = transaction_list
        self.tree_nodes = OrderedDict()    # store all the tree nodes, hash is the key
        self.last_nodes = []    # store the tree nodes in last layer
        self.root = None

        # initialize
        for trans in self.transaction_list:
            node = Merkle_Node()
            node.transaction = trans
            temp = json.dumps(node.transaction, sort_keys=True).encode()
            self.tree_nodes[hashlib.sha256(temp).hexdigest()] = node
            self.last_nodes.append(node)
    
    def create_tree(self):
        if len(self.transaction_list) == 0:
            return

        last_nodes = self.last_nodes
        temp_nodes = []

        # loop through all the current nodes
        for index in range(0, len(last_nodes), 2):
            # get the two siblings
            current_node = last_nodes[index]
            if index+1 != len(last_nodes):
                sibling_node = last_nodes[index+1]
            else:
                sibling_node = None
            
            # get hash
            if type(current_node.transaction) != str:
                # it's leaf node, transaction is real
                temp = json.dumps(current_node.transaction, sort_keys=True).encode()
                current_hash = hashlib.sha256(temp).hexdigest()
                # sibling is also leaf node
                if sibling_node is not None:
                    temp = json.dumps(sibling_node.transaction, sort_keys=True).encode()
                    sibling_hash = hashlib.sha256(temp).hexdigest()
            else:
                # the inner nodes, transaction is str
                current_hash = hashlib.sha256(current_node.transaction.encode()).hexdigest()
                if sibling_node is not None:
                    sibling_hash = hashlib.sha256(sibling_node.transaction.encode()).hexdigest()
            
            if len(last_nodes) != 1:
                # get the parent node
                parent_node = Merkle_Node()
                if sibling_node is not None:
                    parent_node.transaction = hashlib.sha256((current_hash + sibling_hash).encode()).hexdigest()
                else:
                    parent_node.transaction = hashlib.sha256(current_hash.encode()).hexdigest()
                parent_node.lchild = current_node
                parent_node.rchild = sibling_node
                current_node.parent = parent_node
                if sibling_node is not None:
                    sibling_node.parent = parent_node
                
                temp_nodes.append(parent_node)  # the node in this layer

                self.tree_nodes[parent_node.transaction] = parent_node # hash is the key
        
        if len(last_nodes) != 1:
            self.last_nodes = temp_nodes
            self.create_tree()
        else:
            self.root = last_nodes[0]
    
    def get_root(self):
        # Create the tree first
        return self.root
    
    def get_tree_nodes(self):
        # Return the dict, hash is the key
        return self.tree_nodes
    
    def get_root_transaction(self):
        # get the top hash result of the root
        # Create the tree first
        if len(self.transaction_list) == 0:
            return None
        elif len(self.transaction_list) == 1:
            return hashlib.sha256(json.dumps(self.transaction_list[0], sort_keys=True).encode()).hexdigest()
        else:
            return self.root.transaction

# 检查数据是否被修改就只需要计算一下交易记录的梅克尔树的根节点,然后和区块头的梅克尔跟比较就可以得出结果了。
    
def Merkle_proof(tree, hash_val):
    """
    Decide whether the hash value is in the tree
    :param tree: <Merkle_Tree()> a Merkle tree
    :param hash_val: <str> the undecided hash value
    :return: <boolean> True or False
    """
    pass


if __name__ == '__main__':
    trans_list = ['a', 'b', 'c', 'd', 'e']
    mt = Merkle_Tree(trans_list)
    mt.create_tree()
    print (mt.get_root_transaction())

