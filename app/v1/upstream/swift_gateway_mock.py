"""
Mock SWIFT Gateway - Simulates upstream SWIFT FIN messages
"""

import random
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class SWIFTGateway:
    """
    Mock SWIFT Gateway that generates sample MT messages
    Simulates receiving messages from SWIFT network
    """
    
    def __init__(self):
        self.message_templates = self._load_templates()
        logger.info("🌐 SWIFT Gateway Mock initialized")
    
    def _load_templates(self) -> Dict[str, List[str]]:
        """Load MT message templates"""
        return {
            'MT103': [
                """:20:REFERENCE001
:32A:241023USD50000.00
:50K:/US12345678901234567890
John Smith Corp
123 Main Street
New York, NY 10001
:59:/DE89370400440532013000
ABC GmbH
456 Market Strasse
Frankfurt 60311
:70:Invoice INV-2024-1234
Payment for services rendered
:71A:SHA""",
                """:20:REFERENCE002
:32A:241024EUR25000.00
:50K:/GB82WEST12345698765432
Tech Solutions Ltd
789 Oxford Street
London W1D 2HG
:59:/FR1420041010050500013M02606
Paris Trading SA
12 Rue de la Paix
Paris 75002
:70:Contract payment Q4-2024
Consulting services
:71A:OUR""",
                """:20:REFERENCE003
:32A:241025USD100000.00
:50K:/US98765432109876543210
Global Imports Inc
555 Commerce Blvd
Los Angeles, CA 90001
:59:/JP1234567890123456789012
Tokyo Exports KK
10-1 Shibuya
Tokyo 150-0002
:70:Purchase order PO-2024-5678
Electronic components
:71A:BEN"""
            ],
            'MT202': [
                """:20:FIREF001
:32A:241023USD250000.00
:53B:/US87654321098765432109
CHASUS33XXX
JPMorgan Chase Bank
:58A:DEUTDEFFXXX""",
                """:20:FIREF002
:32A:241024EUR150000.00
:53B:/GB12345678901234567890
HSBCGB2LXXX
HSBC Bank PLC
:58A:BNPAFRPPXXX"""
            ]
        }
    
    def receive_messages(self, count: int = 3) -> List[Dict[str, Any]]:
        """
        Simulate receiving MT messages from SWIFT network
        """
        messages = []
        
        for i in range(count):
            # Randomly select MT103 or MT202
            msg_type = random.choice(['MT103', 'MT202'])
            templates = self.message_templates[msg_type]
            raw_message = random.choice(templates)
            
            message = {
                'message_id': f'SWIFT-{msg_type}-{i+1:04d}',
                'type': msg_type,
                'raw_message': raw_message,
                'received_at': '2024-10-23T12:00:00Z',
                'sender_bic': self._extract_sender_bic(raw_message),
                'receiver_bic': 'TESTUS33XXX',
                'priority': random.choice(['HIGH', 'NORMAL', 'LOW'])
            }
            
            messages.append(message)
            logger.info(f"📨 Received {msg_type} message: {message['message_id']}")
        
        return messages
    
    def _extract_sender_bic(self, raw_message: str) -> str:
        """Extract sender BIC from message (simplified)"""
        # In a real implementation, this would parse the SWIFT envelope
        bics = ['CHASUS33XXX', 'CITIUS33XXX', 'HSBCGB2LXXX', 'DEUTDEFFXXX']
        return random.choice(bics)
    
    def send_message(self, mx_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate sending MX message to SWIFT network
        """
        logger.info(f"📤 Sending {mx_message['mx_type']} message to SWIFT network")
        
        return {
            'status': 'sent',
            'swift_reference': f"SWIFT-OUT-{random.randint(1000, 9999)}",
            'sent_at': '2024-10-23T12:00:01Z',
            'acknowledgement': 'ACK',
            'charges': self._calculate_swift_charges(mx_message)
        }
    
    def _calculate_swift_charges(self, mx_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate SWIFT messaging charges
        Shows cost savings of native MX vs translated MT
        """
        base_fee = 0.50  # Base fee per message
        
        # Native MX = standard fee
        # Translated MT would be higher
        return {
            'base_fee': base_fee,
            'total': base_fee,
            'currency': 'USD',
            'charge_type': 'STANDARD_MX',
            'note': 'Native MX format - no translation surcharge'
        }
