"""
ISO 20022 Migration Platform - FastAPI Backend
GenAI-Powered Agentic Migration System API
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import random
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ISO 20022 GenAI Migration API",
    description="Agentic MT to MX transformation with Rule-based and LLM approaches",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============== Data Models ==============

class TransformationRequest(BaseModel):
    mt_message: str
    approach: str = "hybrid"  # "rules", "llm", "hybrid"
    message_id: Optional[str] = None

class AgentResult(BaseModel):
    status: str
    message: str
    confidence: Optional[float] = None
    fields_processed: int = 0
    duration_ms: int = 0

class TransformationResponse(BaseModel):
    success: bool
    message_id: str
    mt_type: str
    mx_type: str
    approach_used: str
    parsed_mt: Dict[str, Any]
    mx_structure: Dict[str, Any]
    mx_xml: str
    agent_results: Dict[str, AgentResult]
    statistics: Dict[str, Any]
    timestamp: str

# ============== MT Parser ==============

class MTParser:
    """Parse SWIFT MT format messages"""
    
    def parse(self, raw_message: str, message_id: str = None) -> Dict[str, Any]:
        message_type = self._detect_message_type(raw_message)
        
        if message_type == 'MT103':
            return self._parse_mt103(raw_message, message_id)
        elif message_type == 'MT202':
            return self._parse_mt202(raw_message, message_id)
        else:
            return self._parse_generic(raw_message, message_type, message_id)
    
    def _detect_message_type(self, raw_message: str) -> str:
        if ':20:' in raw_message and ':32A:' in raw_message and ':50K:' in raw_message:
            return 'MT103'
        elif ':20:' in raw_message and ':32A:' in raw_message and ':53B:' in raw_message:
            return 'MT202'
        return 'MTXXX'
    
    def _parse_mt103(self, raw_message: str, msg_id: str) -> Dict[str, Any]:
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
        
        # Field 50K: Ordering Customer
        match = re.search(r':50K:(.*?)(?=:\d{2}[A-Z]?:|\Z)', raw_message, re.DOTALL)
        if match:
            fields['ordering_customer'] = match.group(1).strip()
        
        # Field 52A: Ordering Institution
        match = re.search(r':52A:([^\n:]+)', raw_message)
        if match:
            fields['ordering_institution'] = match.group(1).strip()
        
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
        
        # Field 72: Sender to Receiver Information
        match = re.search(r':72:(.*?)(?=:\d{2}[A-Z]?:|\Z)', raw_message, re.DOTALL)
        if match:
            fields['sender_to_receiver_info'] = match.group(1).strip()
        
        return {
            'message_id': msg_id or f"MT103-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'message_type': 'MT103',
            'mx_equivalent': 'pacs.008',
            'fields': fields,
            'field_count': len(fields),
            'raw': raw_message
        }
    
    def _parse_mt202(self, raw_message: str, msg_id: str) -> Dict[str, Any]:
        fields = {}
        
        match = re.search(r':20:([^\n:]+)', raw_message)
        if match:
            fields['transaction_reference'] = match.group(1).strip()
        
        match = re.search(r':32A:(\d{6})([A-Z]{3})([\d,\.]+)', raw_message)
        if match:
            fields['value_date'] = match.group(1)
            fields['currency'] = match.group(2)
            fields['amount'] = match.group(3).replace(',', '.')
        
        return {
            'message_id': msg_id or f"MT202-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'message_type': 'MT202',
            'mx_equivalent': 'pacs.009',
            'fields': fields,
            'field_count': len(fields),
            'raw': raw_message
        }
    
    def _parse_generic(self, raw_message: str, msg_type: str, msg_id: str) -> Dict[str, Any]:
        return {
            'message_id': msg_id or f"{msg_type}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'message_type': msg_type,
            'mx_equivalent': 'pacs.XXX',
            'fields': {'raw': raw_message},
            'field_count': 1,
            'raw': raw_message
        }

# ============== Mapping Agent ==============

class MappingAgent:
    """AI Agent for semantic field mapping"""
    
    def __init__(self):
        self.rule_mappings = {
            'transaction_reference': {
                'mx_path': 'CdtTrfTxInf.PmtId.InstrId',
                'confidence': 0.98,
                'reasoning': 'Direct mapping - transaction identifier'
            },
            'value_date': {
                'mx_path': 'CdtTrfTxInf.IntrBkSttlmDt',
                'confidence': 0.99,
                'reasoning': 'Value date to settlement date'
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
                'mx_path': 'CdtTrfTxInf.Dbtr',
                'confidence': 0.97,
                'reasoning': 'Ordering customer is debtor'
            },
            'ordering_institution': {
                'mx_path': 'CdtTrfTxInf.DbtrAgt.FinInstnId.BICFI',
                'confidence': 0.98,
                'reasoning': 'Ordering institution BIC'
            },
            'beneficiary_customer': {
                'mx_path': 'CdtTrfTxInf.Cdtr',
                'confidence': 0.97,
                'reasoning': 'Beneficiary is creditor'
            },
            'remittance_info': {
                'mx_path': 'CdtTrfTxInf.RmtInf.Ustrd',
                'confidence': 0.95,
                'reasoning': 'Remittance to unstructured info'
            },
            'charge_bearer': {
                'mx_path': 'CdtTrfTxInf.ChrgBr',
                'confidence': 1.0,
                'reasoning': 'Charge bearer - direct mapping'
            }
        }
    
    async def map_fields(self, parsed_mt: Dict[str, Any], approach: str) -> Dict[str, Any]:
        fields = parsed_mt['fields']
        mapped_fields = {}
        
        # Simulate processing time based on approach
        if approach == 'llm':
            await asyncio.sleep(0.3)  # LLM inference time
        elif approach == 'hybrid':
            await asyncio.sleep(0.15)
        else:
            await asyncio.sleep(0.05)  # Rules are fast
        
        for field_name, value in fields.items():
            if field_name in self.rule_mappings:
                rule = self.rule_mappings[field_name]
                confidence = rule['confidence']
                
                # Adjust confidence based on approach
                if approach == 'llm':
                    confidence = min(confidence, 0.94 + random.uniform(-0.02, 0.02))
                elif approach == 'hybrid':
                    confidence = confidence * 0.98
                
                mapped_fields[rule['mx_path']] = {
                    'value': value,
                    'confidence': confidence,
                    'reasoning': rule['reasoning'],
                    'source_field': field_name,
                    'method': 'rule' if approach == 'rules' else ('llm' if approach == 'llm' else 'hybrid')
                }
            else:
                # Unknown field - use LLM inference
                inferred = await self._llm_infer_mapping(field_name, value)
                mapped_fields[inferred['mx_path']] = inferred
        
        overall_confidence = sum(f['confidence'] for f in mapped_fields.values()) / len(mapped_fields) if mapped_fields else 0
        
        return {
            'mapped_fields': mapped_fields,
            'fields_mapped': len(mapped_fields),
            'overall_confidence': overall_confidence,
            'approach': approach
        }
    
    async def _llm_infer_mapping(self, field_name: str, value: Any) -> Dict[str, Any]:
        await asyncio.sleep(0.05)
        
        # Simulate LLM semantic analysis
        if 'date' in field_name.lower():
            mx_path = 'CdtTrfTxInf.IntrBkSttlmDt'
            reasoning = 'LLM detected date field'
        elif 'amount' in field_name.lower():
            mx_path = 'CdtTrfTxInf.IntrBkSttlmAmt.Value'
            reasoning = 'LLM detected monetary value'
        else:
            mx_path = 'CdtTrfTxInf.RmtInf.Ustrd'
            reasoning = 'LLM defaulting to unstructured info'
        
        return {
            'value': value,
            'confidence': random.uniform(0.70, 0.88),
            'reasoning': reasoning,
            'source_field': field_name,
            'method': 'llm_inference'
        }

# ============== Enrichment Agent ==============

class EnrichmentAgent:
    """AI Agent for data enrichment"""
    
    def __init__(self):
        self.bic_directory = {
            'CHASUS33': {'name': 'JPMORGAN CHASE', 'country': 'US'},
            'CITIUS33': {'name': 'CITIBANK', 'country': 'US'},
            'DEUTDEFF': {'name': 'DEUTSCHE BANK', 'country': 'DE'},
            'HSBCGB2L': {'name': 'HSBC BANK', 'country': 'GB'},
            'BARCGB22': {'name': 'BARCLAYS BANK', 'country': 'GB'}
        }
    
    async def enrich(self, mapped_fields: Dict[str, Any], parsed_mt: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.2)
        
        enriched_data = mapped_fields['mapped_fields'].copy()
        fields_added = 0
        enrichment_log = []
        
        # Add message ID
        msg_id = f"MX{datetime.utcnow().strftime('%Y%m%d%H%M%S')}{random.randint(100000, 999999)}"
        enriched_data['GrpHdr.MsgId'] = {
            'value': msg_id,
            'confidence': 1.0,
            'reasoning': 'Generated unique message ID',
            'method': 'generated'
        }
        fields_added += 1
        enrichment_log.append('Generated MsgId')
        
        # Add creation timestamp
        enriched_data['GrpHdr.CreDtTm'] = {
            'value': datetime.utcnow().isoformat() + 'Z',
            'confidence': 1.0,
            'reasoning': 'Current UTC timestamp',
            'method': 'generated'
        }
        fields_added += 1
        enrichment_log.append('Added CreDtTm')
        
        # Add End-to-End ID
        tx_ref = parsed_mt['fields'].get('transaction_reference', msg_id)
        enriched_data['CdtTrfTxInf.PmtId.EndToEndId'] = {
            'value': f"E2E-{tx_ref}",
            'confidence': 0.95,
            'reasoning': 'Inferred from transaction reference',
            'method': 'inferred'
        }
        fields_added += 1
        enrichment_log.append('Inferred EndToEndId')
        
        # Add regulatory fields based on currency
        currency = parsed_mt['fields'].get('currency', 'USD')
        if currency == 'EUR':
            enriched_data['SplmtryData.LEI'] = {
                'value': ''.join(random.choices('0123456789ABCDEF', k=20)),
                'confidence': 0.88,
                'reasoning': 'LEI required for EUR transactions',
                'method': 'regulatory'
            }
            fields_added += 1
            enrichment_log.append('Added LEI for EU compliance')
        elif currency == 'USD':
            enriched_data['SplmtryData.FedRef'] = {
                'value': f"FED{random.randint(1000000, 9999999)}",
                'confidence': 0.90,
                'reasoning': 'Federal reference for USD',
                'method': 'regulatory'
            }
            fields_added += 1
            enrichment_log.append('Added Fed reference for US compliance')
        
        # Enrich BIC information
        ordering_inst = parsed_mt['fields'].get('ordering_institution', '')
        bic = ordering_inst[:8] if len(ordering_inst) >= 8 else ''
        if bic in self.bic_directory:
            bank_info = self.bic_directory[bic]
            enriched_data['CdtTrfTxInf.DbtrAgt.FinInstnId.Nm'] = {
                'value': bank_info['name'],
                'confidence': 1.0,
                'reasoning': f'Bank name from BIC directory for {bic}',
                'method': 'knowledge_graph'
            }
            fields_added += 1
            enrichment_log.append(f'Added bank name for BIC {bic}')
        
        return {
            'enriched_data': enriched_data,
            'fields_added': fields_added,
            'enrichment_log': enrichment_log
        }

# ============== Validation Agent ==============

class ValidationAgent:
    """AI Agent for schema validation"""
    
    def __init__(self):
        self.mandatory_fields = [
            'GrpHdr.MsgId',
            'GrpHdr.CreDtTm',
            'CdtTrfTxInf.PmtId.EndToEndId',
            'CdtTrfTxInf.IntrBkSttlmAmt.Ccy',
            'CdtTrfTxInf.IntrBkSttlmAmt.Value'
        ]
    
    async def validate(self, enriched_data: Dict[str, Any]) -> Dict[str, Any]:
        await asyncio.sleep(0.15)
        
        errors = []
        warnings = []
        
        # Check mandatory fields
        for field in self.mandatory_fields:
            found = any(field in key for key in enriched_data.keys())
            if not found:
                errors.append({
                    'type': 'missing_mandatory',
                    'field': field,
                    'message': f'Mandatory field {field} is missing'
                })
        
        # Check field constraints
        for path, field_data in enriched_data.items():
            if isinstance(field_data, dict):
                value = field_data.get('value', '')
                
                # Check MsgId length
                if 'MsgId' in path and isinstance(value, str) and len(value) > 35:
                    errors.append({
                        'type': 'constraint_violation',
                        'field': path,
                        'message': f'MsgId exceeds 35 characters'
                    })
                
                # Check amount format
                if 'Amt.Value' in path:
                    try:
                        float(value)
                    except:
                        errors.append({
                            'type': 'invalid_format',
                            'field': path,
                            'message': 'Invalid amount format'
                        })
        
        # Contextual validation (AI)
        if random.random() < 0.1:
            warnings.append({
                'type': 'contextual',
                'message': 'AI detected unusual transaction pattern',
                'confidence': 0.78
            })
        
        is_valid = len(errors) == 0
        score = max(0, 100 - len(errors) * 10 - len(warnings) * 3)
        
        return {
            'is_valid': is_valid,
            'score': score,
            'errors': errors,
            'warnings': warnings,
            'checked_fields': len(self.mandatory_fields)
        }

# ============== MX Generator ==============

class MXGenerator:
    """Generate ISO 20022 MX XML messages"""
    
    def generate(self, enriched_data: Dict[str, Any], mt_type: str) -> Dict[str, Any]:
        mx_type = 'pacs.008' if mt_type == 'MT103' else 'pacs.009'
        
        # Build structured MX
        mx_structure = self._build_structure(enriched_data, mx_type)
        
        # Generate XML
        xml_output = self._generate_xml(mx_structure, mx_type)
        
        return {
            'mx_type': mx_type,
            'version': '001.08',
            'structure': mx_structure,
            'xml': xml_output
        }
    
    def _build_structure(self, data: Dict[str, Any], mx_type: str) -> Dict[str, Any]:
        structure = {
            'Document': {
                'FIToFICstmrCdtTrf': {
                    'GrpHdr': {
                        'MsgId': '',
                        'CreDtTm': '',
                        'NbOfTxs': '1',
                        'SttlmInf': {'SttlmMtd': 'INDA'}
                    },
                    'CdtTrfTxInf': {
                        'PmtId': {},
                        'IntrBkSttlmAmt': {},
                        'Dbtr': {},
                        'DbtrAgt': {'FinInstnId': {}},
                        'Cdtr': {},
                        'CdtrAgt': {'FinInstnId': {}},
                        'RmtInf': {}
                    }
                }
            }
        }
        
        # Populate from enriched data
        for path, field_data in data.items():
            if isinstance(field_data, dict):
                value = field_data.get('value', '')
                self._set_nested_value(structure, path, value)
        
        return structure
    
    def _set_nested_value(self, obj: Dict, path: str, value: Any):
        parts = path.split('.')
        current = obj.get('Document', {}).get('FIToFICstmrCdtTrf', {})
        
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            current = current[part]
        
        if parts:
            current[parts[-1]] = value
    
    def _generate_xml(self, structure: Dict[str, Any], mx_type: str) -> str:
        def dict_to_xml(d, indent=0):
            xml_parts = []
            spaces = '  ' * indent
            for key, value in d.items():
                if isinstance(value, dict):
                    inner = dict_to_xml(value, indent + 1)
                    xml_parts.append(f"{spaces}<{key}>\n{inner}{spaces}</{key}>")
                else:
                    xml_parts.append(f"{spaces}<{key}>{value}</{key}>")
            return '\n'.join(xml_parts) + '\n'
        
        ns = f"urn:iso:std:iso:20022:tech:xsd:{mx_type}.001.08"
        xml = f'<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += f'<Document xmlns="{ns}">\n'
        xml += dict_to_xml(structure.get('Document', {}), 1)
        xml += '</Document>'
        
        return xml

# ============== API Endpoints ==============

@app.get("/")
async def root():
    return {
        "service": "ISO 20022 GenAI Migration API",
        "version": "1.0.0",
        "endpoints": ["/transform", "/health", "/sample-messages"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/sample-messages")
async def get_sample_messages():
    return {
        "samples": [
            {
                "id": "MT103-001",
                "name": "Standard USD Transfer",
                "message": """:20:TRX2024112001
