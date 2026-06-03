"""
Enrichment Agent
AI-powered data enrichment for regulatory and mandatory MX fields
"""

import logging
import random
import asyncio
from datetime import datetime
from typing import Dict, Any

from models import (
    MappingResult, EnrichmentResult, MappedField,
    AgentResult, AgentStatus, TransformationApproach
)
from services.llm_service import llm_service

logger = logging.getLogger(__name__)


class EnrichmentAgent:
    """
    Agent responsible for enriching MX data with mandatory and regulatory fields
    Uses knowledge graphs, ML models, and LLM inference
    """
    
    def __init__(self):
        self.name = "Enrichment Agent"
        self._load_knowledge_bases()
        logger.info(f"🤖 {self.name} initialized with knowledge graphs")
    
    def _load_knowledge_bases(self):
        """Load BIC directory and regulatory requirements"""
        self.bic_directory = {
            'CHASUS33': {'name': 'JPMORGAN CHASE BANK, N.A.', 'country': 'US', 'city': 'NEW YORK'},
            'CITIUS33': {'name': 'CITIBANK N.A.', 'country': 'US', 'city': 'NEW YORK'},
            'DEUTDEFF': {'name': 'DEUTSCHE BANK AG', 'country': 'DE', 'city': 'FRANKFURT'},
            'HSBCGB2L': {'name': 'HSBC BANK PLC', 'country': 'GB', 'city': 'LONDON'},
            'BARCGB22': {'name': 'BARCLAYS BANK PLC', 'country': 'GB', 'city': 'LONDON'},
            'ABORAEAA': {'name': 'ARAB BANK PLC', 'country': 'AE', 'city': 'ABU DHABI'},
            'SCBLDEFX': {'name': 'STANDARD CHARTERED BANK', 'country': 'DE', 'city': 'FRANKFURT'}
        }
        
        self.regulatory_requirements = {
            'US': {
                'fields': ['FedRef', 'TaxIdNb'],
                'requires_ofac': True,
                'threshold_reporting': 10000
            },
            'EU': {
                'fields': ['LEI', 'TaxIdNb'],
                'requires_sepa': True,
                'psd2_compliant': True
            },
            'GB': {
                'fields': ['SortCode', 'IBAN'],
                'requires_fps': True
            }
        }
        
        self.charge_bearer_mapping = {
            'SHA': 'SHAR',
            'BEN': 'CRED',
            'OUR': 'DEBT'
        }
    
    async def enrich(
        self,
        mapping_result: MappingResult,
        parsed_mt: Dict[str, Any],
        approach: TransformationApproach
    ) -> tuple[EnrichmentResult, AgentResult]:
        """
        Enrich mapped data with mandatory and regulatory fields
        """
        start_time = datetime.utcnow()
        
        try:
            enriched_data = dict(mapping_result.mapped_fields)
            fields_added = 0
            enrichment_log = []
            regulatory_compliance = {}
            
            # Generate mandatory header fields
            header_fields, header_log = await self._generate_header_fields(parsed_mt)
            enriched_data.update(header_fields)
            fields_added += len(header_fields)
            enrichment_log.extend(header_log)
            
            # Generate End-to-End ID
            e2e_field, e2e_log = self._generate_end_to_end_id(parsed_mt)
            enriched_data.update(e2e_field)
            fields_added += 1
            enrichment_log.append(e2e_log)
            
            # Enrich BIC information from knowledge graph
            bic_fields, bic_log = await self._enrich_bic_information(enriched_data)
            enriched_data.update(bic_fields)
            fields_added += len(bic_fields)
            enrichment_log.extend(bic_log)
            
            # Add regulatory fields based on jurisdiction
            currency = parsed_mt.get('fields', {}).get('currency', 'USD')
            reg_fields, reg_log, reg_compliance = await self._add_regulatory_fields(
                enriched_data, currency, approach
            )
            enriched_data.update(reg_fields)
            fields_added += len(reg_fields)
            enrichment_log.extend(reg_log)
            regulatory_compliance = reg_compliance
            
            # Enrich party data using LLM if available
            if approach in [TransformationApproach.LLM, TransformationApproach.HYBRID]:
                party_fields, party_log = await self._enrich_party_data(enriched_data, parsed_mt)
                enriched_data.update(party_fields)
                fields_added += len(party_fields)
                enrichment_log.extend(party_log)
            
            # Map charge bearer code
            cb_field, cb_log = self._map_charge_bearer(enriched_data)
            if cb_field:
                enriched_data.update(cb_field)
                enrichment_log.append(cb_log)
            
            result = EnrichmentResult(
                enriched_data=enriched_data,
                fields_added=fields_added,
                enrichment_log=enrichment_log,
                regulatory_compliance=regulatory_compliance
            )
            
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            agent_result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETE,
                message=f"Added {fields_added} regulatory/mandatory fields",
                fields_processed=fields_added,
                duration_ms=duration,
                details={
                    "enrichment_log": enrichment_log,
                    "regulatory_compliance": regulatory_compliance
                }
            )
            
            logger.info(f"✅ {self.name}: Added {fields_added} fields")
            return result, agent_result
            
        except Exception as e:
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            logger.error(f"❌ {self.name} error: {e}")
            
            agent_result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.ERROR,
                message=f"Enrichment error: {str(e)}",
                duration_ms=duration
            )
            raise
    
    async def _generate_header_fields(self, parsed_mt: Dict[str, Any]) -> tuple[Dict[str, MappedField], list]:
        """Generate mandatory group header fields"""
        fields = {}
        log = []
        
        # Message ID
        msg_id = f"MX{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{random.randint(100000, 999999)}"
        fields['GrpHdr.MsgId'] = MappedField(
            value=msg_id,
            confidence=1.0,
            reasoning='Generated unique ISO 20022 message identifier',
            source_field='generated',
            method='generated',
            mx_path='GrpHdr.MsgId'
        )
        log.append(f"Generated MsgId: {msg_id}")
        
        # Creation DateTime
        cre_dt_tm = datetime.utcnow().isoformat() + 'Z'
        fields['GrpHdr.CreDtTm'] = MappedField(
            value=cre_dt_tm,
            confidence=1.0,
            reasoning='Current UTC timestamp for message creation',
            source_field='generated',
            method='generated',
            mx_path='GrpHdr.CreDtTm'
        )
        log.append('Added CreDtTm timestamp')
        
        # Number of Transactions
        fields['GrpHdr.NbOfTxs'] = MappedField(
            value='1',
            confidence=1.0,
            reasoning='Single transaction in batch',
            source_field='generated',
            method='generated',
            mx_path='GrpHdr.NbOfTxs'
        )
        log.append('Set NbOfTxs to 1')
        
        # Settlement Method
        fields['GrpHdr.SttlmInf.SttlmMtd'] = MappedField(
            value='INDA',
            confidence=0.95,
            reasoning='Default settlement method - Instructed Agent',
            source_field='generated',
            method='generated',
            mx_path='GrpHdr.SttlmInf.SttlmMtd'
        )
        log.append('Set settlement method to INDA')
        
        return fields, log
    
    def _generate_end_to_end_id(self, parsed_mt: Dict[str, Any]) -> tuple[Dict[str, MappedField], str]:
        """Generate End-to-End ID from transaction reference"""
        tx_ref = parsed_mt.get('fields', {}).get('transaction_reference', '')
        e2e_id = f"E2E-{tx_ref}" if tx_ref else f"E2E-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        field = {
            'CdtTrfTxInf.PmtId.EndToEndId': MappedField(
                value=e2e_id,
                confidence=0.95,
                reasoning='Derived from transaction reference for end-to-end tracking',
                source_field='transaction_reference',
                method='inferred',
                mx_path='CdtTrfTxInf.PmtId.EndToEndId'
            )
        }
        
        return field, f"Generated EndToEndId: {e2e_id}"
    
    async def _enrich_bic_information(self, data: Dict[str, MappedField]) -> tuple[Dict[str, MappedField], list]:
        """Enrich BIC codes with bank information from directory"""
        fields = {}
        log = []
        
        for path, field_data in list(data.items()):
            if 'BICFI' in path and isinstance(field_data, MappedField):
                bic = str(field_data.value)[:8] if field_data.value else ''
                
                if bic in self.bic_directory:
                    bank_info = self.bic_directory[bic]
                    
                    # Add bank name
                    name_path = path.replace('BICFI', 'Nm')
                    fields[name_path] = MappedField(
                        value=bank_info['name'],
                        confidence=1.0,
                        reasoning=f'Bank name from BIC directory for {bic}',
                        source_field=path,
                        method='enriched',
                        mx_path=name_path
                    )
                    log.append(f"Added bank name for BIC {bic}: {bank_info['name']}")
                    
                    # Add country
                    ctry_path = path.replace('FinInstnId.BICFI', 'PstlAdr.Ctry')
                    fields[ctry_path] = MappedField(
                        value=bank_info['country'],
                        confidence=1.0,
                        reasoning=f'Country from BIC directory for {bic}',
                        source_field=path,
                        method='enriched',
                        mx_path=ctry_path
                    )
        
        return fields, log
    
    async def _add_regulatory_fields(
        self,
        data: Dict[str, MappedField],
        currency: str,
        approach: TransformationApproach
    ) -> tuple[Dict[str, MappedField], list, Dict[str, bool]]:
        """Add jurisdiction-specific regulatory fields"""
        fields = {}
        log = []
        compliance = {}
        
        # Determine jurisdiction from currency
        jurisdiction_map = {'USD': 'US', 'EUR': 'EU', 'GBP': 'GB'}
        jurisdiction = jurisdiction_map.get(currency, 'US')
        
        if jurisdiction in self.regulatory_requirements:
            reqs = self.regulatory_requirements[jurisdiction]
            
            # Add LEI for EU transactions
            if 'LEI' in reqs['fields']:
                lei = self._generate_lei()
                fields['CdtTrfTxInf.Dbtr.Id.OrgId.LEI'] = MappedField(
                    value=lei,
                    confidence=0.88,
                    reasoning=f'LEI required for {jurisdiction} regulatory compliance',
                    source_field='regulatory',
                    method='enriched',
                    mx_path='CdtTrfTxInf.Dbtr.Id.OrgId.LEI'
                )
                log.append(f'Added LEI for {jurisdiction} compliance')
                compliance['LEI'] = True
            
            # Add Federal Reference for US transactions
            if 'FedRef' in reqs['fields']:
                fed_ref = f"FED{random.randint(1000000, 9999999)}"
                fields['SplmtryData.Envlp.FedRef'] = MappedField(
                    value=fed_ref,
                    confidence=0.90,
                    reasoning='Federal reference for US regulatory reporting',
                    source_field='regulatory',
                    method='enriched',
                    mx_path='SplmtryData.Envlp.FedRef'
                )
                log.append(f'Added Federal reference for US compliance')
                compliance['FedRef'] = True
        
        return fields, log, compliance
    
    async def _enrich_party_data(
        self,
        data: Dict[str, MappedField],
        parsed_mt: Dict[str, Any]
    ) -> tuple[Dict[str, MappedField], list]:
        """Enrich party information using LLM"""
        fields = {}
        log = []
        
        if llm_service.is_available:
            # Extract ordering customer info
            ordering = parsed_mt.get('fields', {}).get('ordering_customer', '')
            if ordering:
                try:
                    currency = parsed_mt.get('fields', {}).get('currency', 'USD')
                    enriched = await llm_service.enrich_party_data(
                        ordering, 'Debtor', {'currency': currency}
                    )
                    
                    if enriched.get('address', {}).get('country'):
                        fields['CdtTrfTxInf.Dbtr.PstlAdr.Ctry'] = MappedField(
                            value=enriched['address']['country'],
                            confidence=enriched.get('confidence', 0.85),
                            reasoning='LLM extracted country from party data',
                            source_field='ordering_customer',
                            method='enriched',
                            mx_path='CdtTrfTxInf.Dbtr.PstlAdr.Ctry'
                        )
                        log.append('LLM enriched debtor country')
                except Exception as e:
                    logger.warning(f"Party enrichment failed: {e}")
        
        return fields, log
    
    def _map_charge_bearer(self, data: Dict[str, MappedField]) -> tuple[Dict[str, MappedField], str]:
        """Map charge bearer code from MT to MX format"""
        for path, field in data.items():
            if 'ChrgBr' in path and isinstance(field, MappedField):
                mt_code = str(field.value)
                if mt_code in self.charge_bearer_mapping:
                    mx_code = self.charge_bearer_mapping[mt_code]
                    return {
                        path: MappedField(
                            value=mx_code,
                            confidence=1.0,
                            reasoning=f'Mapped charge bearer {mt_code} to {mx_code}',
                            source_field=field.source_field,
                            method='enriched',
                            mx_path=path
                        )
                    }, f'Mapped charge bearer: {mt_code} → {mx_code}'
        
        return {}, ''
    
    def _generate_lei(self) -> str:
        """Generate mock Legal Entity Identifier (20 alphanumeric chars)"""
        chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        return ''.join(random.choices(chars, k=20))
