"""
MX Message Generator
Generates ISO 20022 MX format messages from enriched data
"""

import json
import xml.etree.ElementTree as ET
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MXGenerator:
    """Generate ISO 20022 MX XML messages"""
    
    def generate(self, enriched_data: Dict[str, Any], mt_type: str) -> Dict[str, Any]:
        """
        Generate MX message from enriched mapped data
        """
        if mt_type == 'MT103':
            return self._generate_pacs008(enriched_data)
        elif mt_type == 'MT202':
            return self._generate_pacs009(enriched_data)
        else:
            return self._generate_generic(enriched_data, mt_type)
    
    def _generate_pacs008(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate pacs.008.001.08 - Customer Credit Transfer
        """
        # Build MX structure (simplified for POC)
        mx_structure = {
            'Document': {
                'FIToFICstmrCdtTrf': {
                    'GrpHdr': {},
                    'CdtTrfTxInf': {}
                }
            }
        }
        
        # Populate fields from enriched data
        for path, field_data in data.items():
            if path.startswith('_'):  # Skip metadata
                continue
                
            if not isinstance(field_data, dict):
                continue
            
            value = field_data.get('value')
            
            # Map to MX structure
            if 'GrpHdr' in path:
                field_name = path.split('.')[-1]
                mx_structure['Document']['FIToFICstmrCdtTrf']['GrpHdr'][field_name] = value
            elif 'CdtTrfTxInf' in path:
                field_name = path.split('.')[-1]
                mx_structure['Document']['FIToFICstmrCdtTrf']['CdtTrfTxInf'][field_name] = value
        
        # Generate XML representation
        xml_string = self._dict_to_xml(mx_structure)
        
        return {
            'mx_type': 'pacs.008',
            'version': '001.08',
            'structure': mx_structure,
            'xml': xml_string,
            'fields': data,
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }
    
    def _generate_pacs009(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate pacs.009.001.08 - Financial Institution Credit Transfer
        """
        mx_structure = {
            'Document': {
                'FIToFICstmrCdtTrf': {
                    'GrpHdr': {},
                    'CdtTrfTxInf': {}
                }
            }
        }
        
        # Populate from enriched data
        for path, field_data in data.items():
            if path.startswith('_'):
                continue
            if not isinstance(field_data, dict):
                continue
            
            value = field_data.get('value')
            field_name = path.split('.')[-1]
            
            if 'GrpHdr' in path:
                mx_structure['Document']['FIToFICstmrCdtTrf']['GrpHdr'][field_name] = value
            elif 'CdtTrfTxInf' in path:
                mx_structure['Document']['FIToFICstmrCdtTrf']['CdtTrfTxInf'][field_name] = value
        
        xml_string = self._dict_to_xml(mx_structure)
        
        return {
            'mx_type': 'pacs.009',
            'version': '001.08',
            'structure': mx_structure,
            'xml': xml_string,
            'fields': data,
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }
    
    def _generate_generic(self, data: Dict[str, Any], mt_type: str) -> Dict[str, Any]:
        """Generic MX generation"""
        return {
            'mx_type': 'pacs.XXX',
            'fields': data,
            'generated_at': datetime.utcnow().isoformat() + 'Z'
        }
    
    def _dict_to_xml(self, data: Dict[str, Any], root_name: str = 'Document') -> str:
        """
        Convert dictionary to XML string (simplified)
        In production, use proper ISO 20022 XML schemas
        """
        def build_element(parent, data_dict):
            for key, value in data_dict.items():
                child = ET.SubElement(parent, key)
                if isinstance(value, dict):
                    build_element(child, value)
                else:
                    child.text = str(value) if value is not None else ''
        
        root = ET.Element(root_name, attrib={
            'xmlns': 'urn:iso:std:iso:20022:tech:xsd:pacs.008.001.08',
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        })
        
        build_element(root, data)
        
        # Convert to string
        xml_bytes = ET.tostring(root, encoding='utf-8', method='xml')
        return xml_bytes.decode('utf-8')
