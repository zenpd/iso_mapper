"""Compliance validation for MT103 and pacs.008 transformations.

Validates transformed messages against strict SWIFT MT103 and ISO 20022 standards.
"""
import re
from typing import Dict, List, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.schemas import TransformationRequest, TransformationResponse
from shared.logger import get_logger

router = APIRouter(prefix="/api/v1", tags=["Validation"])
log = get_logger("api.routers.validation")


class ValidationResult(BaseModel):
    """Validation result structure."""
    is_compliant: bool
    direction: str
    correct_mappings: List[str]
    missing_fields: List[str]
    validation_errors: List[str]
    suggested_fixes: List[str]
    compliance_score: float  # 0-100


class MT103Validator:
    """Validate MT103 messages against SWIFT standards."""

    VALID_CHARGES = ["BEN", "OUR", "SHA"]
    VALID_BANK_OPERATIONS = ["CRED", "SPAY", "CHQC", "DIVI", "CMSI"]
    ISO_CURRENCIES = {
        "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD", 
        "CNY", "INR", "MXN", "ZAR", "HKD", "SGD", "SEK", "NOK", "DKK"
    }

    def validate_mt103(self, mt_content: str) -> ValidationResult:
        """Validate MT103 message against SWIFT standards."""
        issues = {
            "correct_mappings": [],
            "missing_fields": [],
            "validation_errors": [],
            "suggested_fixes": []
        }

        # Extract fields
        fields = self._extract_mt103_fields(mt_content)

        # Check mandatory fields
        mandatory = [":20:", ":23B:", ":32A:", ":50", ":59", ":71A:"]
        for field in mandatory:
            if field not in mt_content:
                issues["missing_fields"].append(f"[SWIFT MT103] Mandatory field {field} is missing")
                issues["suggested_fixes"].append(f"[SWIFT] Add {field} field to MT103 message")

        # Validate :20: (Reference)
        if ":20:" in mt_content:
            ref = self._extract_field(mt_content, ":20:")
            if ref.startswith("/") or ref.endswith("/") or "//" in ref:
                issues["validation_errors"].append("[SWIFT MT103] :20: field must not start/end with / or contain //")
                issues["suggested_fixes"].append("[SWIFT] Remove leading/trailing / or double // from :20: field")
            else:
                issues["correct_mappings"].append("[SWIFT MT103] :20: (Sender's Reference) - Valid")

        # Validate :23B: (Bank Operation Code)
        if ":23B:" in mt_content:
            op_code = self._extract_field(mt_content, ":23B:")
            if op_code in self.VALID_BANK_OPERATIONS:
                issues["correct_mappings"].append(f"[SWIFT MT103] :23B: (Bank Operation Code) = {op_code} - Valid")
            else:
                issues["validation_errors"].append(f"[SWIFT MT103] :23B: code '{op_code}' is not standard SWIFT")
                issues["suggested_fixes"].append(f"[SWIFT] Use valid code from: {', '.join(self.VALID_BANK_OPERATIONS)}")

        # Validate :32A: (Value Date + Currency + Amount)
        if ":32A:" in mt_content:
            date_ccy_amt = self._extract_field(mt_content, ":32A:")
            # Format: YYMMDDCCCAMOUNT
            if len(date_ccy_amt) >= 10:
                date = date_ccy_amt[:6]
                currency = date_ccy_amt[6:9]
                amount = date_ccy_amt[9:]
                
                if not re.match(r'^\d{6}$', date):
                    issues["validation_errors"].append("[SWIFT MT103] :32A: date must be YYMMDD format")
                else:
                    issues["correct_mappings"].append(f"[SWIFT MT103] :32A: Date {date} - Valid format (YYMMDD)")
                
                if currency not in self.ISO_CURRENCIES:
                    issues["validation_errors"].append(f"[SWIFT MT103] :32A: currency '{currency}' is not valid ISO 4217")
                else:
                    issues["correct_mappings"].append(f"[SWIFT MT103] :32A: Currency {currency} - Valid ISO 4217")
                
                if not re.match(r'^\d+[,\.]\d{2}$', amount):
                    issues["validation_errors"].append(f"[SWIFT MT103] :32A: amount format invalid (should be decimal)")
                else:
                    issues["correct_mappings"].append(f"[SWIFT MT103] :32A: Amount {amount} - Valid format (decimal)")

        # Validate :50a: (Ordering Customer) - should have account and/or name
        if ":50" in mt_content:
            ordering = self._extract_field(mt_content, ":50")
            # Check if field has multiple lines (account on first, name on second)
            ordering_lines = [line.strip() for line in ordering.split('\n') if line.strip()]
            if len(ordering_lines) >= 1:
                # Has at least account/identifier
                issues["correct_mappings"].append("[SWIFT MT103] :50a: (Ordering Customer) - Present with Account/Name")
            else:
                issues["missing_fields"].append("[SWIFT MT103] :50a: must contain ordering customer account and name")
                issues["suggested_fixes"].append("[SWIFT] Add party account and name to :50a: field")

        # Validate :59a: (Beneficiary Customer) - should have account and/or name
        if ":59" in mt_content:
            beneficiary = self._extract_field(mt_content, ":59")
            # Check if field has multiple lines (account on first, name on second)
            beneficiary_lines = [line.strip() for line in beneficiary.split('\n') if line.strip()]
            if len(beneficiary_lines) >= 1:
                # Has at least account/identifier
                issues["correct_mappings"].append("[SWIFT MT103] :59a: (Beneficiary Customer) - Present with Account/Name")
            else:
                issues["missing_fields"].append("[SWIFT MT103] :59a: must contain beneficiary customer account and name")
                issues["suggested_fixes"].append("[SWIFT] Add party account and name to :59a: field")

        # Validate :71A: (Charges)
        if ":71A:" in mt_content:
            charge = self._extract_field(mt_content, ":71A:")
            if charge in self.VALID_CHARGES:
                issues["correct_mappings"].append(f"[SWIFT MT103] :71A: (Charges) = {charge} - Valid")
            else:
                issues["validation_errors"].append(f"[SWIFT MT103] :71A: charge '{charge}' must be one of {self.VALID_CHARGES}")
                issues["suggested_fixes"].append(f"[SWIFT] Change :71A: to one of: {', '.join(self.VALID_CHARGES)}")

        # Calculate compliance score
        total_checks = len(mandatory) + 5
        passed_checks = len(issues["correct_mappings"])
        compliance_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0

        is_compliant = len(issues["validation_errors"]) == 0 and len(issues["missing_fields"]) == 0

        return ValidationResult(
            is_compliant=is_compliant,
            direction="pacs.008_to_MT103",
            correct_mappings=issues["correct_mappings"],
            missing_fields=issues["missing_fields"],
            validation_errors=issues["validation_errors"],
            suggested_fixes=issues["suggested_fixes"],
            compliance_score=min(100, compliance_score)
        )

    def _extract_mt103_fields(self, mt_content: str) -> Dict[str, str]:
        """Extract all MT103 fields."""
        fields = {}
        pattern = r':(\d+[A-Z]?):(.*?)(?=:\d|$)'
        matches = re.findall(pattern, mt_content, re.DOTALL)
        for field_num, field_value in matches:
            fields[f":{field_num}:"] = field_value.strip()
        return fields

    def _extract_field(self, content: str, field_marker: str) -> str:
        """Extract specific field value - handles multi-line fields."""
        # For party fields like :50: and :59:, they can span multiple lines
        pattern = field_marker + r"(.*?)(?=:\d|-}|$)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            field_value = match.group(1).strip()
            # For party fields, keep everything including newlines but strip outer whitespace
            return field_value
        return ""


