import React from 'react'
import { TransformationResponse, ValidationResult } from '@/types/api'
import { Card } from '@/components/common'
import { CheckCircle, AlertCircle, Copy } from 'lucide-react'
import { apiClient } from '@/services/api'

export function TransformationResult({ result, direction = 'mt_to_iso' }: { result: TransformationResponse; direction?: 'mt_to_iso' | 'iso_to_mt' }) {
  const [copied, setCopied] = React.useState(false)
  const [validation, setValidation] = React.useState<ValidationResult | null>(null)
  const [validationLoading, setValidationLoading] = React.useState(false)

  React.useEffect(() => {
    // Auto-validate transformation output
    const validateOutput = async () => {
      try {
        setValidationLoading(true)
        const validationResult = await apiClient.validateTransformation({
          message_id: result.message_id,
          mt_message: result.mx_xml,
          approach: 'rules',
          direction: direction,
        })
        setValidation(validationResult)
      } catch (error) {
        console.error('Validation failed:', error)
      } finally {
        setValidationLoading(false)
      }
    }

    if (result.success && result.mx_xml) {
      validateOutput()
    }
  }, [result.message_id, result.mx_xml, result.success, direction])

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const isMtToIso = direction === 'mt_to_iso'
  const outputTitle = isMtToIso ? 'ISO 20022 MX Output (XML)' : 'SWIFT MT103 Output'
  const conversionArrow = isMtToIso ? '→' : '←'

  return (
    <div className="space-y-4">
      {/* Header */}
      <Card variant="elevated">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-2">
              {result.success ? (
                <>
                  <CheckCircle className="w-6 h-6 text-green-600" />
                  <h3 className="text-lg font-semibold text-green-600">Transformation Successful</h3>
                </>
              ) : (
                <>
                  <AlertCircle className="w-6 h-6 text-red-600" />
                  <h3 className="text-lg font-semibold text-red-600">Transformation Failed</h3>
                </>
              )}
            </div>
            <p className="text-sm text-gray-600">Message ID: {result.message_id}</p>
          </div>
          <div className="text-right">
            <p className="text-sm font-mono text-gray-600">
              {isMtToIso ? `${result.mt_type} ${conversionArrow} ${result.mx_type}` : `${result.mx_type} ${conversionArrow} ${result.mt_type}`}
            </p>
            <p className="text-xs text-gray-500 mt-1">{result.approach_used}</p>
          </div>
        </div>
      </Card>

      {/* Statistics */}
      <Card title="Transformation Statistics">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatItem label="Duration" value={`${result.statistics.total_duration_ms}ms`} />
          <StatItem label="Fields Parsed" value={result.statistics.fields_parsed} />
          <StatItem label="Fields Mapped" value={result.statistics.fields_mapped} />
          <StatItem label="Fields Enriched" value={result.statistics.fields_enriched} />
          <StatItem label="Confidence" value={`${(result.statistics.overall_confidence < 1 ? result.statistics.overall_confidence * 100 : result.statistics.overall_confidence).toFixed(0)}%`} />
          <StatItem label="Validation Score" value={`${(result.statistics.validation_score < 1 ? result.statistics.validation_score * 100 : result.statistics.validation_score).toFixed(0)}%`} />
          <StatItem label="Errors" value={result.statistics.errors} />
          <StatItem label="Warnings" value={result.statistics.warnings} />
        </div>
      </Card>

      {/* Input Data */}
      <Card title={isMtToIso ? "Parsed SWIFT MT Message" : "Parsed ISO 20022 XML"}>
        <div className="space-y-2">
          <p className="text-sm text-gray-600">{isMtToIso ? `Message Type: ${result.mt_type}` : 'Format: pacs.008'}</p>
          <div className="bg-gray-50 p-3 rounded border border-gray-200 max-h-96 overflow-y-auto">
            <pre className="text-xs font-mono whitespace-pre-wrap break-words">
              {JSON.stringify(result.parsed_mt, null, 2)}
            </pre>
          </div>
        </div>
      </Card>

      {/* Output */}
      <Card title={outputTitle}>
        <div className="space-y-3">
          <button
            onClick={() => copyToClipboard(result.mx_xml)}
            className="flex items-center gap-2 text-sm text-purple-600 hover:text-purple-700"
          >
            <Copy className="w-4 h-4" />
            {copied ? 'Copied!' : `Copy ${isMtToIso ? 'XML' : 'MT103'}`}
          </button>
          <div className="bg-gray-50 p-3 rounded border border-gray-200 overflow-auto" style={{ maxHeight: '600px' }}>
            <pre className="text-xs font-mono whitespace-pre-wrap break-words">
              {result.mx_xml}
            </pre>
          </div>
        </div>
      </Card>

      {/* Compliance Validation */}
      {validation && (
        <Card title={`SWIFT/ISO Compliance Validation ${validationLoading ? '(Loading...)' : ''}`} variant="elevated">
          <div className="space-y-4">
            {/* Compliance Status */}
            <div className="grid grid-cols-2 gap-4">
              <div className="border-l-4 p-3 rounded" style={{ borderColor: validation.is_compliant ? '#16a34a' : '#dc2626', backgroundColor: validation.is_compliant ? '#f0fdf4' : '#fef2f2' }}>
                <p className="text-xs text-gray-600 mb-1">Compliance Status</p>
                <p className="text-lg font-bold" style={{ color: validation.is_compliant ? '#16a34a' : '#dc2626' }}>
                  {validation.is_compliant ? '✓ COMPLIANT' : '✗ NON-COMPLIANT'}
                </p>
              </div>
              <div className="border-l-4 border-blue-500 p-3 rounded bg-blue-50">
                <p className="text-xs text-gray-600 mb-1">Compliance Score</p>
                <p className="text-lg font-bold text-blue-600">{validation.compliance_score.toFixed(2)}%</p>
              </div>
            </div>

            {/* Correct Mappings */}
            {validation.correct_mappings.length > 0 && (
              <div>
                <p className="text-sm font-semibold text-green-700 mb-2">✓ Correct Mappings ({validation.correct_mappings.length})</p>
                <ul className="space-y-1">
                  {validation.correct_mappings.map((mapping, i) => (
                    <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                      <span className="text-green-600 mt-0.5">✓</span>
                      <span>{mapping}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Missing Fields */}
            {validation.missing_fields.length > 0 && (
              <div>
                <p className="text-sm font-semibold text-orange-700 mb-2">⚠ Missing Fields ({validation.missing_fields.length})</p>
                <ul className="space-y-1">
                  {validation.missing_fields.map((field, i) => (
                    <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                      <span className="text-orange-600 mt-0.5">⚠</span>
                      <span>{field}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Validation Errors */}
            {validation.validation_errors.length > 0 && (
              <div>
                <p className="text-sm font-semibold text-red-700 mb-2">✗ Validation Errors ({validation.validation_errors.length})</p>
                <ul className="space-y-1">
                  {validation.validation_errors.map((error, i) => (
                    <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                      <span className="text-red-600 mt-0.5">✗</span>
                      <span>{error}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Suggested Fixes */}
            {validation.suggested_fixes.length > 0 && (
              <div>
                <p className="text-sm font-semibold text-blue-700 mb-2">🔧 Suggested Fixes ({validation.suggested_fixes.length})</p>
                <ul className="space-y-1">
                  {validation.suggested_fixes.map((fix, i) => (
                    <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                      <span className="text-blue-600 mt-0.5">•</span>
                      <span>{fix}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Direction Info */}
            <p className="text-xs text-gray-500 pt-2 border-t border-gray-200">
              Validation Direction: <span className="font-mono font-semibold">{validation.direction}</span>
            </p>
          </div>
        </Card>
      )}

      {/* Structure (only for MT→ISO) */}
      {isMtToIso && (
        <Card title="MX Structure (JSON)">
          <div className="bg-gray-50 p-3 rounded border border-gray-200 max-h-96 overflow-auto">
            <pre className="text-xs font-mono whitespace-pre-wrap break-words">
              {JSON.stringify(result.mx_structure, null, 2)}
            </pre>
          </div>
        </Card>
      )}
    </div>
  )
}

function StatItem({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="text-center">
      <p className="text-xs text-gray-600 mb-1">{label}</p>
      <p className="text-lg font-semibold text-gray-900">{value}</p>
    </div>
  )
}
