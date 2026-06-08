import React, { useState } from 'react'
import { Card } from './Card'

interface TransformationType {
  id: string
  mt: string
  iso: string
  title: string
  description: string
}

interface TransformationTypeSelectorProps {
  onSelect?: (type: string) => void
}

const transformationTypes: TransformationType[] = [
  {
    id: 'mt103_pacs008',
    mt: 'MT103',
    iso: 'pacs.008',
    title: 'Customer Credit Transfer',
    description: 'Cross-border payment message',
  },
  {
    id: 'mt101_pain001',
    mt: 'MT101',
    iso: 'pain.001',
    title: 'Customer Payment Instruction',
    description: 'Bulk / instruction message',
  },
  {
    id: 'mt202_pacs009',
    mt: 'MT202',
    iso: 'pacs.009',
    title: 'Bank-to-Bank Transfer',
    description: 'Interbank settlement message',
  },
]

export function TransformationTypeSelector({ onSelect }: TransformationTypeSelectorProps) {
  const [selectedType, setSelectedType] = useState<string | null>(null)

  const handleSelectType = (typeId: string) => {
    setSelectedType(typeId)
    onSelect?.(typeId)
  }

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-900">Select Transformation Type</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {transformationTypes.map((type) => (
          <div
            key={type.id}
            onClick={() => handleSelectType(type.id)}
            className={`cursor-pointer transform transition ${
              selectedType === type.id ? 'scale-105' : 'hover:scale-105'
            }`}
          >
            <Card 
              className={`h-full transition-all ${
                selectedType === type.id 
                  ? 'border-blue-500 border-2 shadow-md' 
                  : 'hover:shadow-md'
              }`}
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className={`inline-block text-xs font-semibold px-3 py-1 rounded ${
                    selectedType === type.id
                      ? 'bg-blue-500 text-white'
                      : 'bg-blue-100 text-blue-800'
                  }`}>
                    {type.mt} ↔ {type.iso}
                  </span>
                </div>
                <div>
                  <h3 className="text-base font-semibold text-gray-900">{type.title}</h3>
                  <p className="text-sm text-gray-600 mt-2">{type.description}</p>
                </div>
              </div>
            </Card>
          </div>
        ))}
      </div>
    </div>
  )
}
