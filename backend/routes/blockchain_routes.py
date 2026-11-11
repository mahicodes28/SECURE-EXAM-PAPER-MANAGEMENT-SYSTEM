import os
from flask import Blueprint, jsonify, request
from flask_login import login_required

from backend.services.blockchain_service import BlockchainService
from backend.models import ExamPaper

blockchain_bp = Blueprint('blockchain', __name__)

@blockchain_bp.route('/status', methods=['GET'])
def blockchain_status():
    bc = BlockchainService()
    connected = bc.is_connected()
    info = {}
    if connected:
        try:
            info = {
                'block_number': bc.w3.eth.block_number,
                'chain_id': bc.w3.eth.chain_id,
                'gas_price': str(bc.w3.eth.gas_price),
                'contract_address': bc.contract_address
            }
        except Exception as e:
            info = {'error': str(e)}
    return jsonify({
        'connected': connected,
        'ganache_url': os.environ.get('GANACHE_URL', 'http://127.0.0.1:7545'),
        **info
    }), 200

@blockchain_bp.route('/latest-block', methods=['GET'])
def latest_block():
    bc = BlockchainService()
    if not bc.is_connected():
        return jsonify({'error': 'Blockchain not connected'}), 503
    try:
        block = bc.w3.eth.get_block('latest')
        return jsonify({
            'number': block['number'], 'hash': block['hash'].hex(),
            'timestamp': block['timestamp'], 'transaction_count': len(block['transactions']),
            'gas_used': block['gasUsed'], 'gas_limit': block['gasLimit']
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blockchain_bp.route('/transactions', methods=['GET'])
@login_required
def get_transactions():
    papers = ExamPaper.query.filter(ExamPaper.transaction_hash.isnot(None)).order_by(ExamPaper.created_at.desc()).limit(50).all()
    transactions = []
    for paper in papers:
        transactions.append({
            'transaction_hash': paper.transaction_hash, 'block_number': paper.block_number,
            'exam_id': paper.blockchain_exam_id, 'subject_code': paper.subject_code,
            'exam_name': paper.exam_name, 'document_hash': paper.document_hash,
            'approval_status': paper.approval_status,
            'timestamp': paper.created_at.isoformat() if paper.created_at else None, 'type': 'UPLOAD'
        })
        if paper.approval_transaction_hash:
            transactions.append({
                'transaction_hash': paper.approval_transaction_hash, 'block_number': None,
                'exam_id': paper.blockchain_exam_id, 'subject_code': paper.subject_code,
                'exam_name': paper.exam_name, 'document_hash': paper.document_hash,
                'approval_status': paper.approval_status,
                'timestamp': paper.approval_timestamp.isoformat() if paper.approval_timestamp else None,
                'type': paper.approval_status.upper()
            })
    return jsonify({'transactions': transactions}), 200

@blockchain_bp.route('/transaction/<tx_hash>', methods=['GET'])
def get_transaction(tx_hash):
    bc = BlockchainService()
    if not bc.is_connected():
        return jsonify({'error': 'Blockchain not connected'}), 503
    try:
        tx = bc.w3.eth.get_transaction(tx_hash)
        receipt = bc.w3.eth.get_transaction_receipt(tx_hash)
        return jsonify({
            'hash': tx['hash'].hex(), 'from': tx['from'], 'to': tx['to'],
            'value': str(tx['value']), 'gas': tx['gas'], 'gas_price': str(tx['gasPrice']),
            'block_number': tx['blockNumber'], 'nonce': tx['nonce'],
            'status': receipt['status'], 'gas_used': receipt['gasUsed'],
            'contract_address': receipt.get('contractAddress')
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blockchain_bp.route('/exam/<int:exam_id>', methods=['GET'])
def get_blockchain_exam(exam_id):
    bc = BlockchainService()
    if not bc.is_connected():
        return jsonify({'error': 'Blockchain not connected'}), 503
    try:
        details = bc.get_exam_details(exam_id)
        return jsonify({'exam': details}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@blockchain_bp.route('/events', methods=['GET'])
@login_required
def get_events():
    bc = BlockchainService()
    if not bc.is_connected():
        return jsonify({'error': 'Blockchain not connected', 'events': []}), 200
    try:
        events = bc.get_all_events()
        return jsonify({'events': events}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'events': []}), 200
