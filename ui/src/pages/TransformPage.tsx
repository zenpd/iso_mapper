import React, { useState } from 'react'
import { MTInputForm } from '@/components/forms/MTInputForm'
import { TransformationResult } from '@/components/results/TransformationResult'
import { LoadingSpinner, TransformationTypeSelector } from '@/components/common'
import { useTransformStore } from '@/store/transformStore'
import { apiClient } from '@/services/api'

export function TransformPage() {
  const { setLoading, setError, setResult, isLoading, lastResult } = useTransformStore()
  const store = useTransformStore()
  const [localError, setLocalError] = useState<string>()
  const [direction, setDirection] = useState<'mt_to_iso' | 'iso_to_mt'>('mt_to_iso')

  const handleTransform = async () => {
    setLocalError(undefined)
    setLoading(true)
    setError(undefined)

    try {
      let result
      if (direction === 'mt_to_iso') {
        result = await apiClient.transform({
          mt_message: store.mtMessage,
          approach: store.approach,
          message_id: store.messageId,
        })
      } else {
        result = await apiClient.reverseTransform({
          mt_message: store.mtMessage,
          approach: store.approach,
          message_id: store.messageId,
        })
      }
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
      {/* Banner Section */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-100 rounded-lg p-6">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          Intelligent Financial Message Transformation
        </h1>
        <p className="text-lg text-gray-600">
          Seamless bidirectional conversion between SWIFT MT and ISO 20022 MX messages with validation and smart mapping
        </p>
      </div>

      {/* Transformation Type Selector */}
      <TransformationTypeSelector />

      {/* Direction Toggle */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <span className="font-medium text-gray-700">Transformation Direction</span>
          <div className="flex items-center gap-4">
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                name="direction"
                value="mt_to_iso"
                checked={direction === 'mt_to_iso'}
                onChange={(e) => setDirection(e.target.value as 'mt_to_iso' | 'iso_to_mt')}
                className="w-4 h-4 text-blue-600"
              />
              <span className="ml-2 text-sm text-gray-700">MT → ISO 20022</span>
            </label>
            <label className="flex items-center cursor-pointer">
              <input
                type="radio"
                name="direction"
                value="iso_to_mt"
                checked={direction === 'iso_to_mt'}
                onChange={(e) => setDirection(e.target.value as 'mt_to_iso' | 'iso_to_mt')}
                className="w-4 h-4 text-blue-600"
              />
              <span className="ml-2 text-sm text-gray-700">ISO 20022 → MT</span>
            </label>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-8">
        {/* Input Section */}
        <div>
          <MTInputForm onSubmit={handleTransform} direction={direction} />
        </div>

        {/* Results Section */}
        <div>
          {isLoading ? (
            <div className="flex items-center justify-center h-full min-h-[400px]">
              <LoadingSpinner message="Transforming message..." />
            </div>
          ) : lastResult ? (
            <TransformationResult result={lastResult} direction={direction} />
          ) : (
            <div className="bg-white rounded-lg border border-gray-200 p-8 text-center min-h-[400px] flex items-center justify-center">
              <div>
                <p className="text-gray-600 mb-2">Results will appear here</p>
                <p className="text-sm text-gray-500">
                  {direction === 'mt_to_iso' 
                    ? 'Paste an MT message and click Transform'
                    : 'Paste ISO 20022 XML and click Transform'
                  }
                </p>
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
