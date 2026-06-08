"""
Mock Core Banking System - Simulates downstream transaction posting
"""

import asyncio
import random
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CoreBankingSystem:
    """
    Mock Core Banking System
    Simulates posting transactions to legacy/modern core banking
    """
    
    def __init__(self):
        self.accounts_db = self._initialize_accounts()
        self.transactions_db = []
        logger.info("🏦 Core Banking System Mock initialized")
    
    def _initialize_accounts(self) -> Dict[str, Dict[str, Any]]:
        """Initialize mock account database"""
        return {
            'US12345678901234567890': {
                'account_number': 'US12345678901234567890',
                'account_name': 'John Smith Corp',
                'currency': 'USD',
                'balance': 500000.00,
                'status': 'ACTIVE'
            },
            'GB82WEST12345698765432': {
                'account_number': 'GB82WEST12345698765432',
                'account_name': 'Tech Solutions Ltd',
                'currency': 'GBP',
                'balance': 250000.00,
                'status': 'ACTIVE'
            },
            'DE89370400440532013000': {
                'account_number': 'DE89370400440532013000',
                'account_name': 'ABC GmbH',
                'currency': 'EUR',
                'balance': 100000.00,
                'status': 'ACTIVE'
            }
        }
    
    async def post_transaction(self, mx_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post MX transaction to core banking ledger
        Simulates both legacy COBOL and modern API integration
        """
        logger.info("🏦 Posting transaction to core banking ledger")
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Extract transaction details from MX message
        tx_details = self._extract_transaction_details(mx_message)
        
        # Validate accounts exist
        validation_result = self._validate_accounts(tx_details)
        if not validation_result['valid']:
            return {
                'status': 'rejected',
                'reason': validation_result['reason'],
                'transaction_id': None
            }
        
        # Simulate balance check
        balance_check = self._check_balance(tx_details)
        if not balance_check['sufficient']:
            return {
                'status': 'rejected',
                'reason': 'Insufficient funds',
                'transaction_id': None,
                'available_balance': balance_check['available']
            }
        
        # Generate transaction ID
        transaction_id = self._generate_transaction_id()
        
        # Post to ledger
        transaction_record = {
            'transaction_id': transaction_id,
            'mx_type': mx_message['mx_type'],
            'amount': tx_details.get('amount', 0),
            'currency': tx_details.get('currency', 'USD'),
            'debit_account': tx_details.get('debit_account'),
            'credit_account': tx_details.get('credit_account'),
            'status': 'posted',
            'posted_at': datetime.utcnow().isoformat() + 'Z',
            'value_date': tx_details.get('value_date'),
            'reconciliation_status': 'pending'
        }
        
        self.transactions_db.append(transaction_record)
        
        # Update account balances (in mock)
        self._update_balances(tx_details)
        
        logger.info(f"✓ Transaction posted successfully: {transaction_id}")
        
        return {
            'status': 'success',
            'transaction_id': transaction_id,
            'posted_at': transaction_record['posted_at'],
            'ledger_entry': transaction_record,
            'integration_method': 'REST API (modern core) / MQ Bridge (legacy COBOL)',
            'stp_rate': '95%'
        }
    
    def _extract_transaction_details(self, mx_message: Dict[str, Any]) -> Dict[str, Any]:
        """Extract transaction details from MX message"""
        fields = mx_message.get('fields', {})
        
        details = {
            'amount': 0,
            'currency': 'USD',
            'debit_account': None,
            'credit_account': None,
            'value_date': None
        }
        
        for path, field_data in fields.items():
            if not isinstance(field_data, dict):
                continue
            
            value = field_data.get('value')
            
            if 'Amt' in path and 'Value' in path:
                try:
                    details['amount'] = float(value)
                except (ValueError, TypeError):
                    pass
            elif 'Ccy' in path:
                details['currency'] = value
            elif 'Dbtr' in path and 'account' in path.lower():
                details['debit_account'] = value
            elif 'Cdtr' in path and 'account' in path.lower():
                details['credit_account'] = value
            elif 'SttlmDt' in path:
                details['value_date'] = value
        
        return details
    
    def _validate_accounts(self, tx_details: Dict[str, Any]) -> Dict[str, Any]:
        """Validate accounts exist and are active"""
        debit_account = tx_details.get('debit_account')
        credit_account = tx_details.get('credit_account')
        
        if not debit_account and not credit_account:
            return {
                'valid': True,  # Allow for demo
                'reason': None
            }
        
        # In production, would check both accounts
        return {
            'valid': True,
            'reason': None
        }
    
    def _check_balance(self, tx_details: Dict[str, Any]) -> Dict[str, Any]:
        """Check if sufficient balance available"""
        # Simulate balance check
        # In demo, always return sufficient
        return {
            'sufficient': True,
            'available': 999999.99
        }
    
    def _update_balances(self, tx_details: Dict[str, Any]):
        """Update account balances in mock database"""
        debit_account = tx_details.get('debit_account')
        credit_account = tx_details.get('credit_account')
        amount = tx_details.get('amount', 0)
        
        if debit_account in self.accounts_db:
            self.accounts_db[debit_account]['balance'] -= amount
        
        if credit_account in self.accounts_db:
            self.accounts_db[credit_account]['balance'] += amount
    
    def _generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        random_suffix = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        return f"TX{timestamp}{random_suffix}"
    
    def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """Query transaction status"""
        for tx in self.transactions_db:
            if tx['transaction_id'] == transaction_id:
                return {
                    'found': True,
                    'transaction': tx
                }
        
        return {
            'found': False,
            'transaction': None
        }
    
    def get_account_balance(self, account_number: str) -> Dict[str, Any]:
        """Get current account balance"""
        if account_number in self.accounts_db:
            account = self.accounts_db[account_number]
            return {
                'found': True,
                'account_number': account_number,
                'balance': account['balance'],
                'currency': account['currency'],
                'status': account['status']
            }
        
        return {
            'found': False,
            'account_number': account_number
        }
