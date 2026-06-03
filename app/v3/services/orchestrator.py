"""
LangGraph Orchestrator - FIXED VERSION
Agentic workflow orchestration using LangGraph state machine
"""

import logging
from datetime import datetime
from typing import Dict, Any, TypedDict, Annotated
import operator

from langgraph.graph import StateGraph, END

from models import (
    TransformationState, TransformationApproach,
    AgentResult, AgentStatus, MXOutput, MappedField
)
from agents import MTParserAgent, MappingAgent, EnrichmentAgent, ValidationAgent
from config import settings

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    """State schema for LangGraph"""
    raw_mt_message: str
    message_id: str
    approach: str
    parsed_mt: dict
    mapping_result: dict
    enrichment_result: dict
    validation_result: dict
    mx_output: dict
    agent_results: dict
    error: str
    success: bool


class TransformationOrchestrator:
    """
    LangGraph-based orchestrator for MT to MX transformation
    Coordinates all AI agents in a stateful workflow
    """
    
    def __init__(self):
        self.parser_agent = MTParserAgent()
        self.mapping_agent = MappingAgent()
        self.enrichment_agent = EnrichmentAgent()
        self.validation_agent = ValidationAgent()
        
        # Build LangGraph
        self.graph = self._build_graph()
        self.app = self.graph.compile()
        
        logger.info("🚀 LangGraph Orchestrator initialized")
    
    def _build_graph(self) -> StateGraph:
        """Build the transformation workflow graph"""
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("parse", self._parse_node)
        workflow.add_node("map", self._map_node)
        workflow.add_node("enrich", self._enrich_node)
        workflow.add_node("validate", self._validate_node)
        workflow.add_node("generate_mx", self._generate_mx_node)
        
        # Define edges
        workflow.set_entry_point("parse")
        workflow.add_edge("parse", "map")
        workflow.add_edge("map", "enrich")
        workflow.add_edge("enrich", "validate")
        workflow.add_edge("validate", "generate_mx")
        workflow.add_edge("generate_mx", END)
        
        return workflow
    
    async def _parse_node(self, state: GraphState) -> GraphState:
        """Parse MT message node"""
        try:
            parsed, result = self.parser_agent.parse(
                state["raw_mt_message"],
                state.get("message_id")
            )
            
            state["parsed_mt"] = parsed.model_dump()
            state["agent_results"]["parser"] = result.model_dump()
            return state
            
        except Exception as e:
            logger.error(f"Parse node error: {e}")
            state["error"] = str(e)
            state["success"] = False
            return state
    
    async def _map_node(self, state: GraphState) -> GraphState:
        """Map fields node"""
        try:
            from models import ParsedMTMessage
            parsed_mt = ParsedMTMessage(**state["parsed_mt"])
            approach = TransformationApproach(state.get("approach", "hybrid"))
            
            result, agent_result = await self.mapping_agent.map_fields(parsed_mt, approach)
            
            # Convert MappedField objects to dicts for serialization
            mapped_fields_dict = {
                k: v.model_dump() for k, v in result.mapped_fields.items()
            }
            
            state["mapping_result"] = {
                "mapped_fields": mapped_fields_dict,
                "fields_mapped": result.fields_mapped,
                "overall_confidence": result.overall_confidence,
                "low_confidence_fields": result.low_confidence_fields,
                "approach_used": result.approach_used.value
            }
            state["agent_results"]["mapping"] = agent_result.model_dump()
            return state
            
        except Exception as e:
            logger.error(f"Map node error: {e}")
            state["error"] = str(e)
            state["success"] = False
            return state
    
    async def _enrich_node(self, state: GraphState) -> GraphState:
        """Enrich data node"""
        try:
            from models import MappingResult
            
            # Reconstruct MappingResult with MappedField objects
            mapping_data = state["mapping_result"]
            mapped_fields = {
                k: MappedField(**v) for k, v in mapping_data["mapped_fields"].items()
            }
            mapping_result = MappingResult(
                mapped_fields=mapped_fields,
                fields_mapped=mapping_data["fields_mapped"],
                overall_confidence=mapping_data["overall_confidence"],
                low_confidence_fields=mapping_data.get("low_confidence_fields", []),
                approach_used=TransformationApproach(mapping_data["approach_used"])
            )
            
            approach = TransformationApproach(state.get("approach", "hybrid"))
            
            result, agent_result = await self.enrichment_agent.enrich(
                mapping_result,
                state["parsed_mt"],
                approach
            )
            
            # Convert enriched data for serialization
            enriched_dict = {
                k: v.model_dump() if isinstance(v, MappedField) else v 
                for k, v in result.enriched_data.items()
            }
            
            state["enrichment_result"] = {
                "enriched_data": enriched_dict,
                "fields_added": result.fields_added,
                "enrichment_log": result.enrichment_log,
                "regulatory_compliance": result.regulatory_compliance
            }
            state["agent_results"]["enrichment"] = agent_result.model_dump()
            return state
            
        except Exception as e:
            logger.error(f"Enrich node error: {e}")
            state["error"] = str(e)
            state["success"] = False
            return state
    
    async def _validate_node(self, state: GraphState) -> GraphState:
        """Validate MX message node"""
        try:
            from models import EnrichmentResult
            
            # Reconstruct EnrichmentResult
            enrich_data = state["enrichment_result"]
            enriched_fields = {
                k: MappedField(**v) if isinstance(v, dict) and 'confidence' in v else v
                for k, v in enrich_data["enriched_data"].items()
            }
            enrichment_result = EnrichmentResult(
                enriched_data=enriched_fields,
                fields_added=enrich_data["fields_added"],
                enrichment_log=enrich_data["enrichment_log"],
                regulatory_compliance=enrich_data.get("regulatory_compliance", {})
            )
            
            mx_type = state["parsed_mt"]["mx_equivalent"]
            approach = TransformationApproach(state.get("approach", "hybrid"))
            
            result, agent_result = await self.validation_agent.validate(
                enrichment_result,
                mx_type,
                approach
            )
            
            state["validation_result"] = result.model_dump()
            state["agent_results"]["validation"] = agent_result.model_dump()
            return state
            
        except Exception as e:
            logger.error(f"Validate node error: {e}")
            state["error"] = str(e)
            state["success"] = False
            return state
    
    async def _generate_mx_node(self, state: GraphState) -> GraphState:
        """Generate final MX message node"""
        try:
            enriched_data = state["enrichment_result"]["enriched_data"]
            mt_type = state["parsed_mt"]["message_type"]
            mx_type = 'pacs.008' if mt_type == 'MT103' else 'pacs.009'
            
            # Build MX structure
            mx_structure = self._build_mx_structure(enriched_data, mx_type)
            
            # Generate XML
            xml_output = self._generate_xml(mx_structure, mx_type)
            
            state["mx_output"] = {
                "mx_type": mx_type,
                "version": "001.08",
                "structure": mx_structure,
                "xml": xml_output,
                "generated_at": datetime.utcnow().isoformat()
            }
            state["success"] = True
            return state
            
        except Exception as e:
            logger.error(f"Generate MX node error: {e}")
            state["error"] = str(e)
            state["success"] = False
            return state
    
    def _build_mx_structure(self, enriched_data: Dict[str, Any], mx_type: str) -> Dict[str, Any]:
        """Build hierarchical MX structure from flat enriched data"""
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
                        'ChrgBr': 'SHAR',
                        'Dbtr': {'Nm': '', 'PstlAdr': {}},
                        'DbtrAgt': {'FinInstnId': {}},
                        'Cdtr': {'Nm': '', 'PstlAdr': {}},
                        'CdtrAgt': {'FinInstnId': {}},
                        'RmtInf': {}
                    }
                }
            }
        }
        
        # Populate structure from enriched data
        for path, field_data in enriched_data.items():
            value = field_data.get('value') if isinstance(field_data, dict) else field_data
            if value:
                self._set_nested_value(structure['Document']['FIToFICstmrCdtTrf'], path, value)
        
        return structure
    
    def _set_nested_value(self, obj: Dict, path: str, value: Any):
        """Set a value in nested dictionary using dot-notation path"""
        parts = path.split('.')
        current = obj
        
        for i, part in enumerate(parts[:-1]):
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        
        if parts:
            current[parts[-1]] = value
    
    def _generate_xml(self, structure: Dict[str, Any], mx_type: str) -> str:
        """Generate ISO 20022 XML from structure"""
        def dict_to_xml(d: Dict, indent: int = 0) -> str:
            xml_parts = []
            spaces = '  ' * indent
            
            for key, value in d.items():
                if isinstance(value, dict) and value:
                    inner = dict_to_xml(value, indent + 1)
                    xml_parts.append(f"{spaces}<{key}>\n{inner}{spaces}</{key}>")
                elif value is not None and value != '':
                    xml_parts.append(f"{spaces}<{key}>{value}</{key}>")
            
            return '\n'.join(xml_parts) + '\n' if xml_parts else ''
        
        ns = f"urn:iso:std:iso:20022:tech:xsd:{mx_type}.001.08"
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += f'<Document xmlns="{ns}" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
        xml += dict_to_xml(structure.get('Document', {}), 1)
        xml += '</Document>'
        
        return xml
    
    async def transform(self, state: TransformationState) -> Dict[str, Any]:
        """
        Execute the full transformation workflow
        """
        start_time = datetime.utcnow()
        
        # Prepare initial state
        initial_state: GraphState = {
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
            # Run the workflow using invoke instead of astream
            result = await self.app.ainvoke(initial_state)
            
            # Calculate total duration
            total_duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return {
                **result,
                "total_duration_ms": total_duration,
                "completed_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Transformation workflow error: {e}")
            import traceback
            traceback.print_exc()
            return {
                **initial_state,
                "error": str(e),
                "success": False,
                "total_duration_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
            }


# Singleton instance
orchestrator = TransformationOrchestrator()