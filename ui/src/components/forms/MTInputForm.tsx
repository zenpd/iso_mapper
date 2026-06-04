import React, { useState } from 'react'
import { useTransformStore } from '@/store/transformStore'
import { Button, Card } from '@/components/common'
import { TransformationApproach } from '@/types/api'

export function MTInputForm({ onSubmit }: { onSubmit: () => void }) {
  const { mtMessage, approach, messageId, isLoading } = useTransformStore()
  const { setMtMessage, setApproach, setMessageId } = useTransformStore()
  const [error, setError] = useState<string>()

  const handleSubmit = () => {
    if (!mtMessage.trim()) {
      setError('Please enter an MT message')
      return
    }
    setError(undefined)
    onSubmit()
  }

  const approaches: { value: TransformationApproach; label: string }[] = [
    { value: 'rules', label: 'Rules-Based' },
    { value: 'llm', label: 'LLM-Based' },
    { value: 'hybrid', label: 'Hybrid' },
  ]

  return (
    <Card title="MT Message Input" variant="elevated">
      <div className="space-y-4">
        <div>
          <label htmlFor="mt-message" className="block text-sm font-medium text-gray-700 mb-2">
            SWIFT MT Message
          </label>
          <textarea
            id="mt-message"
            value={mtMessage}
            onChange={(e) => setMtMessage(e.target.value)}
            placeholder="Paste your SWIFT MT message here (e.g., :20:REFERENCE123\n:32A:250101USD..."
            className="w-full h-40 p-3 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            disabled={isLoading}
          />
          {error && <p className="text-red-600 text-sm mt-2">{error}</p>}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="approach" className="block text-sm font-medium text-gray-700 mb-2">
              Approach
            </label>
            <select
              id="approach"
              value={approach}
              onChange={(e) => setApproach(e.target.value as TransformationApproach)}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              disabled={isLoading}
            >
              {approaches.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="message-id" className="block text-sm font-medium text-gray-700 mb-2">
              Message ID (Optional)
            </label>
            <input
              id="message-id"
              type="text"
              value={messageId || ''}
              onChange={(e) => setMessageId(e.target.value || undefined)}
              placeholder="e.g., MSG-001"
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
              disabled={isLoading}
            />
          </div>
        </div>

        <Button
          onClick={handleSubmit}
          isLoading={isLoading}
          size="lg"
          className="w-full"
          disabled={!mtMessage.trim()}
        >
          Transform to ISO 20022
        </Button>
      </div>
    </Card>
  )
}
