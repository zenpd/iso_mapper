// TypeScript type definitions for API responses.

export type TransformationApproach = 'rules' | 'llm' | 'hybrid'
export type TransformationDirection = 'mt_to_iso' | 'iso_to_mt'

export interface TransformationRequest {
  mt_message: string
  approach: TransformationApproach
  message_id?: string
  direction?: TransformationDirection
}

export interface StatisticsData {
  total_duration_ms: number
  fields_parsed: number
  fields_mapped: number
  fields_enriched: number
  overall_confidence: number
  validation_score: number
  errors: number
  warnings: number
}

export interface TransformationResponse {
  success: boolean
  message_id: string
  mt_type: string
  mx_type: string
  approach_used: string
  parsed_mt: Record<string, any>
  mx_structure: Record<string, any>
  mx_xml: string
  agent_results: Record<string, Record<string, any>>
  statistics: StatisticsData
  timestamp: string
  error?: string
}

export interface SampleMessage {
  id: string
  name: string
  description: string
  message: string
  currency: string
  amount: string
}

export interface HealthResponse {
  status: string
  timestamp: string
  components: Record<string, string>
}

export interface ValidationResult {
  is_compliant: boolean
  direction: string
  compliance_score: number
  correct_mappings: string[]
  missing_fields: string[]
  validation_errors: string[]
  suggested_fixes: string[]
}

export interface ConfigResponse {
  default_approach: string
  llm_configured: boolean
  llm_model?: string
  cache_enabled: boolean
  log_level: string
  app_env: string
}
