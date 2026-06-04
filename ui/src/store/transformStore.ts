import { create } from 'zustand'
import { TransformationResponse, TransformationApproach } from '@/types/api'

interface TransformState {
  // Input
  mtMessage: string
  approach: TransformationApproach
  messageId?: string
  
  // Processing
  isLoading: boolean
  error?: string
  
  // Results
  lastResult?: TransformationResponse
  
  // Actions
  setMtMessage: (message: string) => void
  setApproach: (approach: TransformationApproach) => void
  setMessageId: (id?: string) => void
  setLoading: (loading: boolean) => void
  setError: (error?: string) => void
  setResult: (result: TransformationResponse) => void
  reset: () => void
}

export const useTransformStore = create<TransformState>((set) => ({
  mtMessage: '',
  approach: 'hybrid',
  messageId: undefined,
  isLoading: false,
  error: undefined,
  lastResult: undefined,

  setMtMessage: (message) => set({ mtMessage: message }),
  setApproach: (approach) => set({ approach }),
  setMessageId: (id) => set({ messageId: id }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  setResult: (result) => set({ lastResult: result, error: undefined }),
  reset: () => set({
    mtMessage: '',
    approach: 'hybrid',
    messageId: undefined,
    isLoading: false,
    error: undefined,
    lastResult: undefined,
  }),
}))
