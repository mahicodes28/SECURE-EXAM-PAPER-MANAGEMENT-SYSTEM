# 🔐 Blockchain-Based Secure Exam Paper Management System

> **Secure Storage, Access Control & Integrity Verification**

---

## Overview

A university-grade exam paper management platform that combines **blockchain technology**, **symmetric encryption**, and **Role-Based Access Control (RBAC)** to ensure the confidentiality, integrity, and tamper-proof auditability of sensitive exam documents. Administrators manage the full lifecycle of exam papers—upload, encrypt, and distribute—while faculty access only the papers they are authorized for. Every access and mutation event is recorded on the blockchain, providing an immutable audit trail.

---

## Features

### 👨‍💼 Admin Features
- Upload and AES-encrypt exam papers before storage
- Register and manage faculty accounts with specific subject permissions
- Deploy and interact with the smart contract for access control
- View the full blockchain audit log of all operations
- Revoke faculty access at any time
- Generate hash fingerprints for paper integrity verification

### 👩‍🏫 Faculty Features
- Securely download only the exam papers assigned to them
- View paper metadata (subject, exam date, hash) without decrypting prematurely
- Receive time-locked access that expires after the exam window
- Verify paper integrity via blockchain-stored hash comparison

---

## Tech Stack

| Layer        | Technology                                      |
|--------------|-------------------------------------------------|
| **Frontend** | HTML5, CSS3, JavaScript, Jinja2 Templates       |
| **Backend**  | Python 3.9+, Flask 2.3, Flask-Login, Flask-WTF  |
| **Blockchain**| Solidity 0.8.x, Web3.py 6.x, Ganache, MetaMask |
| **Database** | SQLite (dev) via Flask-SQLAlchemy               |
| **Security** | Fernet (AES-128-CBC + HMAC), python-cryptography, WTF CSRF |

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+** — [python.org](https://www.python.org/downloads/)
- **Ganache Desktop or CLI** — [trufflesuite.com/ganache](https://trufflesuite.com/ganache/) or `npm install -g ganache`
- **MetaMask** browser extension — [metamask.io](https://metamask.io/)
- **Git** — [git-scm.com](https://git-scm.com/)

---

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd SECURE-EXAM-PAPER-MANAGEMENT-SYSTEM
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Open .env and fill in SECRET_KEY, FERNET_KEY, etc.
   ```

5. **Start Ganache**
   - Open Ganache Desktop and start a workspace on port `7545`, **or**
   - Run `ganache --port 7545` in a terminal.

6. **Deploy the smart contract**
   ```bash
   python blockchain/scripts/deploy.py
   ```

7. **Set `CONTRACT_ADDRESS` in `.env`**
   Copy the deployed contract address printed by the deploy script and paste it into `.env`.

8. **Run the Flask application**
   ```bash
   flask run
   ```

9. **Open your browser**
   Navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000) and log in with the admin credentials from `.env`.

---

## Project Structure

```
SECURE-EXAM-PAPER-MANAGEMENT-SYSTEM/
├── frontend/
│   ├── templates/          # Jinja2 HTML templates
│   └── static/
│       ├── css/            # Stylesheets
│       ├── js/             # Client-side scripts
│       └── images/         # Static images / icons
├── backend/
│   ├── __init__.py
│   ├── app.py              # Flask application factory
│   ├── models.py           # SQLAlchemy ORM models
│   ├── routes/             # Blueprint route handlers
│   │   └── __init__.py
│   ├── services/           # Business logic (encryption, blockchain calls)
│   │   └── __init__.py
│   └── utils/              # Helper utilities
│       └── __init__.py
├── blockchain/
│   ├── contracts/          # Solidity smart contracts (.sol)
│   ├── scripts/            # Deploy / interact scripts
│   ├── artifacts/          # Compiled ABIs and bytecode (auto-generated)
│   └── deployments/        # Deployment records (address, network, date)
├── encrypted_storage/      # AES-encrypted exam paper files (not committed)
├── tests/                  # Pytest test suite
│   └── __init__.py
├── .env.example            # Environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Environment Variables

| Variable               | Description                                          | Required |
|------------------------|------------------------------------------------------|----------|
| `FLASK_APP`            | Entry point for Flask (`backend/app.py`)             | ✅       |
| `FLASK_ENV`            | `development` or `production`                        | ✅       |
| `SECRET_KEY`           | Flask session signing key (32 random bytes)          | ✅       |
| `WTF_CSRF_SECRET_KEY`  | CSRF token signing key                               | ✅       |
| `DATABASE_URL`         | SQLAlchemy connection string                         | ✅       |
| `GANACHE_URL`          | JSON-RPC endpoint for local blockchain               | ✅       |
| `CONTRACT_ADDRESS`     | Deployed smart contract address                      | ✅       |
| `ADMIN_WALLET_ADDRESS` | Ethereum address of the deploying admin              | ✅       |
| `ADMIN_PRIVATE_KEY`    | Private key for signing transactions (**keep secret**) | ✅     |
| `FERNET_KEY`           | Fernet symmetric encryption key (base64)             | ✅       |
| `UPLOAD_FOLDER`        | Path where encrypted files are stored                | ✅       |
| `MAX_CONTENT_LENGTH`   | Max upload size in bytes (default 16 MB)             | ✅       |
| `ADMIN_EMAIL`          | Default admin login email                            | ✅       |
| `ADMIN_PASSWORD`       | Default admin password (**change on first login**)   | ✅       |

---

## MetaMask Setup Instructions

1. Install the [MetaMask](https://metamask.io/) browser extension.
2. Create or import a wallet.
3. Click the network selector → **Add Network** → **Add a network manually**.
4. Fill in:
   - **Network Name**: Ganache Local
   - **New RPC URL**: `http://127.0.0.1:7545`
   - **Chain ID**: `1337`
   - **Currency Symbol**: ETH
5. Import one of the Ganache accounts using its private key (shown in the Ganache UI).
6. The admin account should correspond to `ADMIN_WALLET_ADDRESS` in `.env`.

---

## Blockchain Workflow

1. **Admin uploads** an exam paper via the web portal.
2. The backend **encrypts** the file using the Fernet key and saves it to `encrypted_storage/`.
3. A **SHA-256 hash** of the original file is computed and sent to the smart contract via `web3.py`.
4. The smart contract **stores the hash on-chain** along with the uploader address and timestamp.
5. Admin **grants access** to a faculty member by calling the contract's `grantAccess` function.
6. Faculty **logs in** and requests a download; the backend verifies on-chain authorization.
7. If authorized, the backend **decrypts** the file in-memory and streams it to the faculty browser.
8. The download event is **logged on-chain** as an immutable audit entry.
9. Admin can **revoke access** at any time; subsequent download attempts are rejected.
10. Any integrity check re-hashes the stored file and compares it to the **on-chain hash** — tampering is immediately detected.

---

## Security Features

- 🔑 **Fernet Encryption** — AES-128-CBC with HMAC-SHA256 for all stored exam files
- 🔗 **Blockchain Integrity** — SHA-256 hashes stored on immutable Ethereum ledger
- 🛡️ **RBAC** — Role-Based Access Control enforced at both Flask and smart-contract layers
- 🚫 **CSRF Protection** — Flask-WTF CSRF tokens on all state-changing forms
- 🔒 **Secure Sessions** — Signed, HTTP-only cookies via Flask-Login
- 📋 **Immutable Audit Log** — Every access event permanently recorded on-chain
- ⏱️ **Time-Locked Access** — Faculty access automatically expires after the exam window
- 🚷 **Private Key Isolation** — Private keys are environment-only; never stored in code or DB

---

## API Endpoints

| Method | Endpoint                        | Auth Role | Description                        |
|--------|---------------------------------|-----------|------------------------------------|
| GET    | `/`                             | Public    | Landing / login redirect           |
| POST   | `/auth/login`                   | Public    | User login                         |
| GET    | `/auth/logout`                  | Any       | User logout                        |
| GET    | `/admin/dashboard`              | Admin     | Admin overview                     |
| POST   | `/admin/upload`                 | Admin     | Upload & encrypt an exam paper     |
| POST   | `/admin/grant-access`           | Admin     | Grant faculty access to a paper    |
| POST   | `/admin/revoke-access`          | Admin     | Revoke faculty access              |
| GET    | `/admin/audit-log`              | Admin     | View full blockchain audit log     |
| GET    | `/faculty/dashboard`            | Faculty   | Faculty overview                   |
| GET    | `/faculty/download/<paper_id>`  | Faculty   | Download authorized exam paper     |
| GET    | `/faculty/verify/<paper_id>`    | Faculty   | Verify paper integrity on-chain    |

---

## License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