class Pacs008Validator:
    """Validate pacs.008 messages against ISO 20022 standards."""

    def validate_pacs008(self, xml_content: str) -> ValidationResult:
        """Validate pacs.008 XML against ISO 20022 standards."""
        issues = {
            "correct_mappings": [],
            "missing_fields": [],
            "validation_errors": [],
            "suggested_fixes": []
        }

        # Check for required XML elements (excluding Dbtr/Cdtr which need deeper validation)
        required_elements = [
            ("<MsgId>", "Message ID"),
            ("<CreDtTm>", "Creation Date/Time"),
            ("<NbOfTxs>", "Number of Transactions"),
            ("<IntrBkSttlmAmt>", "Interbank Settlement Amount"),
            ("<ChrgBr>", "Charge Bearer"),
        ]

        for element, description in required_elements:
            if element in xml_content:
                issues["correct_mappings"].append(f"[ISO 20022 pacs.008] {description} ({element}) - Present")
            else:
                issues["missing_fields"].append(f"[ISO 20022 pacs.008] Mandatory element {element} ({description}) is missing")
                issues["suggested_fixes"].append(f"[ISO] Add {element} element to pacs.008 XML structure")

        # Validate MsgId length (max 35)
        msg_id_match = re.search(r'<MsgId>(.*?)</MsgId>', xml_content)
        if msg_id_match:
            msg_id = msg_id_match.group(1)
            if len(msg_id) > 35:
                issues["validation_errors"].append(f"[ISO 20022 pacs.008] MsgId length {len(msg_id)} exceeds maximum of 35")
                issues["suggested_fixes"].append(f"[ISO] Truncate MsgId to 35 characters: {msg_id[:35]}")
            else:
                issues["correct_mappings"].append(f"[ISO 20022 pacs.008] MsgId length {len(msg_id)} - Valid (≤35)")

        # Validate NbOfTxs (numeric, <= 15 digits)
        nbofo_match = re.search(r'<NbOfTxs>(\d+)</NbOfTxs>', xml_content)
        if nbofo_match:
            nbtxs = nbofo_match.group(1)
            if len(nbtxs) <= 15 and nbtxs.isdigit():
                issues["correct_mappings"].append(f"[ISO 20022 pacs.008] NbOfTxs = {nbtxs} - Valid (≤15 digits)")
            else:
                issues["validation_errors"].append(f"[ISO 20022 pacs.008] NbOfTxs '{nbtxs}' must be numeric and <= 15 digits")

        # Validate ChrgBr (must be SHAR, DEBT, or CRED)
        chrgbr_match = re.search(r'<ChrgBr>(.*?)</ChrgBr>', xml_content)
        if chrgbr_match:
            chrgbr = chrgbr_match.group(1)
            valid_chrgbr = ["SHAR", "DEBT", "CRED", "SLEV"]
            if chrgbr in valid_chrgbr:
                issues["correct_mappings"].append(f"[ISO 20022 pacs.008] ChrgBr = {chrgbr} - Valid")
            else:
                issues["validation_errors"].append(f"[ISO 20022 pacs.008] ChrgBr '{chrgbr}' must be one of {valid_chrgbr}")
                issues["suggested_fixes"].append(f"[ISO] Use valid ChrgBr: {', '.join(valid_chrgbr)}")

        # Validate Debtor structure (must have Nm)
        if "<Dbtr>" in xml_content:
            # Extract Debtor section specifically
            dbtr_match = re.search(r'<Dbtr>(.*?)</Dbtr>', xml_content, re.DOTALL)
            if dbtr_match:
                dbtr_content = dbtr_match.group(1)
                if "<Nm>" in dbtr_content and "</Nm>" in dbtr_content:
                    nm_match = re.search(r'<Nm>(.*?)</Nm>', dbtr_content)
                    if nm_match and nm_match.group(1).strip():
                        issues["correct_mappings"].append("[ISO 20022 pacs.008] Debtor Name (<Nm>) - Present")
                    else:
                        issues["missing_fields"].append("[ISO 20022 pacs.008] Debtor Name (<Nm>) is empty")
                        issues["suggested_fixes"].append("[ISO] Populate the <Nm> element with debtor name within <Dbtr> section")
                else:
                    issues["missing_fields"].append("[ISO 20022 pacs.008] Debtor must include Name (<Nm>)")
                    issues["suggested_fixes"].append("[ISO] Add <Nm> element within <Dbtr> section")
            else:
                issues["missing_fields"].append("[ISO 20022 pacs.008] Debtor structure is malformed")
                issues["suggested_fixes"].append("[ISO] Ensure <Dbtr> element is properly closed with </Dbtr>")

        # Validate Creditor structure (must have Nm)
        if "<Cdtr>" in xml_content:
            # Extract Creditor section specifically
            cdtr_match = re.search(r'<Cdtr>(.*?)</Cdtr>', xml_content, re.DOTALL)
            if cdtr_match:
                cdtr_content = cdtr_match.group(1)
                if "<Nm>" in cdtr_content and "</Nm>" in cdtr_content:
                    nm_match = re.search(r'<Nm>(.*?)</Nm>', cdtr_content)
                    if nm_match and nm_match.group(1).strip():
                        issues["correct_mappings"].append("[ISO 20022 pacs.008] Creditor Name (<Nm>) - Present")
                    else:
                        issues["missing_fields"].append("[ISO 20022 pacs.008] Creditor Name (<Nm>) is empty")
                        issues["suggested_fixes"].append("[ISO] Populate the <Nm> element with creditor name within <Cdtr> section")
                else:
                    issues["missing_fields"].append("[ISO 20022 pacs.008] Creditor must include Name (<Nm>)")
                    issues["suggested_fixes"].append("[ISO] Add <Nm> element within <Cdtr> section")
            else:
                issues["missing_fields"].append("[ISO 20022 pacs.008] Creditor structure is malformed")
                issues["suggested_fixes"].append("[ISO] Ensure <Cdtr> element is properly closed with </Cdtr>")

        # Calculate compliance score
        total_checks = len(required_elements) + 7  # MsgId length, NbOfTxs, ChrgBr, Dbtr Name, Cdtr Name + other checks
        passed_checks = len(issues["correct_mappings"])
        compliance_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0

        is_compliant = len(issues["validation_errors"]) == 0 and len(issues["missing_fields"]) == 0

        return ValidationResult(
            is_compliant=is_compliant,
            direction="MT103_to_pacs.008",
            correct_mappings=issues["correct_mappings"],
            missing_fields=issues["missing_fields"],
            validation_errors=issues["validation_errors"],
            suggested_fixes=issues["suggested_fixes"],
            compliance_score=min(100, compliance_score)
        )


