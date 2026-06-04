import React, { useState } from 'react'
import { MTInputForm } from '@/components/forms/MTInputForm'
import { TransformationResult } from '@/components/results/TransformationResult'
import { LoadingSpinner } from '@/components/common'
import { useTransformStore } from '@/store/transformStore'
import { apiClient } from '@/services/api'

export function TransformPage() {
  const { setLoading, setError, setResult, isLoading, lastResult } = useTransformStore()
  const store = useTransformStore()
  const [localError, setLocalError] = useState<string>()

  const handleTransform = async () => {
    setLocalError(undefined)
    setLoading(true)
    setError(undefined)

    try {
      const result = await apiClient.transform({
        mt_message: store.mtMessage,
        approach: store.approach,
        message_id: store.messageId,
      })
      setResult(result)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Transformation failed'
      setLocalError(errorMessage)
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold text-gray-900 mb-2">MT to ISO 20022 Transformation</h1>
        <p className="text-gray-600">
          Transform SWIFT MT messages to ISO 20022 MX format using intelligent mapping agents
        </p>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Input Section */}
        <div>
          <MTInputForm onSubmit={handleTransform} />
        </div>

        {/* Results Section */}
        <div>
          {isLoading ? (
            <div className="flex items-center justify-center h-full min-h-[400px]">
              <LoadingSpinner message="Transforming message..." />
            </div>
          ) : lastResult ? (
            <TransformationResult result={lastResult} />
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 p-8 text-center min-h-[400px] flex items-center justify-center">
              <div>
                <p className="text-gray-600 mb-2">Results will appear here</p>
                <p className="text-sm text-gray-500">Paste an MT message and click Transform</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {(localError || store.error) && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 font-medium">Error</p>
          <p className="text-red-700 text-sm mt-1">{localError || store.error}</p>
        </div>
      )}
    </div>
  )
}