:23B:CRED
:32A:241118USD50000,00
:50K:/123456789
ACME CORPORATION
123 BUSINESS STREET
NEW YORK, NY 10001
:52A:CHASUS33XXX
:59:/987654321
GLOBAL TRADING LTD
456 COMMERCE AVENUE
LONDON, EC2R 8AH
:70:INVOICE INV-2024-1234
:71A:SHA"""
            },
            {
                "id": "MT103-002",
                "name": "High Value EUR Transfer",
                "message": """:20:TRX2024112002
:23B:CRED
:32A:241118EUR2500000,00
:50K:/DE89370400440532013000
DEUTSCHE MANUFACTURING GMBH
INDUSTRIESTRASSE 45
60329 FRANKFURT
:52A:DEUTDEFFXXX
:59:/GB82WEST12345698765432
BRITISH IMPORTS PLC
789 TRADE LANE
MANCHESTER, M1 2AB
:70:CONTRACT CON-2024-5678
:71A:OUR"""
            },
            {
                "id": "MT103-003",
                "name": "Cross-Border GBP Payment",
                "message": """:20:TRX2024112003
:23B:CRED
:32A:241118GBP175000,00
:50K:/GB29NWBK60161331926819
LONDON TECH VENTURES
10 INNOVATION SQUARE
LONDON, SW1A 1AA
:52A:HSBCGB2LXXX
:59:/US12345678901234567890
SILICON VALLEY INNOVATIONS INC
1 STARTUP BLVD
SAN FRANCISCO, CA 94105
:70:SERIES B INVESTMENT
:71A:BEN"""
            }
        ]
    }

@app.post("/transform", response_model=TransformationResponse)
async def transform_message(request: TransformationRequest):
    """
    Transform MT message to MX format using agentic AI pipeline
    """
    start_time = datetime.utcnow()
    agent_results = {}
    
    try:
        # Step 1: Parse MT Message
        parser = MTParser()
        parse_start = datetime.utcnow()
        parsed_mt = parser.parse(request.mt_message, request.message_id)
        parse_duration = int((datetime.utcnow() - parse_start).total_seconds() * 1000)
        
        agent_results['parser'] = AgentResult(
            status='complete',
            message=f"Parsed {parsed_mt['field_count']} fields from {parsed_mt['message_type']}",
            fields_processed=parsed_mt['field_count'],
            duration_ms=parse_duration
        )
        
        # Step 2: Mapping Agent
        mapping_agent = MappingAgent()
        map_start = datetime.utcnow()
        mapping_result = await mapping_agent.map_fields(parsed_mt, request.approach)
        map_duration = int((datetime.utcnow() - map_start).total_seconds() * 1000)
        
        agent_results['mapping'] = AgentResult(
            status='complete',
            message=f"Mapped {mapping_result['fields_mapped']} fields using {request.approach} approach",
            confidence=mapping_result['overall_confidence'],
            fields_processed=mapping_result['fields_mapped'],
            duration_ms=map_duration
        )
        
        # Step 3: Enrichment Agent
        enrichment_agent = EnrichmentAgent()
        enrich_start = datetime.utcnow()
        enrichment_result = await enrichment_agent.enrich(mapping_result, parsed_mt)
        enrich_duration = int((datetime.utcnow() - enrich_start).total_seconds() * 1000)
        
        agent_results['enrichment'] = AgentResult(
            status='complete',
            message=f"Added {enrichment_result['fields_added']} regulatory/mandatory fields",
            fields_processed=enrichment_result['fields_added'],
            duration_ms=enrich_duration
        )
        
        # Step 4: Generate MX
        generator = MXGenerator()
        mx_output = generator.generate(enrichment_result['enriched_data'], parsed_mt['message_type'])
        
        # Step 5: Validation Agent
        validation_agent = ValidationAgent()
        val_start = datetime.utcnow()
        validation_result = await validation_agent.validate(enrichment_result['enriched_data'])
        val_duration = int((datetime.utcnow() - val_start).total_seconds() * 1000)
        
        agent_results['validation'] = AgentResult(
            status='complete' if validation_result['is_valid'] else 'warning',
            message=f"Validation score: {validation_result['score']}% - {len(validation_result['errors'])} errors, {len(validation_result['warnings'])} warnings",
            confidence=validation_result['score'] / 100,
            fields_processed=validation_result['checked_fields'],
            duration_ms=val_duration
        )
        
        # Calculate statistics
        total_duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        statistics = {
            'total_duration_ms': total_duration,
            'fields_parsed': parsed_mt['field_count'],
            'fields_mapped': mapping_result['fields_mapped'],
            'fields_enriched': enrichment_result['fields_added'],
            'overall_confidence': mapping_result['overall_confidence'],
            'validation_score': validation_result['score'],
            'errors': len(validation_result['errors']),
            'warnings': len(validation_result['warnings'])
        }
        
        return TransformationResponse(
            success=True,
            message_id=parsed_mt['message_id'],
            mt_type=parsed_mt['message_type'],
            mx_type=mx_output['mx_type'],
            approach_used=request.approach,
            parsed_mt=parsed_mt,
            mx_structure=mx_output['structure'],
            mx_xml=mx_output['xml'],
            agent_results=agent_results,
            statistics=statistics,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Transformation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
