import os
import json
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

EXAM_REGISTRY_ABI = [
    {
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "examId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "approver", "type": "address"}
        ],
        "name": "ExamApproved",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "examId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "approver", "type": "address"}
        ],
        "name": "ExamRejected",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "examId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "uploader", "type": "address"},
            {"indexed": False, "internalType": "string", "name": "subjectCode", "type": "string"},
            {"indexed": False, "internalType": "bytes32", "name": "documentHash", "type": "bytes32"},
            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "name": "ExamUploaded",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "faculty", "type": "address"}
        ],
        "name": "FacultyRegistered",
        "type": "event"
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "address", "name": "faculty", "type": "address"}
        ],
        "name": "FacultyRevoked",
        "type": "event"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "examId", "type": "uint256"}],
        "name": "approveExam",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "examCount",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "name": "exams",
        "outputs": [
            {"internalType": "uint256", "name": "examId", "type": "uint256"},
            {"internalType": "bytes32", "name": "documentHash", "type": "bytes32"},
            {"internalType": "address", "name": "uploader", "type": "address"},
            {"internalType": "string", "name": "subjectCode", "type": "string"},
            {"internalType": "string", "name": "fileReference", "type": "string"},
            {"internalType": "uint256", "name": "uploadTimestamp", "type": "uint256"},
            {"internalType": "uint8", "name": "status", "type": "uint8"},
            {"internalType": "address", "name": "approver", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "examId", "type": "uint256"}],
        "name": "getExamDetails",
        "outputs": [
            {"internalType": "uint256", "name": "id", "type": "uint256"},
            {"internalType": "bytes32", "name": "documentHash", "type": "bytes32"},
            {"internalType": "address", "name": "uploader", "type": "address"},
            {"internalType": "string", "name": "subjectCode", "type": "string"},
            {"internalType": "string", "name": "fileReference", "type": "string"},
            {"internalType": "uint256", "name": "uploadTimestamp", "type": "uint256"},
            {"internalType": "uint8", "name": "status", "type": "uint8"},
            {"internalType": "address", "name": "approver", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "", "type": "address"}],
        "name": "isFaculty",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "uint256", "name": "examId", "type": "uint256"}],
        "name": "rejectExam",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "facultyAddress", "type": "address"}],
        "name": "registerFaculty",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "facultyAddress", "type": "address"}],
        "name": "revokeFaculty",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "string", "name": "subjectCode", "type": "string"},
            {"internalType": "bytes32", "name": "documentHash", "type": "bytes32"},
            {"internalType": "string", "name": "fileReference", "type": "string"}
        ],
        "name": "uploadExam",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "examId", "type": "uint256"},
            {"internalType": "bytes32", "name": "hashToVerify", "type": "bytes32"}
        ],
        "name": "verifyIntegrity",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

