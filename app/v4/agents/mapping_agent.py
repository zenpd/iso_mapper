"""
Mapping Agent
AI-powered semantic field mapping from MT to MX
Supports rule-based, LLM-based, and hybrid approaches
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any

from models import (
    ParsedMTMessage, MappingResult, MappedField, 
    AgentResult, AgentStatus, TransformationApproach
)
from services.llm_service import llm_service

logger = logging.getLogger(__name__)


class MappingAgent:
    """
    Agent responsible for mapping MT fields to MX paths
    Uses configurable approach: rules, LLM, or hybrid
    """
    
    def __init__(self):
        self.name = "Mapping Agent"
        self.confidence_threshold = 0.85
        self._load_mapping_rules()
        logger.info(f"🤖 {self.name} initialized")
    
    def _load_mapping_rules(self):
        """Load rule-based mappings for all supported MT/MX combinations"""
        # MT103 → pacs.008 mappings
        self.mt103_mappings = {
            'transaction_reference': {
                'mx_path': 'CdtTrfTxInf.PmtId.InstrId',
                'confidence': 0.98,
                'reasoning': 'Direct mapping - transaction identifier'
            },
            'bank_operation_code': {
                'mx_path': 'CdtTrfTxInf.PmtTpInf.SvcLvl.Cd',
                'confidence': 0.95,
                'reasoning': 'Bank operation code to service level'
            },
            'value_date': {
                'mx_path': 'CdtTrfTxInf.IntrBkSttlmDt',
                'confidence': 0.99,
                'reasoning': 'Value date maps to interbank settlement date'
            },
            'currency': {
                'mx_path': 'CdtTrfTxInf.IntrBkSttlmAmt.Ccy',
                'confidence': 1.0,
                'reasoning': 'Currency code - exact match'
            },
            'amount': {
                'mx_path': 'CdtTrfTxInf.IntrBkSttlmAmt.Value',
                'confidence': 1.0,
                'reasoning': 'Amount value - exact match'
            },
            'ordering_customer': {
                'mx_path': 'CdtTrfTxInf.Dbtr.Nm',
                'confidence': 0.97,
                'reasoning': 'Ordering customer name is debtor name in ISO 20022'
            },
            'ordering_customer_account': {
                'mx_path': 'CdtTrfTxInf.DbtrAcct.Id.Othr.Id',
                'confidence': 0.97,
                'reasoning': 'Ordering customer account to debtor account'
            },
            'ordering_institution': {
                'mx_path': 'CdtTrfTxInf.DbtrAgt.FinInstnId.BICFI',
                'confidence': 0.98,
                'reasoning': 'Ordering institution BIC to debtor agent'
            },
            'senders_correspondent': {
                'mx_path': 'CdtTrfTxInf.IntrmyAgt1.FinInstnId.BICFI',
                'confidence': 0.92,
                'reasoning': 'Sender correspondent to intermediary agent'
            },
            'beneficiary_customer': {
                'mx_path': 'CdtTrfTxInf.Cdtr.Nm',
                'confidence': 0.97,
                'reasoning': 'Beneficiary customer name is creditor name in ISO 20022'
            },
            'beneficiary_customer_account': {
                'mx_path': 'CdtTrfTxInf.CdtrAcct.Id.Othr.Id',
                'confidence': 0.97,
                'reasoning': 'Beneficiary customer account to creditor account'
            },
            'remittance_info': {
                'mx_path': 'CdtTrfTxInf.RmtInf.Ustrd',
                'confidence': 0.95,
                'reasoning': 'Remittance info to unstructured remittance'
            },
            'charge_bearer': {
                'mx_path': 'CdtTrfTxInf.ChrgBr',
                'confidence': 1.0,
                'reasoning': 'Charge bearer - direct mapping (SHA/BEN/OUR)'
            },
            'sender_to_receiver_info': {
                'mx_path': 'CdtTrfTxInf.InstrForNxtAgt.InstrInf',
                'confidence': 0.90,
                'reasoning': 'Sender to receiver maps to instruction for next agent'
            }
        }
        
        # MT101 → pain.001 mappings
        self.mt101_mappings = {
            'sender_reference': {
                'mx_path': 'GrpHdr.MsgId',
                'confidence': 0.98,
                'reasoning': 'Sender reference maps to message ID in payment initiation'
            },
            'message_index': {
                'mx_path': 'PmtInf.PmtInfId',
                'confidence': 0.90,
                'reasoning': 'Message index maps to payment info ID'
            },
            'execution_date': {
                'mx_path': 'PmtInf.ReqdExctnDt',
                'confidence': 0.99,
                'reasoning': 'Execution date maps to required execution date'
            },
            'transaction_reference': {
                'mx_path': 'CdtTrfTxInf.PmtId.EndToEndId',
                'confidence': 0.98,
                'reasoning': 'Transaction reference maps to end-to-end ID'
            },
            'currency': {
                'mx_path': 'CdtTrfTxInf.Amt.InstdAmt.Ccy',
                'confidence': 1.0,
                'reasoning': 'Currency code - exact match'
            },
            'amount': {
                'mx_path': 'CdtTrfTxInf.Amt.InstdAmt.Value',
                'confidence': 1.0,
                'reasoning': 'Amount value - exact match'
            },
            'ordering_customer': {
                'mx_path': 'PmtInf.Dbtr.Nm',
                'confidence': 0.98,
                'reasoning': 'Ordering customer name maps to debtor name'
            },
            'ordering_customer_account': {
                'mx_path': 'PmtInf.DbtrAcct.Id.IBAN',
                'confidence': 0.97,
                'reasoning': 'Ordering customer account maps to debtor account IBAN'
            },
            'ordering_customer_address': {
                'mx_path': 'PmtInf.Dbtr.PstlAdr.AdrLine',
                'confidence': 0.90,
                'reasoning': 'Ordering customer address maps to postal address'
            },
            'ordering_institution': {
                'mx_path': 'PmtInf.DbtrAgt.FinInstnId.BICFI',
                'confidence': 0.98,
                'reasoning': 'Ordering institution BIC maps to debtor agent'
            },
            'beneficiary_customer': {
                'mx_path': 'CdtTrfTxInf.Cdtr.Nm',
                'confidence': 0.98,
                'reasoning': 'Beneficiary customer name maps to creditor name'
            },
            'beneficiary_customer_account': {
                'mx_path': 'CdtTrfTxInf.CdtrAcct.Id.IBAN',
                'confidence': 0.97,
                'reasoning': 'Beneficiary customer account maps to creditor account IBAN'
            },
            'beneficiary_customer_address': {
                'mx_path': 'CdtTrfTxInf.Cdtr.PstlAdr.AdrLine',
                'confidence': 0.90,
                'reasoning': 'Beneficiary customer address maps to postal address'
            },
            'charge_bearer': {
                'mx_path': 'CdtTrfTxInf.ChrgBr',
                'confidence': 1.0,
                'reasoning': 'Charge bearer - direct mapping (SHAR/DEBT/CRED)'
            },
            'remittance_info': {
                'mx_path': 'CdtTrfTxInf.RmtInf.Ustrd',
                'confidence': 0.95,
                'reasoning': 'Remittance information maps to unstructured remittance'
            }
        }
        
        # MT202 → pacs.009 mappings
        self.mt202_mappings = {
            'sender_reference': {
                'mx_path': 'GrpHdr.MsgId',
                'confidence': 0.98,
                'reasoning': 'Sender reference maps to message ID'
            },
            'transaction_reference': {
                'mx_path': 'CdtTrfTxInf.PmtId.EndToEndId',
                'confidence': 0.98,
                'reasoning': 'Related reference maps to end-to-end ID'
            },
            'value_date': {
                'mx_path': 'CdtTrfTxInf.IntrBkSttlmDt',
                'confidence': 0.99,
                'reasoning': 'Value date maps to interbank settlement date'
            },
            'currency': {
                'mx_path': 'CdtTrfTxInf.IntrBkSttlmAmt.Ccy',
                'confidence': 1.0,
                'reasoning': 'Currency code - exact match'
            },
            'amount': {
                'mx_path': 'CdtTrfTxInf.IntrBkSttlmAmt.Value',
                'confidence': 1.0,
                'reasoning': 'Amount value - exact match'
            },
            'senders_institution': {
                'mx_path': 'CdtTrfTxInf.InstgAgt.FinInstnId.BICFI',
                'confidence': 0.98,
                'reasoning': 'Senders institution BIC maps to instructing agent'
            },
            'beneficiary_institution': {
                'mx_path': 'CdtTrfTxInf.InstdAgt.FinInstnId.BICFI',
                'confidence': 0.98,
                'reasoning': 'Beneficiary institution BIC maps to instructed agent'
            },
            'senders_correspondent': {
                'mx_path': 'CdtTrfTxInf.IntrmyAgt1.FinInstnId.BICFI',
                'confidence': 0.92,
                'reasoning': 'Senders correspondent maps to intermediary agent'
            },
            'sender_to_receiver_info': {
                'mx_path': 'CdtTrfTxInf.InstrForNxtAgt.InstrInf',
                'confidence': 0.90,
                'reasoning': 'Sender to receiver info maps to instruction for next agent'
            }
        }
        
        # Default to MT103 (will be overridden by message type)
        self.rule_mappings = self.mt103_mappings
    
    async def map_fields(
        self,
        parsed_mt: ParsedMTMessage,
        approach: TransformationApproach
    ) -> tuple[MappingResult, AgentResult]:
        """
        Map MT fields to MX paths using specified approach
        """
        start_time = datetime.utcnow()
        
        try:
            # Select mapping rules based on message type
            if parsed_mt.message_type == 'MT101':
                self.rule_mappings = self.mt101_mappings
            elif parsed_mt.message_type == 'MT202':
                self.rule_mappings = self.mt202_mappings
            else:  # Default to MT103
                self.rule_mappings = self.mt103_mappings
            
            mapped_fields: Dict[str, MappedField] = {}
            low_confidence_fields = []
            
            for field_name, value in parsed_mt.fields.items():
                if approach == TransformationApproach.RULES:
                    mapping = await self._map_with_rules(field_name, value, parsed_mt)
                elif approach == TransformationApproach.LLM:
                    mapping = await self._map_with_llm(field_name, value, parsed_mt)
                else:  # HYBRID
                    mapping = await self._map_hybrid(field_name, value, parsed_mt)
                
                mapped_fields[mapping.mx_path] = mapping
                
                if mapping.confidence < self.confidence_threshold:
                    low_confidence_fields.append(field_name)
            
            # Calculate overall confidence
            confidences = [f.confidence for f in mapped_fields.values()]
            overall_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            result = MappingResult(
                mapped_fields=mapped_fields,
                fields_mapped=len(mapped_fields),
                overall_confidence=overall_confidence,
                low_confidence_fields=low_confidence_fields,
                approach_used=approach
            )
            
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            agent_result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETE,
                message=f"Mapped {len(mapped_fields)} fields using {approach.value} approach",
                confidence=overall_confidence,
                fields_processed=len(mapped_fields),
                duration_ms=duration,
                details={
                    "approach": approach.value,
                    "low_confidence_count": len(low_confidence_fields),
                    "low_confidence_fields": low_confidence_fields
                }
            )
            
            logger.info(f"✅ {self.name}: Mapped {len(mapped_fields)} fields ({approach.value})")
            return result, agent_result
            
        except Exception as e:
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            logger.error(f"❌ {self.name} error: {e}")
            
            agent_result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.ERROR,
                message=f"Mapping error: {str(e)}",
                duration_ms=duration
            )
            raise
    
    async def _map_with_rules(
        self,
        field_name: str,
        value: Any,
        parsed_mt: ParsedMTMessage
    ) -> MappedField:
        """Map field using rule-based approach"""
        if field_name in self.rule_mappings:
            rule = self.rule_mappings[field_name]
            return MappedField(
                value=value,
                confidence=rule['confidence'],
                reasoning=rule['reasoning'],
                source_field=field_name,
                method="rule",
                mx_path=rule['mx_path']
            )
        else:
            # Fallback for unknown fields
            return MappedField(
                value=value,
                confidence=0.60,
                reasoning="No rule found - defaulting to unstructured remittance",
                source_field=field_name,
                method="rule",
                mx_path="CdtTrfTxInf.RmtInf.Ustrd"
            )
    
    async def _map_with_llm(
        self,
        field_name: str,
        value: Any,
        parsed_mt: ParsedMTMessage
    ) -> MappedField:
        """Map field using LLM semantic analysis"""
        if not llm_service.is_available:
            logger.warning("LLM not available, falling back to rules")
            return await self._map_with_rules(field_name, value, parsed_mt)
        
        try:
            context = {
                "message_type": parsed_mt.message_type,
                "mx_type": parsed_mt.mx_equivalent
            }
            
            result = await llm_service.analyze_field_mapping(field_name, value, context)
            
            return MappedField(
                value=value,
                confidence=result.get('confidence', 0.85),
                reasoning=result.get('reasoning', 'LLM inference'),
                source_field=field_name,
                method="llm",
                mx_path=result.get('mx_path', 'CdtTrfTxInf.RmtInf.Ustrd')
            )
        except Exception as e:
            logger.error(f"LLM mapping failed: {e}")
            return await self._map_with_rules(field_name, value, parsed_mt)
    
    async def _map_hybrid(
        self,
        field_name: str,
        value: Any,
        parsed_mt: ParsedMTMessage
    ) -> MappedField:
        """Map field using hybrid approach - rules first, LLM for unknowns"""
        # Try rules first
        if field_name in self.rule_mappings:
            return await self._map_with_rules(field_name, value, parsed_mt)
        
        # Fall back to LLM for unknown fields
        if llm_service.is_available:
            return await self._map_with_llm(field_name, value, parsed_mt)
        
        # Final fallback
        return MappedField(
            value=value,
            confidence=0.55,
            reasoning="Unknown field - hybrid fallback to unstructured",
            source_field=field_name,
            method="inferred",
            mx_path="CdtTrfTxInf.RmtInf.Ustrd"
        )
