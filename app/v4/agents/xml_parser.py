"""
XML Parser Agent
Parses ISO 20022 XML messages into structured data
"""

import re
import logging
from datetime import datetime
from typing import Dict, Any
from xml.etree import ElementTree as ET

from models import ParsedMTMessage, AgentResult, AgentStatus

logger = logging.getLogger(__name__)


class XMLParserAgent:
    """
    Agent responsible for parsing ISO 20022 XML messages
    Supports pain.001, pacs.008, and pacs.009 formats
    """
    
    def __init__(self):
        self.name = "XML Parser Agent"
        logger.info(f"🤖 {self.name} initialized")
    
    def parse(self, xml_message: str, message_id: str = None) -> tuple[ParsedMTMessage, AgentResult]:
        """
        Parse XML message and return structured data with agent result
        """
        start_time = datetime.utcnow()
        
        try:
            # Detect message type from XML
            msg_type = self._detect_message_type(xml_message)
            
            if msg_type == 'pain.001':
                parsed = self._parse_pain001(xml_message, message_id)
            elif msg_type == 'pacs.008':
                parsed = self._parse_pacs008(xml_message, message_id)
            elif msg_type == 'pacs.009':
                parsed = self._parse_pacs009(xml_message, message_id)
            else:
                raise ValueError(f"Unsupported message type: {msg_type}")
            
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
    
    def _detect_message_type(self, xml_message: str) -> str:
        """Detect XML message type from content"""
        if 'CstmrCdtTrfInitn' in xml_message:
            return 'pain.001'
        elif 'FIToFICstmrCdtTrf' in xml_message:
            # Could be pacs.008 or pacs.009 - need more specific detection
            if 'IntrBkSttlmAmt' in xml_message:
                return 'pacs.008'
            else:
                return 'pacs.009'
        else:
            raise ValueError("Unknown XML message type")
    
    def _parse_pain001(self, xml_str: str, msg_id: str) -> ParsedMTMessage:
        """Parse pain.001 - Customer Payment Initiation"""
        fields = {}
        
        try:
            root = ET.fromstring(xml_str)
            ns = {'ns': 'urn:iso:std:iso:20022:tech:xsd:pain.001.002.03'}
            
            # Try without namespace first
            if root.tag.endswith('Document'):
                ns = {}
            
            # Extract fields
            msg_id_elem = self._find_elem(root, './/MsgId', ns)
            if msg_id_elem is not None:
                fields['sender_reference'] = msg_id_elem.text
            
            exec_date_elem = self._find_elem(root, './/ReqdExctnDt', ns)
            if exec_date_elem is not None:
                # Convert ISO date to YYMMDD format
                date_str = exec_date_elem.text  # e.g., 2026-06-05
                if date_str:
                    fields['execution_date'] = date_str.replace('-', '')[2:]  # YYMMDD
            
            # Debtor (Ordering Customer)
            dbtr_nm = self._find_elem(root, './/PmtInf/Dbtr/Nm', ns)
            if dbtr_nm is not None:
                fields['ordering_customer'] = dbtr_nm.text
            
            dbtr_acct = self._find_elem(root, './/PmtInf/DbtrAcct/Id/IBAN', ns)
            if dbtr_acct is not None:
                fields['ordering_customer_account'] = dbtr_acct.text
            
            dbtr_adr = self._find_elem(root, './/PmtInf/Dbtr/PstlAdr/AdrLine', ns)
            if dbtr_adr is not None:
                fields['ordering_customer_address'] = dbtr_adr.text
            
            # Ordering Institution
            dbtr_agt = self._find_elem(root, './/PmtInf/DbtrAgt/FinInstnId/BICFI', ns)
            if dbtr_agt is not None:
                fields['ordering_institution'] = dbtr_agt.text
            
            # Creditor (Beneficiary Customer)
            cdtr_nm = self._find_elem(root, './/CdtTrfTxInf/Cdtr/Nm', ns)
            if cdtr_nm is not None:
                fields['beneficiary_customer'] = cdtr_nm.text
            
            cdtr_acct = self._find_elem(root, './/CdtTrfTxInf/CdtrAcct/Id/IBAN', ns)
            if cdtr_acct is not None:
                fields['beneficiary_customer_account'] = cdtr_acct.text
            
            cdtr_adr = self._find_elem(root, './/CdtTrfTxInf/Cdtr/PstlAdr/AdrLine', ns)
            if cdtr_adr is not None:
                fields['beneficiary_customer_address'] = cdtr_adr.text
            
            # Amount and Currency
            ccy = self._find_elem(root, './/Amt/InstdAmt', ns)
            if ccy is not None:
                fields['currency'] = ccy.get('Ccy', '')
                if ccy.text:
                    fields['amount'] = ccy.text
            
            # Transaction Reference
            e2e_id = self._find_elem(root, './/PmtId/EndToEndId', ns)
            if e2e_id is not None:
                fields['transaction_reference'] = e2e_id.text
            
            # Charge Bearer
            chg_br = self._find_elem(root, './/ChrgBr', ns)
            if chg_br is not None:
                # Map from ISO to SWIFT: SHAR->SHA, DEBT->OUR, CRED->BEN
                charge_map = {'SHAR': 'SHA', 'DEBT': 'OUR', 'CRED': 'BEN'}
                fields['charge_bearer'] = charge_map.get(chg_br.text, chg_br.text)
            
            # Remittance Information
            remit = self._find_elem(root, './/RmtInf/Ustrd', ns)
            if remit is not None:
                fields['remittance_info'] = remit.text
            
        except Exception as e:
            logger.error(f"Error parsing pain.001: {e}")
            raise
        
        return ParsedMTMessage(
            message_id=msg_id or f"PAIN001-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            message_type='pain.001',
            mx_equivalent='MT101',
            fields=fields,
            field_count=len(fields),
            raw=xml_str
        )
    
    def _parse_pacs008(self, xml_str: str, msg_id: str) -> ParsedMTMessage:
        """Parse pacs.008 - Customer Credit Transfer"""
        # For now, treat similar to pain.001 extraction
        # This would map back to MT103
        fields = {}
        
        try:
            root = ET.fromstring(xml_str)
            ns = {}
            
            # Extract fields similar to pain.001
            msg_id_elem = self._find_elem(root, './/MsgId', ns)
            if msg_id_elem is not None:
                fields['transaction_reference'] = msg_id_elem.text
            
            # Debtor
            dbtr_nm = self._find_elem(root, './/Dbtr/Nm', ns)
            if dbtr_nm is not None:
                fields['ordering_customer'] = dbtr_nm.text
            
            dbtr_acct = self._find_elem(root, './/DbtrAcct/Id/Othr/Id', ns)
            if dbtr_acct is not None:
                fields['ordering_customer_account'] = dbtr_acct.text
            
            # Creditor
            cdtr_nm = self._find_elem(root, './/Cdtr/Nm', ns)
            if cdtr_nm is not None:
                fields['beneficiary_customer'] = cdtr_nm.text
            
            cdtr_acct = self._find_elem(root, './/CdtrAcct/Id/Othr/Id', ns)
            if cdtr_acct is not None:
                fields['beneficiary_customer_account'] = cdtr_acct.text
            
            # Amount
            amt = self._find_elem(root, './/IntrBkSttlmAmt', ns)
            if amt is not None:
                fields['currency'] = amt.get('Ccy', '')
                if amt.text:
                    fields['amount'] = amt.text
            
            # Value Date
            dt = self._find_elem(root, './/IntrBkSttlmDt', ns)
            if dt is not None:
                date_str = dt.text
                if date_str:
                    fields['value_date'] = date_str.replace('-', '')[2:]
            
        except Exception as e:
            logger.error(f"Error parsing pacs.008: {e}")
            raise
        
        return ParsedMTMessage(
            message_id=msg_id or f"PACS008-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            message_type='pacs.008',
            mx_equivalent='MT103',
            fields=fields,
            field_count=len(fields),
            raw=xml_str
        )
    
    def _parse_pacs009(self, xml_str: str, msg_id: str) -> ParsedMTMessage:
        """Parse pacs.009 - Financial Institution Transfer"""
        fields = {}
        
        try:
            root = ET.fromstring(xml_str)
            ns = {}
            
            # Message ID
            msg_id_elem = self._find_elem(root, './/MsgId', ns)
            if msg_id_elem is not None:
                fields['sender_reference'] = msg_id_elem.text
            
            # End-to-End ID / Transaction Reference
            e2e = self._find_elem(root, './/EndToEndId', ns)
            if e2e is not None:
                fields['transaction_reference'] = e2e.text
            
            # Value Date
            dt = self._find_elem(root, './/IntrBkSttlmDt', ns)
            if dt is not None:
                date_str = dt.text
                if date_str:
                    fields['value_date'] = date_str.replace('-', '')[2:]
            
            # Amount
            amt = self._find_elem(root, './/IntrBkSttlmAmt', ns)
            if amt is not None:
                fields['currency'] = amt.get('Ccy', '')
                if amt.text:
                    fields['amount'] = amt.text
            
            # Instructing Agent (Sender)
            inst_agt = self._find_elem(root, './/InstgAgt/FinInstnId/BICFI', ns)
            if inst_agt is not None:
                fields['senders_institution'] = inst_agt.text
            
            # Instructed Agent (Beneficiary)
            instd_agt = self._find_elem(root, './/InstdAgt/FinInstnId/BICFI', ns)
            if instd_agt is not None:
                fields['beneficiary_institution'] = instd_agt.text
            
            # Intermediary Agent
            int_agt = self._find_elem(root, './/IntrmyAgt1/FinInstnId/BICFI', ns)
            if int_agt is not None:
                fields['senders_correspondent'] = int_agt.text
            
        except Exception as e:
            logger.error(f"Error parsing pacs.009: {e}")
            raise
        
        return ParsedMTMessage(
            message_id=msg_id or f"PACS009-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            message_type='pacs.009',
            mx_equivalent='MT202',
            fields=fields,
            field_count=len(fields),
            raw=xml_str
        )
    
    def _find_elem(self, root: ET.Element, path: str, ns: Dict) -> Any:
        """Find element using XPath, handling namespaces"""
        try:
            # Try with namespace first
            if ns:
                result = root.find(path, ns)
                if result is not None:
                    return result
            
            # Try without namespace
            return root.find(path)
        except:
            return None