class BlockchainService:
    """
    Connects to Ethereum blockchain / Ganache testnet via Web3.py
    and interacts with ExamPaperRegistry smart contract.
    """
    
    def __init__(self):
        self.ganache_url = os.environ.get('GANACHE_URL', 'http://127.0.0.1:7545')
        self.contract_address = os.environ.get('CONTRACT_ADDRESS', '')
        self.admin_private_key = os.environ.get('ADMIN_PRIVATE_KEY', '')
        self.admin_wallet = os.environ.get('ADMIN_WALLET_ADDRESS', '')
        
        self.w3 = None
        self.contract = None
        self._connected = False
        
        self._connect()
    
    def _connect(self):
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.ganache_url))
            if self.w3.is_connected():
                self._connected = True
                
                # Check if valid contract address is configured
                if (self.contract_address and 
                    self.contract_address != 'your-deployed-contract-address-here' and
                    self.w3.is_address(self.contract_address)):
                    
                    abi = self._load_abi_from_file() or EXAM_REGISTRY_ABI
                    checksum_addr = Web3.to_checksum_address(self.contract_address)
                    self.contract = self.w3.eth.contract(address=checksum_addr, abi=abi)
                    print(f"[BlockchainService] Connected & contract initialized at {checksum_addr}")
                else:
                    print("[BlockchainService] Connected to node, awaiting contract address deployment.")
            else:
                self._connected = False
        except Exception as e:
            print(f"[BlockchainService] Connection failed: {e}")
            self._connected = False
            
    def _load_abi_from_file(self):
        try:
            artifact_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                'blockchain', 'artifacts', 'ExamPaperRegistry.json'
            )
            if os.path.exists(artifact_path):
                with open(artifact_path, 'r') as f:
                    data = json.load(f)
                    return data.get('abi')
        except Exception:
            pass
        return None
        
    def is_connected(self) -> bool:
        return self._connected and self.contract is not None
        
    def _get_admin_account(self):
        if self.admin_private_key and len(self.admin_private_key) >= 64 and 'your-admin' not in self.admin_private_key:
            pk = self.admin_private_key if self.admin_private_key.startswith('0x') else '0x' + self.admin_private_key
            return self.w3.eth.account.from_key(pk)
        
        # Local Ganache accounts
        if self.w3 and self._connected:
            accounts = self.w3.eth.accounts
            if accounts:
                return accounts[0]
        return None
        
    def _send_transaction(self, func_call, from_account=None):
        if not self.is_connected():
            raise ConnectionError("Blockchain or contract is not connected")
            
        if from_account is None:
            from_account = self._get_admin_account()
            
        if isinstance(from_account, str):
            tx_hash = func_call.transact({'from': from_account, 'gas': 500000})
        else:
            nonce = self.w3.eth.get_transaction_count(from_account.address)
            tx = func_call.build_transaction({
                'from': from_account.address,
                'nonce': nonce,
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price
            })
            signed_tx = self.w3.eth.account.sign_transaction(tx, from_account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        return {
            'transactionHash': receipt['transactionHash'].hex(),
            'blockNumber': receipt['blockNumber'],
            'gasUsed': receipt['gasUsed'],
            'status': receipt['status']
        }
        
    def register_faculty(self, faculty_wallet: str) -> dict:
        checksum_addr = Web3.to_checksum_address(faculty_wallet)
        func_call = self.contract.functions.registerFaculty(checksum_addr)
        return self._send_transaction(func_call)
        
    def revoke_faculty(self, faculty_wallet: str) -> dict:
        checksum_addr = Web3.to_checksum_address(faculty_wallet)
        func_call = self.contract.functions.revokeFaculty(checksum_addr)
        return self._send_transaction(func_call)
        
    def upload_exam(self, subject_code: str, document_hash: str, file_reference: str) -> dict:
        if not self.is_connected():
            raise ConnectionError("Blockchain is not connected")
            
        clean_hex = document_hash[2:] if document_hash.startswith('0x') else document_hash
        hash_bytes = bytes.fromhex(clean_hex)
        
        from_account = self._get_admin_account()
        if isinstance(from_account, str):
            tx_hash = self.contract.functions.uploadExam(
                subject_code, hash_bytes, file_reference
            ).transact({'from': from_account, 'gas': 500000})
        else:
            nonce = self.w3.eth.get_transaction_count(from_account.address)
            tx = self.contract.functions.uploadExam(
                subject_code, hash_bytes, file_reference
            ).build_transaction({
                'from': from_account.address,
                'nonce': nonce,
                'gas': 500000,
                'gasPrice': self.w3.eth.gas_price
            })
            signed_tx = self.w3.eth.account.sign_transaction(tx, from_account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        
        exam_id = None
        try:
            logs = self.contract.events.ExamUploaded().process_receipt(receipt)
            if logs:
                exam_id = logs[0]['args']['examId']
        except Exception:
            try:
                exam_id = self.contract.functions.examCount().call()
            except Exception:
                pass
                
        return {
            'transactionHash': receipt['transactionHash'].hex(),
            'blockNumber': receipt['blockNumber'],
            'gasUsed': receipt['gasUsed'],
            'status': receipt['status'],
            'exam_id': exam_id
        }
        
    def approve_exam(self, exam_id: int) -> dict:
        func_call = self.contract.functions.approveExam(exam_id)
        return self._send_transaction(func_call)
        
    def reject_exam(self, exam_id: int) -> dict:
        func_call = self.contract.functions.rejectExam(exam_id)
        return self._send_transaction(func_call)
        
    def get_exam_details(self, exam_id: int) -> dict:
        if not self.is_connected():
            raise ConnectionError("Blockchain is not connected")
            
        result = self.contract.functions.getExamDetails(exam_id).call()
        return {
            'examId': result[0],
            'documentHash': result[1].hex(),
            'uploader': result[2],
            'subjectCode': result[3],
            'fileReference': result[4],
            'uploadTimestamp': result[5],
            'status': result[6],
            'approver': result[7]
        }
        
    def verify_integrity(self, exam_id: int, document_hash: str) -> bool:
        if not self.is_connected():
            raise ConnectionError("Blockchain is not connected")
        clean_hex = document_hash[2:] if document_hash.startswith('0x') else document_hash
        hash_bytes = bytes.fromhex(clean_hex)
        return self.contract.functions.verifyIntegrity(exam_id, hash_bytes).call()
        
    def get_all_events(self) -> list:
        if not self.is_connected():
            return []
            
        events = []
        try:
            upload_events = self.contract.events.ExamUploaded.get_logs(from_block=0)
            for ev in upload_events:
                events.append({
                    'event': 'ExamUploaded',
                    'exam_id': ev['args']['examId'],
                    'uploader': ev['args']['uploader'],
                    'subject_code': ev['args']['subjectCode'],
                    'document_hash': ev['args']['documentHash'].hex(),
                    'timestamp': ev['args']['timestamp'],
                    'transaction_hash': ev['transactionHash'].hex(),
                    'block_number': ev['blockNumber']
                })
        except Exception:
            pass
            
        try:
            approve_events = self.contract.events.ExamApproved.get_logs(from_block=0)
            for ev in approve_events:
                events.append({
                    'event': 'ExamApproved',
                    'exam_id': ev['args']['examId'],
                    'approver': ev['args']['approver'],
                    'transaction_hash': ev['transactionHash'].hex(),
                    'block_number': ev['blockNumber']
                })
        except Exception:
            pass
            
        try:
            reject_events = self.contract.events.ExamRejected.get_logs(from_block=0)
            for ev in reject_events:
                events.append({
                    'event': 'ExamRejected',
                    'exam_id': ev['args']['examId'],
                    'approver': ev['args']['approver'],
                    'transaction_hash': ev['transactionHash'].hex(),
                    'block_number': ev['blockNumber']
                })
        except Exception:
            pass
            
        return sorted(events, key=lambda x: x.get('block_number', 0), reverse=True)

