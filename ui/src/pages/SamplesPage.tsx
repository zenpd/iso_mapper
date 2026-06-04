import React, { useEffect, useState } from 'react'
import { Card, Button, LoadingSpinner } from '@/components/common'
import { SampleMessage } from '@/types/api'
import { apiClient } from '@/services/api'
import { useTransformStore } from '@/store/transformStore'
import { Copy } from 'lucide-react'

export function SamplesPage() {
  const [samples, setSamples] = useState<SampleMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>()
  const { setMtMessage } = useTransformStore()

  useEffect(() => {
    loadSamples()
  }, [])

  const loadSamples = async () => {
    setLoading(true)
    setError(undefined)
    try {
      const data = await apiClient.getSamples()
      setSamples(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load samples')
    } finally {
      setLoading(false)
    }
  }

  const useSample = (message: string) => {
    setMtMessage(message)
    window.location.href = '/'
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-96">
        <LoadingSpinner message="Loading samples..." />
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Sample MT Messages</h1>
        <p className="text-gray-600">
          Browse example SWIFT MT messages to test the transformation pipeline
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
          <Button onClick={loadSamples} variant="secondary" size="sm" className="mt-2">
            Try Again
          </Button>
        </div>
      )}

      <div className="grid gap-6">
        {samples.map((sample) => (
          <Card key={sample.id} variant="elevated">
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{sample.name}</h3>
                <p className="text-sm text-gray-600 mt-1">{sample.description}</p>
                <div className="flex gap-4 mt-2 text-sm">
                  <span className="text-gray-600">
                    Currency: <span className="font-mono font-semibold">{sample.currency}</span>
                  </span>
                  <span className="text-gray-600">
                    Amount: <span className="font-mono font-semibold">{sample.amount}</span>
                  </span>
                </div>
              </div>

              <div className="bg-gray-50 p-3 rounded border border-gray-200">
                <pre className="text-xs font-mono whitespace-pre-wrap break-words">
                  {sample.message}
                </pre>
              </div>

              <div className="flex gap-3">
                <Button
                  onClick={() => useSample(sample.message)}
                  variant="primary"
                  size="sm"
                >
                  Use this Sample
                </Button>
                <Button
                  onClick={() => {
                    navigator.clipboard.writeText(sample.message)
                  }}
                  variant="secondary"
                  size="sm"
                >
                  <Copy className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
