// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title ExamPaperRegistry
 * @dev Blockchain-based secure examination paper management system.
 *      Maintains exam metadata, document hashes, and approval status on-chain.
 *      Never stores confidential PDFs, passwords, or encryption keys on-chain.
 */
contract ExamPaperRegistry {
    
    enum ExamStatus { Pending, Approved, Rejected }
    
    struct ExamPaper {
        uint256 examId;
        bytes32 documentHash;      // SHA-256 hash of original PDF
        address uploader;          // Faculty wallet address
        string subjectCode;        // e.g. "CS401"
        string fileReference;      // Encrypted file identifier
        uint256 uploadTimestamp;
        ExamStatus status;
        address approver;          // Admin who approved/rejected
        uint256 actionTimestamp;
    }
    
    address public admin;
    uint256 public examCount;
    
    mapping(uint256 => ExamPaper) public exams;
    mapping(address => bool) public isFaculty;
    mapping(bytes32 => uint256) private hashToExamId;
    
    event FacultyRegistered(address indexed faculty);
    event FacultyRevoked(address indexed faculty);
    event ExamUploaded(
        uint256 indexed examId,
        address indexed uploader,
        string subjectCode,
        bytes32 documentHash,
        uint256 timestamp
    );
    event ExamApproved(uint256 indexed examId, address indexed approver);
    event ExamRejected(uint256 indexed examId, address indexed approver);
    
    modifier onlyAdmin() {
        require(msg.sender == admin, "ExamPaperRegistry: Only administrator permitted");
        _;
    }
    
    modifier onlyFaculty() {
        require(isFaculty[msg.sender], "ExamPaperRegistry: Only registered faculty permitted");
        _;
    }
    
    modifier onlyAuthorized() {
        require(
            msg.sender == admin || isFaculty[msg.sender],
            "ExamPaperRegistry: Caller is not authorized"
        );
        _;
    }
    
    modifier examExists(uint256 examId) {
        require(examId > 0 && examId <= examCount, "ExamPaperRegistry: Exam record does not exist");
        _;
    }
    
    constructor() {
        admin = msg.sender;
        examCount = 0;
    }
    
    function registerFaculty(address facultyAddress) external onlyAdmin {
        require(facultyAddress != address(0), "ExamPaperRegistry: Invalid address");
        require(!isFaculty[facultyAddress], "ExamPaperRegistry: Already registered");
        
        isFaculty[facultyAddress] = true;
        emit FacultyRegistered(facultyAddress);
    }
    
    function revokeFaculty(address facultyAddress) external onlyAdmin {
        require(facultyAddress != address(0), "ExamPaperRegistry: Invalid address");
        require(isFaculty[facultyAddress], "ExamPaperRegistry: Not registered faculty");
        
        isFaculty[facultyAddress] = false;
        emit FacultyRevoked(facultyAddress);
    }
    
    function uploadExam(
        string calldata subjectCode,
        bytes32 documentHash,
        string calldata fileReference
    ) external onlyAuthorized returns (uint256) {
        require(documentHash != bytes32(0), "ExamPaperRegistry: Document hash cannot be empty");
        require(bytes(subjectCode).length > 0, "ExamPaperRegistry: Subject code is required");
        require(bytes(fileReference).length > 0, "ExamPaperRegistry: File reference is required");
        
        examCount++;
        uint256 newExamId = examCount;
        
        exams[newExamId] = ExamPaper({
            examId: newExamId,
            documentHash: documentHash,
            uploader: msg.sender,
            subjectCode: subjectCode,
            fileReference: fileReference,
            uploadTimestamp: block.timestamp,
            status: ExamStatus.Pending,
            approver: address(0),
            actionTimestamp: 0
        });
        
        hashToExamId[documentHash] = newExamId;
        
        emit ExamUploaded(newExamId, msg.sender, subjectCode, documentHash, block.timestamp);
        return newExamId;
    }
    
    function approveExam(uint256 examId) external onlyAdmin examExists(examId) {
        ExamPaper storage exam = exams[examId];
        require(exam.status == ExamStatus.Pending, "ExamPaperRegistry: Exam is not in pending status");
        
        exam.status = ExamStatus.Approved;
        exam.approver = msg.sender;
        exam.actionTimestamp = block.timestamp;
        
        emit ExamApproved(examId, msg.sender);
    }
    
    function rejectExam(uint256 examId) external onlyAdmin examExists(examId) {
        ExamPaper storage exam = exams[examId];
        require(exam.status == ExamStatus.Pending, "ExamPaperRegistry: Exam is not in pending status");
        
        exam.status = ExamStatus.Rejected;
        exam.approver = msg.sender;
        exam.actionTimestamp = block.timestamp;
        
        emit ExamRejected(examId, msg.sender);
    }
    
    function verifyIntegrity(uint256 examId, bytes32 hashToVerify) external view examExists(examId) returns (bool) {
        return exams[examId].documentHash == hashToVerify;
    }
    
    function getExamDetails(uint256 examId) external view examExists(examId) returns (
        uint256 id,
        bytes32 documentHash,
        address uploader,
        string memory subjectCode,
        string memory fileReference,
        uint256 uploadTimestamp,
        uint8 status,
        address approver
    ) {
        ExamPaper storage exam = exams[examId];
        return (
            exam.examId,
            exam.documentHash,
            exam.uploader,
            exam.subjectCode,
            exam.fileReference,
            exam.uploadTimestamp,
            uint8(exam.status),
            exam.approver
        );
    }
    
    function getExamIdByHash(bytes32 documentHash) external view returns (uint256) {
        return hashToExamId[documentHash];
    }
    
    function getAdmin() external view returns (address) {
        return admin;
    }
}

