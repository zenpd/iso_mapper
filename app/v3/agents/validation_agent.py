"""
Validation Agent
AI-powered schema and contextual validation for MX messages
"""

import logging
import random
from datetime import datetime
from typing import Dict, Any, List

from models import (
    EnrichmentResult, ValidationResult, ValidationError, MappedField,
    AgentResult, AgentStatus, TransformationApproach
)
from services.llm_service import llm_service

logger = logging.getLogger(__name__)


class ValidationAgent:
    """
    Agent responsible for validating MX messages
    Performs schema validation and AI-powered contextual analysis
    """
    
    def __init__(self):
        self.name = "Validation Agent"
        self._load_schema_rules()
        logger.info(f"🤖 {self.name} initialized with ISO 20022 schemas")
    
    def _load_schema_rules(self):
        """Load ISO 20022 XSD schema rules"""
        self.mandatory_fields = {
            'pacs.008': [
                'GrpHdr.MsgId',
                'GrpHdr.CreDtTm',
                'GrpHdr.NbOfTxs',
                'CdtTrfTxInf.PmtId.EndToEndId',
                'CdtTrfTxInf.IntrBkSttlmAmt.Ccy',
                'CdtTrfTxInf.IntrBkSttlmAmt.Value',
                'CdtTrfTxInf.IntrBkSttlmDt'
            ],
            'pacs.009': [
                'GrpHdr.MsgId',
                'GrpHdr.CreDtTm',
                'CdtTrfTxInf.PmtId.InstrId'
            ]
        }
        
        self.field_constraints = {
            'GrpHdr.MsgId': {
                'max_length': 35,
                'pattern': r'^[A-Za-z0-9/\-?:().,\'+\s]{1,35}$',
                'description': 'Message ID'
            },
            'GrpHdr.CreDtTm': {
                'format': 'ISO8601',
                'description': 'Creation DateTime'
            },
            'CdtTrfTxInf.IntrBkSttlmAmt.Value': {
                'type': 'decimal',
                'max_digits': 18,
                'decimal_places': 5,
                'description': 'Settlement Amount'
            },
            'CdtTrfTxInf.IntrBkSttlmAmt.Ccy': {
                'type': 'currency_code',
                'length': 3,
                'description': 'Currency Code'
            },
            'CdtTrfTxInf.ChrgBr': {
                'enum': ['DEBT', 'CRED', 'SHAR', 'SLEV'],
                'description': 'Charge Bearer'
            }
        }
    
    async def validate(
        self,
        enrichment_result: EnrichmentResult,
        mx_type: str,
        approach: TransformationApproach
    ) -> tuple[ValidationResult, AgentResult]:
        """
        Validate MX message against schema and perform contextual analysis
        """
        start_time = datetime.utcnow()
        
        try:
            errors: List[ValidationError] = []
            warnings: List[ValidationError] = []
            auto_corrections = []
            
            data = enrichment_result.enriched_data
            
            # Schema validation
            schema_errors = await self._validate_schema(data, mx_type)
            errors.extend(schema_errors)
            
            # Constraint validation
            constraint_errors = await self._validate_constraints(data)
            errors.extend(constraint_errors)
            
            # Contextual validation (AI-powered)
            if approach in [TransformationApproach.LLM, TransformationApproach.HYBRID]:
                contextual_warnings = await self._contextual_validation(data, mx_type)
                warnings.extend(contextual_warnings)
            
            # Business rule validation
            business_warnings = await self._validate_business_rules(data)
            warnings.extend(business_warnings)
            
            # Generate auto-corrections
            if errors or warnings:
                auto_corrections = await self._generate_auto_corrections(errors, warnings, data)
            
            # Calculate compliance score
            compliance_score = self._calculate_compliance_score(errors, warnings)
            is_valid = len(errors) == 0
            
            result = ValidationResult(
                is_valid=is_valid,
                compliance_score=compliance_score,
                errors=errors,
                warnings=warnings,
                auto_corrections=auto_corrections
            )
            
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            status = AgentStatus.COMPLETE if is_valid else AgentStatus.WARNING
            message = f"Validation {'passed' if is_valid else 'completed with issues'} - Score: {compliance_score:.0f}%"
            
            agent_result = AgentResult(
                agent_name=self.name,
                status=status,
                message=message,
                confidence=compliance_score / 100,
                fields_processed=len(self.mandatory_fields.get(mx_type, [])),
                duration_ms=duration,
                details={
                    "error_count": len(errors),
                    "warning_count": len(warnings),
                    "auto_corrections": len(auto_corrections)
                }
            )
            
            logger.info(f"{'✅' if is_valid else '⚠️'} {self.name}: Score {compliance_score:.0f}%")
            return result, agent_result
            
        except Exception as e:
            duration = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            logger.error(f"❌ {self.name} error: {e}")
            
            agent_result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.ERROR,
                message=f"Validation error: {str(e)}",
                duration_ms=duration
            )
            raise
    
    async def _validate_schema(self, data: Dict[str, MappedField], mx_type: str) -> List[ValidationError]:
        """Check mandatory fields are present"""
        errors = []
        mandatory = self.mandatory_fields.get(mx_type, [])
        
        for required_field in mandatory:
            found = any(
                required_field in path or path.endswith(required_field.split('.')[-1])
                for path in data.keys()
            )
            
            if not found:
                errors.append(ValidationError(
                    error_type='missing_mandatory_field',
                    field=required_field,
                    message=f'Mandatory field {required_field} is missing',
                    severity='error',
                    suggestion=self._get_field_suggestion(required_field)
                ))
        
        return errors
    
    async def _validate_constraints(self, data: Dict[str, MappedField]) -> List[ValidationError]:
        """Validate field-level constraints"""
        errors = []
        
        for path, field_data in data.items():
            if not isinstance(field_data, MappedField):
                continue
            
            value = field_data.value
            
            # Check constraints for this field
            for constraint_path, rules in self.field_constraints.items():
                if constraint_path in path or path.endswith(constraint_path.split('.')[-1]):
                    
                    # Length validation
                    if 'max_length' in rules and isinstance(value, str):
                        if len(value) > rules['max_length']:
                            errors.append(ValidationError(
                                error_type='constraint_violation',
                                field=path,
                                message=f"{rules['description']} exceeds maximum length of {rules['max_length']}",
                                severity='error',
                                suggestion=f"Truncate to {rules['max_length']} characters"
                            ))
                    
                    # Currency code validation
                    if rules.get('type') == 'currency_code':
                        if not isinstance(value, str) or len(value) != 3:
                            errors.append(ValidationError(
                                error_type='constraint_violation',
                                field=path,
                                message='Currency code must be exactly 3 characters',
                                severity='error'
                            ))
                    
                    # Enum validation
                    if 'enum' in rules and value not in rules['enum']:
                        errors.append(ValidationError(
                            error_type='invalid_enum_value',
                            field=path,
                            message=f"Invalid value '{value}'. Must be one of: {rules['enum']}",
                            severity='error'
                        ))
        
        return errors
    
    async def _contextual_validation(
        self,
        data: Dict[str, MappedField],
        mx_type: str
    ) -> List[ValidationError]:
        """AI-powered contextual validation"""
        warnings = []
        
        # LLM-based validation if available
        if llm_service.is_available:
            try:
                # Extract context for LLM
                context = {
                    'mx_type': mx_type,
                    'currency': None,
                    'amount': None
                }
                
                for path, field in data.items():
                    if isinstance(field, MappedField):
                        if 'Ccy' in path:
                            context['currency'] = field.value
                        elif 'Value' in path and 'Amt' in path:
                            context['amount'] = field.value
                
                result = await llm_service.validate_contextually(
                    {k: v.value if isinstance(v, MappedField) else v for k, v in data.items()},
                    context
                )
                
                for warning in result.get('warnings', []):
                    warnings.append(ValidationError(
                        error_type='contextual_warning',
                        field='transaction',
                        message=warning.get('message', 'AI detected potential issue'),
                        severity='warning'
                    ))
                    
            except Exception as e:
                logger.warning(f"LLM contextual validation failed: {e}")
        
        # Rule-based contextual checks
        # Check for unusually high amounts
        for path, field in data.items():
            if isinstance(field, MappedField) and 'Value' in path and 'Amt' in path:
                try:
                    amount = float(field.value)
                    if amount > 10000000:  # 10M threshold
                        warnings.append(ValidationError(
                            error_type='high_value_transaction',
                            field=path,
                            message=f'High value transaction ({amount:,.2f}) may require additional review',
                            severity='warning'
                        ))
                except (ValueError, TypeError):
                    pass
        
        return warnings
    
    async def _validate_business_rules(self, data: Dict[str, MappedField]) -> List[ValidationError]:
        """Validate business rules"""
        warnings = []
        
        # Check for missing creditor agent
        has_creditor_agent = any('CdtrAgt' in path for path in data.keys())
        if not has_creditor_agent:
            warnings.append(ValidationError(
                error_type='missing_recommended_field',
                field='CdtTrfTxInf.CdtrAgt',
                message='Creditor agent information is recommended for STP',
                severity='warning'
            ))
        
        return warnings
    
    def _calculate_compliance_score(self, errors: List[ValidationError], warnings: List[ValidationError]) -> float:
        """Calculate overall compliance score"""
        error_weight = 10
        warning_weight = 2
        
        deductions = len(errors) * error_weight + len(warnings) * warning_weight
        score = max(0, 100 - deductions)
        
        return score
    
    def _get_field_suggestion(self, field_path: str) -> str:
        """Get suggestion for missing field"""
        suggestions = {
            'GrpHdr.MsgId': 'Generate unique message ID with timestamp',
            'GrpHdr.CreDtTm': 'Use current UTC timestamp in ISO 8601 format',
            'CdtTrfTxInf.PmtId.EndToEndId': 'Derive from transaction reference',
            'CdtTrfTxInf.IntrBkSttlmAmt.Ccy': 'Extract currency from MT field 32A',
            'CdtTrfTxInf.IntrBkSttlmAmt.Value': 'Extract amount from MT field 32A',
            'CdtTrfTxInf.IntrBkSttlmDt': 'Use value date from MT field 32A'
        }
        return suggestions.get(field_path, 'Review ISO 20022 documentation')
    
    async def _generate_auto_corrections(
        self,
        errors: List[ValidationError],
        warnings: List[ValidationError],
        data: Dict[str, MappedField]
    ) -> List[Dict[str, Any]]:
        """Generate automatic correction suggestions"""
        corrections = []
        
        for error in errors:
            if error.error_type == 'missing_mandatory_field':
                corrections.append({
                    'issue': error.message,
                    'auto_fix': 'available',
                    'action': error.suggestion or 'Add required field',
                    'confidence': 0.92,
                    'method': 'rule_based'
                })
            elif error.error_type == 'constraint_violation':
                corrections.append({
                    'issue': error.message,
                    'auto_fix': 'available',
                    'action': error.suggestion or 'Adjust field value',
                    'confidence': 1.0,
                    'method': 'rule_based'
                })
        
        return corrections
