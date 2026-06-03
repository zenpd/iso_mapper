"""
MT Message Parser
Parses legacy SWIFT MT messages
"""

import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class MTParser:
    """Parse SWIFT MT format messages"""
    
    def parse(self, mt_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse MT message and extract fields
        """
        raw_message = mt_message.get('raw_message', '')
        message_type = self._detect_message_type(raw_message)
        
        if message_type == 'MT103':
            return self._parse_mt103(raw_message, mt_message.get('message_id'))
        elif message_type == 'MT202':
            return self._parse_mt202(raw_message, mt_message.get('message_id'))
        else:
            return self._parse_generic(raw_message, message_type, mt_message.get('message_id'))
    
    def _detect_message_type(self, raw_message: str) -> str:
        """Detect MT message type from content"""
        if ':20:' in raw_message and ':32A:' in raw_message and ':50K:' in raw_message:
            return 'MT103'
        elif ':20:' in raw_message and ':32A:' in raw_message and ':53B:' in raw_message:
            return 'MT202'
        return 'MTXXX'
    
    def _parse_mt103(self, raw_message: str, msg_id: str) -> Dict[str, Any]:
        """Parse MT103 - Customer Credit Transfer"""
        fields = {}
        
        # Field 20: Transaction Reference
        match = re.search(r':20:([^\n:]+)', raw_message)
        if match:
            fields['transaction_reference'] = match.group(1).strip()
        
        # Field 32A: Value Date, Currency, Amount
        match = re.search(r':32A:(\d{6})([A-Z]{3})([\d,\.]+)', raw_message)
        if match:
            fields['value_date'] = match.group(1)
            fields['currency'] = match.group(2)
            fields['amount'] = match.group(3).replace(',', '')
        
        # Field 50K: Ordering Customer
        match = re.search(r':50K:(.*?)(?=:\d{2}[A-Z]?:|\Z)', raw_message, re.DOTALL)
        if match:
            fields['ordering_customer'] = match.group(1).strip()
        
        # Field 59: Beneficiary Customer
        match = re.search(r':59:(.*?)(?=:\d{2}[A-Z]?:|\Z)', raw_message, re.DOTALL)
        if match:
            fields['beneficiary_customer'] = match.group(1).strip()
        
        # Field 70: Remittance Information
        match = re.search(r':70:(.*?)(?=:\d{2}[A-Z]?:|\Z)', raw_message, re.DOTALL)
        if match:
            fields['remittance_info'] = match.group(1).strip()
        
        # Field 71A: Details of Charges
        match = re.search(r':71A:([A-Z]{3})', raw_message)
        if match:
            fields['charge_bearer'] = match.group(1)
        
        return {
            'message_id': msg_id,
            'message_type': 'MT103',
            'mx_equivalent': 'pacs.008',
            'fields': fields,
            'raw': raw_message
        }
    
    def _parse_mt202(self, raw_message: str, msg_id: str) -> Dict[str, Any]:
        """Parse MT202 - Financial Institution Transfer"""
        fields = {}
        
        # Field 20: Transaction Reference
        match = re.search(r':20:([^\n:]+)', raw_message)
        if match:
            fields['transaction_reference'] = match.group(1).strip()
        
        # Field 32A: Value Date, Currency, Amount
        match = re.search(r':32A:(\d{6})([A-Z]{3})([\d,\.]+)', raw_message)
        if match:
            fields['value_date'] = match.group(1)
            fields['currency'] = match.group(2)
            fields['amount'] = match.group(3).replace(',', '')
        
        # Field 53B: Sender's Correspondent
        match = re.search(r':53B:(.*?)(?=:\d{2}[A-Z]?:|\Z)', raw_message, re.DOTALL)
        if match:
            fields['senders_correspondent'] = match.group(1).strip()
        
        # Field 58A: Beneficiary Institution
        match = re.search(r':58A:(.*?)(?=:\d{2}[A-Z]?:|\Z)', raw_message, re.DOTALL)
        if match:
            fields['beneficiary_institution'] = match.group(1).strip()
        
        return {
            'message_id': msg_id,
            'message_type': 'MT202',
            'mx_equivalent': 'pacs.009',
            'fields': fields,
            'raw': raw_message
        }
    
    def _parse_generic(self, raw_message: str, msg_type: str, msg_id: str) -> Dict[str, Any]:
        """Generic parser for other MT types"""
        return {
            'message_id': msg_id,
            'message_type': msg_type,
            'fields': {'raw': raw_message},
            'raw': raw_message
        }
