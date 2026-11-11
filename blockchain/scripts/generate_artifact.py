import json
import os

artifact = {
  "contractName": "ExamPaperRegistry",
  "abi": [
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
      "inputs": [{"internalType": "bytes32", "name": "documentHash", "type": "bytes32"}],
      "name": "getExamIdByHash",
      "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "getAdmin",
      "outputs": [{"internalType": "address", "name": "", "type": "address"}],
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
      "inputs": [{"internalType": "uint256", "name": "examId", "type": "uint256"}],
      "name": "rejectExam",
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
}

target_path = r"c:\Users\Mahi\Desktop\6th-sem files\ibmproj\SECURE-EXAM-PAPER-MANAGEMENT-SYSTEM\blockchain\artifacts\ExamPaperRegistry.json"
os.makedirs(os.path.dirname(target_path), exist_ok=True)
with open(target_path, "w") as f:
    json.dump(artifact, f, indent=2)
print("Artifact saved successfully!")

