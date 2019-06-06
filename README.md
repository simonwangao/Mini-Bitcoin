# Mini-Bitcoin
The Python implementation of mini Bitcoin wallet.  

## Features
* Follow most of Bitcoin protocols and block structures.  
* Support block mining, transaction and verification.  
* Implement [Merkle Tree](https://en.wikipedia.org/wiki/Merkle_tree) to verify transactions.  
* Use HTTP protocol to connect and set up P2P network.
* The block chain and keys are stored locally to avoid loss.


## Usage
Install required packages:   
```
$ pip3 install -r requirements.txt
```  

Run the wallet with chosen port (default is 10000):   
```
$ python3 main.py -p {port}
```  
  
Register the addresses of peers first, then input `help` or `-h` to check legal commands.


## Reference
1. the [Developer Documentation](https://bitcoin.org/en/developer-documentation) of Bitcoin
2. this [blog](https://hackernoon.com/learn-blockchains-by-building-one-117428612f46)