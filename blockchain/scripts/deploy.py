import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'backend'))
load_dotenv(project_root / '.env')

from web3 import Web3

def deploy():
    ganache_url = os.environ.get('GANACHE_URL', 'http://127.0.0.1:7545')
    print(f"Connecting to Ethereum node / Ganache at {ganache_url}...")
    w3 = Web3(Web3.HTTPProvider(ganache_url))
    
    if not w3.is_connected():
        print(f"Error: Could not connect to Ganache at {ganache_url}. Please ensure Ganache is running.")
        return
        
    print(f"Connected! Current block number: {w3.eth.block_number}")
    accounts = w3.eth.accounts
    if not accounts:
        print("No accounts available on node.")
        return
        
    deployer = accounts[0]
    print(f"Using deployer account: {deployer}")
    print(f"Balance: {w3.from_wei(w3.eth.get_balance(deployer), 'ether')} ETH")
    
    artifact_path = project_root / 'blockchain' / 'artifacts' / 'ExamPaperRegistry.json'
    with open(artifact_path, 'r') as f:
        artifact = json.load(f)
        
    abi = artifact['abi']
    bytecode = artifact.get('bytecode') or artifact.get('bin')
    
    if not bytecode:
        print("Note: Bytecode not bundled. You can compile with solc/Remix or install py-solc-x.")
        return
        
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx_hash = Contract.constructor().transact({'from': deployer})
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    contract_address = receipt['contractAddress']
    print(f"\nContract successfully deployed at: {contract_address}")
    print(f"Tx Hash: {receipt['transactionHash'].hex()}")
    print(f"Gas used: {receipt['gasUsed']}")

if __name__ == '__main__':
    deploy()

