import React, { useEffect, useState } from 'react'
import { Card, LoadingSpinner } from '@/components/common'
import { ConfigResponse } from '@/types/api'
import { apiClient } from '@/services/api'

export function AnalyticsPage() {
  const [config, setConfig] = useState<ConfigResponse>()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>()

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    setLoading(true)
    setError(undefined)
    try {
      const data = await apiClient.getConfig()
      setConfig(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load configuration')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-96">
        <LoadingSpinner message="Loading analytics..." />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Analytics & Configuration</h1>
        <p className="text-gray-600">System configuration and platform statistics</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {config && (
        <div className="grid md:grid-cols-2 gap-6">
          <Card title="Transformation Settings">
            <div className="space-y-3">
              <ConfigItem label="Default Approach" value={config.default_approach} />
              <ConfigItem
                label="LLM Configured"
                value={config.llm_configured ? 'Yes' : 'No'}
              />
              {config.llm_configured && (
                <ConfigItem label="LLM Model" value={config.llm_model || 'N/A'} />
              )}
              <ConfigItem label="Cache Enabled" value={config.cache_enabled ? 'Yes' : 'No'} />
            </div>
          </Card>

          <Card title="Platform Settings">
            <div className="space-y-3">
              <ConfigItem label="Environment" value={config.app_env} />
              <ConfigItem label="Log Level" value={config.log_level} />
              <div className="text-sm mt-4 p-3 bg-blue-50 rounded border border-blue-200">
                <p className="text-blue-900">
                  Approach: <span className="font-semibold">{config.default_approach}</span>
                </p>
                <p className="text-blue-800 text-xs mt-1">
                  The default transformation strategy used for new requests
                </p>
              </div>
            </div>
          </Card>
        </div>
      )}

      <Card title="About">
        <div className="space-y-4">
          <p className="text-gray-700">
            <strong>ISO 20022 GenAI Migration Platform v3</strong>
          </p>
          <p className="text-sm text-gray-600">
            A modern, agentic MT to MX transformation. Built with FastAPI (backend), React (frontend), LangGraph (agents), and
            Tailwind CSS (styling).
          </p>
          <div className="pt-4 border-t">
            <p className="text-sm text-gray-600">
              📚 See the API documentation at <code className="bg-gray-100 px-2 py-1 rounded">/docs</code>
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}

function ConfigItem({ label, value }: { label: string; value: string | boolean }) {
  return (
    <div className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
      <span className="text-gray-600">{label}</span>
      <span className="font-mono font-medium text-gray-900">{String(value)}</span>
    </div>
  )
}