@router.post("/validate-transformation")
async def validate_transformation(request: TransformationRequest) -> ValidationResult:
    """Validate transformation for SWIFT MT103 and ISO 20022 compliance.
    
    Uses explicit direction if provided, otherwise auto-detects format.
    """
    
    log.info("validation_requested", message_id=request.message_id, direction=request.direction)
    
    try:
        # Determine direction: use explicit parameter if provided, otherwise auto-detect
        direction = request.direction
        
        if not direction:
            # Auto-detect format based on message content
            direction = _detect_format(request.mt_message)
        
        if direction == "iso_to_mt":
            # Output is MT103 (ISO→MT transformation)
            validator = MT103Validator()
            result = validator.validate_mt103(request.mt_message)
            result.direction = "ISO 20022 → SWIFT MT103"
        else:
            # Output is pacs.008 XML (MT→ISO transformation)
            validator = Pacs008Validator()
            result = validator.validate_pacs008(request.mt_message)
            result.direction = "SWIFT MT103 → ISO 20022"
        
        log.info("validation_complete", message_id=request.message_id, compliant=result.is_compliant, direction=result.direction)
        return result
    
    except Exception as e:
        log.error("validation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


def _detect_format(message: str) -> str:
    """Auto-detect if message is MT103 format or ISO 20022 XML format.
    
    Returns:
        "iso_to_mt" if MT103 format is detected
        "mt_to_iso" if XML format is detected
    """
    message_stripped = message.strip()
    
    # Check for MT103 indicators
    mt_indicators = [
        message_stripped.startswith('{1:'),  # Standard MT103 start
        ':20:' in message_stripped,           # MT103 field marker
        message_stripped.startswith('{'),     # SWIFT envelope start
        '-}' in message_stripped,             # SWIFT envelope end
    ]
    
    # Check for XML/pacs.008 indicators
    xml_indicators = [
        message_stripped.startswith('<'),     # XML tag start
        message_stripped.startswith('<?xml'), # XML declaration
        '<CstmrCdtTrfInitn>' in message_stripped,  # pacs.008 root element
        '<MsgId>' in message_stripped,        # pacs.008 message ID
        '<Dbtr>' in message_stripped,         # pacs.008 debtor
        '</MsgId>' in message_stripped,       # XML closing tag
    ]
    
    mt_score = sum(mt_indicators)
    xml_score = sum(xml_indicators)
    
    # Determine format based on scoring
    if xml_score > mt_score:
        return "mt_to_iso"  # XML format → from MT to ISO
    else:
        return "iso_to_mt"  # MT format → from ISO to MT
