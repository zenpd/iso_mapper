"""
MT Parser Agent
Parses SWIFT MT format messages into structured data
"""

import re
import logging
from datetime import datetime
from typing import Dict, Any

from models import ParsedMTMessage, AgentResult, AgentStatus

logger = logging.getLogger(__name__)


class MTParserAgent:
    """
    Agent responsible for parsing SWIFT MT messages
    Supports MT103, MT202, and generic MT formats
    """
    
    def __init__(self):
        self.name = "MT Parser Agent"
        logger.info(f"🤖 {self.name} initialized")
    
    def parse(self, raw_message: str, message_id: str = None) -> tuple[ParsedMTMessage, AgentResult]:
        """
        Parse MT message and return structured data with agent result
        """
        start_time = datetime.utcnow()
        
        try:
            message_type = self._detect_message_type(raw_message)
            
            if message_type == 'MT103':
                parsed = self._parse_mt103(raw_message, message_id)
            elif message_type == 'MT202':
                parsed = self._parse_mt202(raw_message, message_id)
            else:
                parsed = self._parse_generic(raw_message, message_type, message_id)
            
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETE,
                message=f"Parsed {parsed.field_count} fields from {parsed.message_type}",
                fields_processed=parsed.field_count,
                duration_ms=duration,
                details={
                    "message_type": parsed.message_type,
                    "mx_equivalent": parsed.mx_equivalent,
                    "fields_found": list(parsed.fields.keys())
                }
            )
            
            logger.info(f"✅ {self.name}: Parsed {parsed.field_count} fields")
            return parsed, result
            
        except Exception as e:
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            logger.error(f"❌ {self.name} error: {e}")
            
            result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.ERROR,
                message=f"Parse error: {str(e)}",
                duration_ms=duration
            )
            raise
    
    def _detect_message_type(self, raw_message: str) -> str:
        """Detect MT message type from content"""
        if ':20:' in raw_message and ':32A:' in raw_message:
            if ':50K:' in raw_message or ':50A:' in raw_message:
                return 'MT103'
            elif ':53B:' in raw_message or ':58A:' in raw_message:
                return 'MT202'
        return 'MTXXX'
    
    def _parse_mt103(self, raw_message: str, msg_id: str) -> ParsedMTMessage:
        """Parse MT103 - Customer Credit Transfer"""
        fields = {}
        
        # Field 20: Transaction Reference
        match = re.search(r':20:([^\n:]+)', raw_message)
        if match:
            fields['transaction_reference'] = match.group(1).strip()
        
        # Field 23B: Bank Operation Code
        match = re.search(r':23B:([^\n:]+)', raw_message)
        if match:
            fields['bank_operation_code'] = match.group(1).strip()
        
        # Field 32A: Value Date, Currency, Amount
        match = re.search(r':32A:(\d{6})([A-Z]{3})([\d,\.]+)', raw_message)
        if match:
            fields['value_date'] = match.group(1)
            fields['currency'] = match.group(2)
            fields['amount'] = match.group(3).replace(',', '.')
        
        # Field 50K/50A: Ordering Customer
        match = re.search(r':50[KA]:(.*?)(?=:\d{2}[A-Z]?:|\Z)', raw_message, re.DOTALL)
        if match:
            fields['ordering_customer'] = match.group(1).strip()
        
        # Field 52A: Ordering Institution
        match = re.search(r':52A:([^\n:]+)', raw_message)
        if match:
            fields['ordering_institution'] = match.group(1).strip()
        
        # Field 53B: Sender's Correspondent
        match = re.search(r':53B:(.*?)(?=:\d{2}[A-Z]?:|\Z)', raw_message, re.DOTALL)
        if match:
            fields['senders_correspondent'] = match.group(1).strip()
        
        # Field 59/59A: Beneficiary Customer
        match = re.search(r':59[A]?:(.*?)(?=:\d{2}[A-Z]?:|\Z)', raw_message, re.DOTALL)
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
        
        # Field 72: Sender to Receiver Information
        match = re.search(r':72:(.*?)(?=:\d{2}[A-Z]?:|\Z)', raw_message, re.DOTALL)
        if match:
            fields['sender_to_receiver_info'] = match.group(1).strip()
        
        return ParsedMTMessage(
            message_id=msg_id or f"MT103-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            message_type='MT103',
            mx_equivalent='pacs.008',
            fields=fields,
            field_count=len(fields),
            raw=raw_message
        )
    
    def _parse_mt202(self, raw_message: str, msg_id: str) -> ParsedMTMessage:
        """Parse MT202 - Financial Institution Transfer"""
        fields = {}
        
        match = re.search(r':20:([^\n:]+)', raw_message)
        if match:
            fields['transaction_reference'] = match.group(1).strip()
        
        match = re.search(r':32A:(\d{6})([A-Z]{3})([\d,\.]+)', raw_message)
        if match:
            fields['value_date'] = match.group(1)
            fields['currency'] = match.group(2)
            fields['amount'] = match.group(3).replace(',', '.')
        
        match = re.search(r':53B:(.*?)(?=:\d{2}[A-Z]?:|\Z)', raw_message, re.DOTALL)
        if match:
            fields['senders_correspondent'] = match.group(1).strip()
        
        match = re.search(r':58A:(.*?)(?=:\d{2}[A-Z]?:|\Z)', raw_message, re.DOTALL)
        if match:
            fields['beneficiary_institution'] = match.group(1).strip()
        
        return ParsedMTMessage(
            message_id=msg_id or f"MT202-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            message_type='MT202',
            mx_equivalent='pacs.009',
            fields=fields,
            field_count=len(fields),
            raw=raw_message
        )
    
    def _parse_generic(self, raw_message: str, msg_type: str, msg_id: str) -> ParsedMTMessage:
        """Generic parser for unsupported MT types"""
        fields = {'raw_content': raw_message}
        
        # Try to extract basic fields
        match = re.search(r':20:([^\n:]+)', raw_message)
        if match:
            fields['transaction_reference'] = match.group(1).strip()
        
        return ParsedMTMessage(
            message_id=msg_id or f"{msg_type}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            message_type=msg_type,
            mx_equivalent='pacs.XXX',
            fields=fields,
            field_count=len(fields),
            raw=raw_message
        )
