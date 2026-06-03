"""
Utility functions and sample data
"""

from typing import List
from models import SampleMessage


def get_sample_messages() -> List[SampleMessage]:
    """Get sample MT103 messages for demo"""
    return [
        SampleMessage(
            id="MT103-001",
            name="Standard USD Transfer",
            description="Corporate payment to trading partner",
            currency="USD",
            amount="50,000.00",
            message=""":20:TRX2024112001
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
        ),
        SampleMessage(
            id="MT103-002",
            name="High Value EUR Transfer",
            description="Manufacturing equipment payment",
            currency="EUR",
            amount="2,500,000.00",
            message=""":20:TRX2024112002
:23B:CRED
:32A:241118EUR2500000,00
:50K:/DE89370400440532013000
DEUTSCHE MANUFACTURING GMBH
:52A:DEUTDEFFXXX
:59:/GB82WEST12345698765432
BRITISH IMPORTS PLC
:70:CONTRACT CON-2024-5678
:71A:OUR"""
        )
    ]


def format_duration(ms: int) -> str:
    """Format duration in human-readable format"""
    if ms < 1000:
        return f"{ms}ms"
    elif ms < 60000:
        return f"{ms/1000:.1f}s"
    else:
        return f"{ms/60000:.1f}m"
