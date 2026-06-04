import axios, { AxiosInstance } from 'axios'
import {
  TransformationRequest,
  TransformationResponse,
  SampleMessage,
  HealthResponse,
  ConfigResponse,
} from '@/types/api'

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })
  }

  // Transformation endpoints
  async transform(request: TransformationRequest): Promise<TransformationResponse> {
    const response = await this.client.post<TransformationResponse>(
      '/api/v1/transform',
      request
    )
    return response.data
  }

  async getSamples(): Promise<SampleMessage[]> {
    const response = await this.client.get<{ count: number; samples: SampleMessage[] }>(
      '/api/v1/samples'
    )
    return response.data.samples
  }

  // System endpoints
  async getHealth(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health')
    return response.data
  }

  async getConfig(): Promise<ConfigResponse> {
    const response = await this.client.get<ConfigResponse>('/config')
    return response.data
  }
}

export const apiClient = new APIClient()
