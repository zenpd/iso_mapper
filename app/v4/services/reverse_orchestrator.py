"""
Reverse Transformation Orchestrator - XML/MX to MT transformation
Reverse of the forward orchestrator
"""

import logging
from datetime import datetime
from typing import Dict, Any

from models import TransformationState, TransformationApproach
from agents.xml_parser import XMLParserAgent
from agents.mt_generator import MTGeneratorAgent

logger = logging.getLogger(__name__)


class ReverseTransformationOrchestrator:
    """Orchestrator for ISO 20022 (XML) to SWIFT MT transformation"""
    
    def __init__(self):
        self.xml_parser = XMLParserAgent()
        self.mt_generator = MTGeneratorAgent()
        logger.info("🚀 Reverse Orchestrator initialized")
    
    async def transform(self, state: TransformationState) -> Dict[str, Any]:
        """Execute reverse transformation workflow (XML → MT)"""
        start_time = datetime.utcnow()
        
        result = {
            "raw_mx_message": state.raw_mt_message,  # Contains XML
            "message_id": state.message_id or f"MSG-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "approach": state.approach.value,
            "parsed_xml": {},
            "mt_fields": {},
            "mt_output": {},
            "agent_results": {},
            "error": "",
            "success": False
        }
        
        try:
            # Step 1: Parse XML
            logger.info("Step 1: Parsing XML...")
            parsed, parse_result = self.xml_parser.parse(
                state.raw_mt_message,
                result["message_id"]
            )
            result["parsed_xml"] = parsed.model_dump()
            result["agent_results"]["parser"] = parse_result.model_dump()
            
            # Determine MT type based on MX type
            mx_type = parsed.mx_equivalent
            if mx_type == 'MT101':
                mt_type = 'MT101'
            elif mx_type == 'MT103':
                mt_type = 'MT103'
            elif mx_type == 'MT202':
                mt_type = 'MT202'
            else:
                mt_type = 'MT103'  # Default
            
            # Step 2: Generate MT message
            logger.info(f"Step 2: Generating {mt_type}...")
            mt_message = self.mt_generator.generate(parsed.fields, mt_type)
            
            result["mt_fields"] = parsed.fields
            result["mt_output"] = {
                "mt_type": mt_type,
                "message": mt_message,
                "field_count": len(parsed.fields),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            result["success"] = True
            logger.info(f"✅ Reverse transformation complete: {parsed.message_type} -> {mt_type}")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            result["error"] = str(e)
            result["success"] = False
        
        result["total_duration_ms"] = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        result["completed_at"] = datetime.utcnow().isoformat()
        
        return result


# Singleton
reverse_orchestrator = ReverseTransformationOrchestrator()
