import React from 'react'
import { TransformationResponse } from '@/types/api'
import { Card } from '@/components/common'
import { CheckCircle, AlertCircle, Copy } from 'lucide-react'

export function TransformationResult({ result }: { result: TransformationResponse }) {
  const [copied, setCopied] = React.useState(false)

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

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
            <p className="text-sm font-mono text-gray-600">{result.mt_type} → {result.mx_type}</p>
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
          <StatItem label="Confidence" value={`${(result.statistics.overall_confidence * 100).toFixed(0)}%`} />
          <StatItem label="Validation Score" value={`${result.statistics.validation_score.toFixed(0)}`} />
          <StatItem label="Errors" value={result.statistics.errors} />
          <StatItem label="Warnings" value={result.statistics.warnings} />
        </div>
      </Card>

      {/* Parsed MT */}
      <Card title="Parsed SWIFT MT Message">
        <div className="space-y-2">
          <p className="text-sm text-gray-600">Message Type: {result.mt_type}</p>
          <div className="bg-gray-50 p-3 rounded border border-gray-200 max-h-96 overflow-y-auto">
            <pre className="text-xs font-mono whitespace-pre-wrap break-words">
              {JSON.stringify(result.parsed_mt, null, 2)}
            </pre>
          </div>
        </div>
      </Card>

      {/* MX XML */}
      <Card title="ISO 20022 MX Output (XML)">
        <div className="space-y-3">
          <button
            onClick={() => copyToClipboard(result.mx_xml)}
            className="flex items-center gap-2 text-sm text-purple-600 hover:text-purple-700"
          >
            <Copy className="w-4 h-4" />
            {copied ? 'Copied!' : 'Copy XML'}
          </button>
          <div className="bg-gray-50 p-3 rounded border border-gray-200 overflow-auto" style={{ maxHeight: '600px' }}>
            <pre className="text-xs font-mono whitespace-pre-wrap break-words">
              {result.mx_xml}
            </pre>
          </div>
        </div>
      </Card>

      {/* MX Structure */}
      <Card title="MX Structure (JSON)">
        <div className="bg-gray-50 p-3 rounded border border-gray-200 max-h-96 overflow-auto">
          <pre className="text-xs font-mono whitespace-pre-wrap break-words">
            {JSON.stringify(result.mx_structure, null, 2)}
          </pre>
        </div>
      </Card>
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
