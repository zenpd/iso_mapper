"""MT message parser — extracts fields from SWIFT MT messages.

Responsible for parsing raw SWIFT MT message text and extracting structured fields.
Implements SWIFT MT message structure knowledge.
"""
from __future__ import annotations

from api.schemas import ParsedMTMessage
from shared.logger import get_logger

log = get_logger("services.mt_parser")


class MTParser:
    """Parser for SWIFT MT messages."""

    async def parse(self, raw_message: str) -> ParsedMTMessage:
        """Parse raw SWIFT MT message.
        
        Args:
            raw_message: Raw SWIFT MT message text
        
        Returns:
            ParsedMTMessage with extracted fields
        """
        log.info("mt_parser.parse_started")

        # TODO: Implement actual MT parsing logic
        # For now, return placeholder

        parsed = ParsedMTMessage(
            message_id="msg-001",
            message_type="MT103",
            mx_equivalent="pacs.008",
            fields={},
            field_count=0,
            raw=raw_message,
        )

        log.info("mt_parser.parse_complete", field_count=parsed.field_count)
        return parsed
