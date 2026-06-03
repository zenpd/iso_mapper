"""
LLM Service
Azure OpenAI integration with retry logic and error handling
"""

import logging
from typing import Optional, Dict, Any
from openai import AzureOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Azure OpenAI LLM service for semantic understanding and inference
    """
    
    def __init__(self):
        self.client: Optional[AzureOpenAI] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Azure OpenAI client if configured"""
        if settings.is_llm_configured:
            try:
                self.client = AzureOpenAI(
                    azure_endpoint=settings.azure_openai_endpoint,
                    api_key=settings.azure_api_key,
                    api_version=settings.azure_api_version
                )
                logger.info("✅ Azure OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Azure OpenAI: {e}")
                self.client = None
        else:
            logger.warning("⚠️ Azure OpenAI not configured - LLM features disabled")
    
    @property
    def is_available(self) -> bool:
        """Check if LLM service is available"""
        return self.client is not None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2000
    ) -> str:
        """
        Get completion from Azure OpenAI
        """
        if not self.is_available:
            raise RuntimeError("LLM service not available")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = self.client.chat.completions.create(
                model=settings.chat_llm_deployment,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM completion error: {e}")
            raise
    
    async def analyze_field_mapping(
        self,
        mt_field: str,
        mt_value: Any,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use LLM to analyze and map an MT field to MX path
        """
        system_prompt = """You are an expert in ISO 20022 message transformation.
Your task is to map SWIFT MT fields to ISO 20022 MX paths.
Respond in JSON format with: mx_path, confidence (0-1), reasoning."""

        prompt = f"""Analyze this MT field and suggest the appropriate MX mapping:

Field Name: {mt_field}
Field Value: {mt_value}
Message Type: {context.get('message_type', 'MT103')}
Target MX Type: {context.get('mx_type', 'pacs.008')}

Provide the MX path mapping in JSON format:
{{
    "mx_path": "path.to.field",
    "confidence": 0.95,
    "reasoning": "explanation"
}}"""

        try:
            response = await self.complete(prompt, system_prompt)
            import json
            # Clean response and parse JSON
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            return json.loads(response)
        except Exception as e:
            logger.error(f"Field mapping analysis failed: {e}")
            return {
                "mx_path": "CdtTrfTxInf.RmtInf.Ustrd",
                "confidence": 0.5,
                "reasoning": f"Fallback mapping due to error: {str(e)}"
            }
    
    async def enrich_party_data(
        self,
        party_info: str,
        party_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use LLM to extract and enrich party information
        """
        system_prompt = """You are an expert in payment message processing.
Extract structured party information from the provided text.
Respond in JSON format."""

        prompt = f"""Extract structured information for this {party_type}:

Raw Data:
{party_info}

Currency: {context.get('currency', 'USD')}

Provide structured data in JSON format:
{{
    "name": "Party Name",
    "account": "Account Number",
    "address": {{
        "street": "Street",
        "city": "City",
        "country": "Country Code"
    }},
    "confidence": 0.95
}}"""

        try:
            response = await self.complete(prompt, system_prompt)
            import json
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            return json.loads(response)
        except Exception as e:
            logger.error(f"Party enrichment failed: {e}")
            return {"name": party_info.split('\n')[0] if party_info else "", "confidence": 0.5}
    
    async def validate_contextually(
        self,
        mx_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Use LLM for contextual validation beyond schema rules
        """
        system_prompt = """You are an expert in payment compliance and validation.
Analyze the transaction data for potential issues, anomalies, or compliance concerns.
Respond in JSON format with warnings and recommendations."""

        prompt = f"""Analyze this MX transaction data for potential issues:

Transaction Type: {context.get('mx_type', 'pacs.008')}
Currency: {context.get('currency', 'USD')}
Amount: {context.get('amount', 'Unknown')}

Data Summary:
- Debtor fields: {len([k for k in mx_data.keys() if 'Dbtr' in k])}
- Creditor fields: {len([k for k in mx_data.keys() if 'Cdtr' in k])}
- Total fields: {len(mx_data)}

Provide analysis in JSON format:
{{
    "warnings": [
        {{"type": "warning_type", "message": "description", "confidence": 0.8}}
    ],
    "recommendations": ["recommendation1", "recommendation2"],
    "risk_score": 0.2
}}"""

        try:
            response = await self.complete(prompt, system_prompt)
            import json
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            return json.loads(response)
        except Exception as e:
            logger.error(f"Contextual validation failed: {e}")
            return {"warnings": [], "recommendations": [], "risk_score": 0.0}


# Singleton instance
llm_service = LLMService()
