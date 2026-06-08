"""
MT Message Generator Agent
Generates SWIFT MT messages from parsed fields
"""

import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MTGeneratorAgent:
    """
    Agent responsible for generating SWIFT MT messages from field data
    Supports MT101, MT103, and MT202 formats
    """
    
    def __init__(self):
        self.name = "MT Generator Agent"
        logger.info(f"🤖 {self.name} initialized")
    
    def generate(self, fields: Dict[str, Any], mt_type: str) -> str:
        """Generate MT message from parsed fields"""
        
        if mt_type == 'MT101':
            return self._generate_mt101(fields)
        elif mt_type == 'MT103':
            return self._generate_mt103(fields)
        elif mt_type == 'MT202':
            return self._generate_mt202(fields)
        else:
            raise ValueError(f"Unsupported MT type: {mt_type}")
    
    def _generate_mt101(self, fields: Dict[str, Any]) -> str:
        """Generate MT101 message"""
        mt = "{1:F01BANKXXXX0000000000}{2:I101BANKUSXXAXXXN}{4:\n"
        
        # Field 20: Sender Reference
        if 'sender_reference' in fields:
            mt += f":20:{fields['sender_reference']}\n"
        
        # Field 28D: Message Index/Total
        if 'message_index' in fields:
            mt += f":28D:{fields['message_index']}\n"
        
        # Field 30: Execution Date
        if 'execution_date' in fields:
            mt += f":30:{fields['execution_date']}\n"
        
        # Field 21: Transaction Reference
        if 'transaction_reference' in fields:
            mt += f":21:{fields['transaction_reference']}\n"
        
        # Field 50H: Ordering Customer
        mt += ":50H:"
        if 'ordering_customer_account' in fields:
            mt += f"/{fields['ordering_customer_account']}\n"
        if 'ordering_customer' in fields:
            mt += fields['ordering_customer']
            if 'ordering_customer_address' in fields:
                mt += f"\n{fields['ordering_customer_address']}"
        mt += "\n"
        
        # Field 52A: Ordering Institution
        if 'ordering_institution' in fields:
            mt += f":52A:{fields['ordering_institution']}\n"
        
        # Field 32B: Currency and Amount
        if 'currency' in fields and 'amount' in fields:
            amount = fields['amount'].replace('.', ',')
            mt += f":32B:{fields['currency']}{amount}\n"
        
        # Field 59: Beneficiary Customer
        mt += ":59:"
        if 'beneficiary_customer_account' in fields:
            mt += f"/{fields['beneficiary_customer_account']}\n"
        if 'beneficiary_customer' in fields:
            mt += fields['beneficiary_customer']
            if 'beneficiary_customer_address' in fields:
                mt += f"\n{fields['beneficiary_customer_address']}"
        mt += "\n"
        
        # Field 71A: Details of Charges
        if 'charge_bearer' in fields:
            mt += f":71A:{fields['charge_bearer']}\n"
        
        # Field 70: Remittance Information
        if 'remittance_info' in fields:
            mt += f":70:{fields['remittance_info']}\n"
        
        mt += "-}"
        return mt
    
    def _generate_mt103(self, fields: Dict[str, Any]) -> str:
        """Generate MT103 message"""
        mt = "{1:F01BANKXXXX0000000000}{2:I103BANKXXXXXXXXXXN}{4:\n"
        
        # Field 20: Transaction Reference
        if 'transaction_reference' in fields:
            mt += f":20:{fields['transaction_reference']}\n"
        
        # Field 23B: Bank Operation Code
        if 'bank_operation_code' in fields:
            mt += f":23B:{fields['bank_operation_code']}\n"
        
        # Field 32A: Value Date, Currency, Amount
        if 'value_date' in fields and 'currency' in fields and 'amount' in fields:
            amount = fields['amount'].replace('.', ',')
            mt += f":32A:{fields['value_date']}{fields['currency']}{amount}\n"
        
        # Field 50K: Ordering Customer
        mt += ":50K:"
        if 'ordering_customer_account' in fields:
            mt += f"/{fields['ordering_customer_account']}\n"
        if 'ordering_customer' in fields:
            mt += fields['ordering_customer']
        mt += "\n"
        
        # Field 52A: Ordering Institution
        if 'ordering_institution' in fields:
            mt += f":52A:{fields['ordering_institution']}\n"
        
        # Field 59: Beneficiary Customer
        mt += ":59:"
        if 'beneficiary_customer_account' in fields:
            mt += f"/{fields['beneficiary_customer_account']}\n"
        if 'beneficiary_customer' in fields:
            mt += fields['beneficiary_customer']
        mt += "\n"
        
        # Field 70: Remittance Information
        if 'remittance_info' in fields:
            mt += f":70:{fields['remittance_info']}\n"
        
        # Field 71A: Details of Charges
        if 'charge_bearer' in fields:
            mt += f":71A:{fields['charge_bearer']}\n"
        
        mt += "-}"
        return mt
    
    def _generate_mt202(self, fields: Dict[str, Any]) -> str:
        """Generate MT202 message"""
        mt = "{1:F01BANKINXX0000000000}{2:I202BANKUSXXAXXXN}{4:\n"
        
        # Field 20: Sender Reference
        if 'sender_reference' in fields:
            mt += f":20:{fields['sender_reference']}\n"
        
        # Field 21: Related Reference
        if 'transaction_reference' in fields:
            mt += f":21:{fields['transaction_reference']}\n"
        
        # Field 32A: Value Date, Currency, Amount
        if 'value_date' in fields and 'currency' in fields and 'amount' in fields:
            amount = fields['amount'].replace('.', ',')
            mt += f":32A:{fields['value_date']}{fields['currency']}{amount}\n"
        
        # Field 52A: Sender's Institution
        if 'senders_institution' in fields:
            mt += f":52A:{fields['senders_institution']}\n"
        
        # Field 53B: Sender's Correspondent
        if 'senders_correspondent' in fields:
            mt += f":53B:{fields['senders_correspondent']}\n"
        
        # Field 58A: Beneficiary Institution
        if 'beneficiary_institution' in fields:
            mt += f":58A:{fields['beneficiary_institution']}\n"
        
        # Field 72: Sender to Receiver Information
        if 'sender_to_receiver_info' in fields:
            mt += f":72:{fields['sender_to_receiver_info']}\n"
        
        mt += "-}"
        return mt
