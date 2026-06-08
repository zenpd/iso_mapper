"""
Orchestrator - Sequential MT to MX transformation
MT101 -> pain.001 | MT103 -> pacs.008
"""

import logging
from datetime import datetime
from typing import Dict, Any

from models import (
    TransformationState, TransformationApproach,
    MappedField
)
from agents import MTParserAgent, MappingAgent, EnrichmentAgent, ValidationAgent

logger = logging.getLogger(__name__)


class TransformationOrchestrator:
    """Sequential orchestrator for MT to MX transformation"""
    
    def __init__(self):
        self.parser_agent = MTParserAgent()
        self.mapping_agent = MappingAgent()
        self.enrichment_agent = EnrichmentAgent()
        self.validation_agent = ValidationAgent()
        logger.info("🚀 Orchestrator initialized")
    
    async def transform(self, state: TransformationState) -> Dict[str, Any]:
        """Execute transformation workflow"""
        start_time = datetime.utcnow()
        
        result = {
            "raw_mt_message": state.raw_mt_message,
            "message_id": state.message_id or f"MSG-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "approach": state.approach.value,
            "parsed_mt": {},
            "mapping_result": {},
            "enrichment_result": {},
            "validation_result": {},
            "mx_output": {},
            "agent_results": {},
            "error": "",
            "success": False
        }
        
        try:
            # Step 1: Parse
            logger.info("Step 1: Parsing...")
            parsed, parse_result = self.parser_agent.parse(
                state.raw_mt_message,
                result["message_id"]
            )
            result["parsed_mt"] = parsed.model_dump()
            result["agent_results"]["parser"] = parse_result.model_dump()
            
            # Determine correct MX type based on MT type
            mt_type = result["parsed_mt"]["message_type"]
            if mt_type == 'MT101':
                mx_type = 'pain.001'
            elif mt_type == 'MT103':
                mx_type = 'pacs.008'
            else:
                mx_type = 'pacs.008'  # Default
            
            # Update parsed_mt with correct mx_equivalent
            result["parsed_mt"]["mx_equivalent"] = mx_type
            
            # Step 2: Map
            logger.info("Step 2: Mapping...")
            mapping_result, map_agent_result = await self.mapping_agent.map_fields(
                parsed, state.approach
            )
            
            mapped_fields_dict = {
                k: v.model_dump() for k, v in mapping_result.mapped_fields.items()
            }
            result["mapping_result"] = {
                "mapped_fields": mapped_fields_dict,
                "fields_mapped": mapping_result.fields_mapped,
                "overall_confidence": mapping_result.overall_confidence,
                "low_confidence_fields": mapping_result.low_confidence_fields,
                "approach_used": mapping_result.approach_used.value
            }
            result["agent_results"]["mapping"] = map_agent_result.model_dump()
            
            # Step 3: Enrich
            logger.info("Step 3: Enriching...")
            from models import MappingResult
            mapping_for_enrich = MappingResult(
                mapped_fields={k: MappedField(**v) for k, v in mapped_fields_dict.items()},
                fields_mapped=mapping_result.fields_mapped,
                overall_confidence=mapping_result.overall_confidence,
                low_confidence_fields=mapping_result.low_confidence_fields,
                approach_used=mapping_result.approach_used
            )
            
            enrichment_result, enrich_agent_result = await self.enrichment_agent.enrich(
                mapping_for_enrich,
                result["parsed_mt"],
                state.approach
            )
            
            enriched_dict = {
                k: v.model_dump() if isinstance(v, MappedField) else v
                for k, v in enrichment_result.enriched_data.items()
            }
            result["enrichment_result"] = {
                "enriched_data": enriched_dict,
                "fields_added": enrichment_result.fields_added,
                "enrichment_log": enrichment_result.enrichment_log,
                "regulatory_compliance": enrichment_result.regulatory_compliance
            }
            result["agent_results"]["enrichment"] = enrich_agent_result.model_dump()
            
            # Step 4: Validate
            logger.info("Step 4: Validating...")
            from models import EnrichmentResult
            enrichment_for_validate = EnrichmentResult(
                enriched_data={
                    k: MappedField(**v) if isinstance(v, dict) and 'confidence' in v else v
                    for k, v in enriched_dict.items()
                },
                fields_added=enrichment_result.fields_added,
                enrichment_log=enrichment_result.enrichment_log,
                regulatory_compliance=enrichment_result.regulatory_compliance
            )
            
            validation_result, val_agent_result = await self.validation_agent.validate(
                enrichment_for_validate,
                mx_type,
                state.approach
            )
            result["validation_result"] = validation_result.model_dump()
            result["agent_results"]["validation"] = val_agent_result.model_dump()
            
            # Step 5: Generate MX
            logger.info(f"Step 5: Generating {mx_type}...")
            mx_structure = self._build_mx_structure(enriched_dict, mx_type, mt_type)
            xml_output = self._generate_xml(mx_structure, mx_type)
            
            result["mx_output"] = {
                "mx_type": mx_type,
                "version": "001.08",
                "structure": mx_structure,
                "xml": xml_output,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            result["success"] = True
            logger.info(f"✅ Transformation complete: {mt_type} -> {mx_type}")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            result["error"] = str(e)
            result["success"] = False
        
        result["total_duration_ms"] = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        result["completed_at"] = datetime.utcnow().isoformat()
        
        return result
    
    def _build_mx_structure(self, enriched_data: Dict[str, Any], mx_type: str, mt_type: str) -> Dict[str, Any]:
        """Build MX structure based on message type"""
        
        if mx_type == 'pain.001':
            # Payment Initiation structure for MT101
            structure = {
                'Document': {
                    'CstmrCdtTrfInitn': {
                        'GrpHdr': {
                            'MsgId': '',
                            'CreDtTm': datetime.utcnow().isoformat(),
                            'NbOfTxs': '1',
                            'CtrlSum': '',
                            'InitgPty': {'Nm': ''}
                        },
                        'PmtInf': {
                            'PmtInfId': '',
                            'PmtMtd': 'TRF',
                            'NbOfTxs': '1',
                            'ReqdExctnDt': '',
                            'Dbtr': {'Nm': '', 'PstlAdr': {'AdrLine': ''}},
                            'DbtrAcct': {'Id': {'IBAN': ''}},
                            'DbtrAgt': {'FinInstnId': {'BICFI': ''}},
                            'CdtTrfTxInf': {
                                'PmtId': {'EndToEndId': ''},
                                'Amt': {'InstdAmt': {'Ccy': '', 'Value': ''}},
                                'CdtrAgt': {'FinInstnId': {'BICFI': ''}},
                                'Cdtr': {'Nm': '', 'PstlAdr': {'AdrLine': ''}},
                                'CdtrAcct': {'Id': {'IBAN': ''}},
                                'ChrgBr': 'SHAR',
                                'RmtInf': {'Ustrd': ''}
                            }
                        }
                    }
                }
            }
        elif mx_type == 'pacs.009':
            # Financial Institution Transfer structure for MT202
            structure = {
                'Document': {
                    'FIToFICstmrCdtTrf': {
                        'GrpHdr': {
                            'MsgId': '',
                            'CreDtTm': datetime.utcnow().isoformat(),
                            'NbOfTxs': '1',
                            'SttlmInf': {'SttlmMtd': 'INDA'}
                        },
                        'CdtTrfTxInf': {
                            'PmtId': {'EndToEndId': ''},
                            'IntrBkSttlmAmt': {'Ccy': '', 'Value': ''},
                            'IntrBkSttlmDt': '',
                            'ChrgBr': 'SHAR',
                            'InstgAgt': {'FinInstnId': {'BICFI': ''}},
                            'InstdAgt': {'FinInstnId': {'BICFI': ''}},
                            'IntrmyAgt1': {'FinInstnId': {'BICFI': ''}},
                            'InstrForNxtAgt': {'InstrInf': ''}
                        }
                    }
                }
            }
        else:
            # pacs.008 - Customer Credit Transfer (default)
            structure = {
                'Document': {
                    'FIToFICstmrCdtTrf': {
                        'GrpHdr': {
                            'MsgId': '',
                            'CreDtTm': datetime.utcnow().isoformat(),
                            'NbOfTxs': '1',
                            'SttlmInf': {'SttlmMtd': 'INDA'}
                        },
                        'CdtTrfTxInf': {
                            'PmtId': {'InstrId': '', 'EndToEndId': ''},
                            'IntrBkSttlmAmt': {'Ccy': '', 'Value': ''},
                            'IntrBkSttlmDt': '',
                            'ChrgBr': 'SHAR',
                            'Dbtr': {'Nm': '', 'PstlAdr': {}},
                            'DbtrAcct': {'Id': {'Othr': {'Id': ''}}},
                            'DbtrAgt': {'FinInstnId': {'BICFI': ''}},
                            'CdtrAgt': {'FinInstnId': {'BICFI': ''}},
                            'Cdtr': {'Nm': '', 'PstlAdr': {}},
                            'CdtrAcct': {'Id': {'Othr': {'Id': ''}}},
                            'RmtInf': {'Ustrd': ''}
                        }
                    }
                }
            }
        
        # Populate structure from enriched data
        for path, field_data in enriched_data.items():
            value = field_data.get('value') if isinstance(field_data, dict) else field_data
            if value:
                if mx_type == 'pain.001':
                    self._set_nested_value(structure['Document']['CstmrCdtTrfInitn'], path, value)
                else:
                    self._set_nested_value(structure['Document']['FIToFICstmrCdtTrf'], path, value)
        
        return structure
    
    def _set_nested_value(self, obj: Dict, path: str, value: Any):
        """Set nested value using dot notation"""
        parts = path.split('.')
        current = obj
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        
        if parts:
            current[parts[-1]] = value
    
    def _generate_xml(self, structure: Dict[str, Any], mx_type: str) -> str:
        """Generate XML from structure"""
        def dict_to_xml(d: Dict, indent: int = 0) -> str:
            xml_parts = []
            spaces = '  ' * indent
            
            for key, value in d.items():
                if isinstance(value, dict) and value:
                    inner = dict_to_xml(value, indent + 1)
                    if inner.strip():
                        xml_parts.append(f"{spaces}<{key}>\n{inner}{spaces}</{key}>")
                elif value is not None and value != '':
                    xml_parts.append(f"{spaces}<{key}>{value}</{key}>")
            
            return '\n'.join(xml_parts) + '\n' if xml_parts else ''
        
        ns = f"urn:iso:std:iso:20022:tech:xsd:{mx_type}.001.08"
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += f'<Document xmlns="{ns}">\n'
        xml += dict_to_xml(structure.get('Document', {}), 1)
        xml += '</Document>'
        
        return xml


# Singleton
orchestrator = TransformationOrchestrator()