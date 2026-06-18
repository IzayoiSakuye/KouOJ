import http from './http'
import type { AgentRun, CreateAgentRunRequest, PaginatedResponse } from '../types/api'

export function createAgentRun(data: CreateAgentRunRequest) {
  return http.post<AgentRun>('/ai-agent/runs/', data, { timeout: 60000 })
}

export function getAgentRuns(params?: { page?: number }) {
  return http.get<PaginatedResponse<AgentRun>>('/ai-agent/runs/', { params })
}

export function getAgentRun(id: number | string) {
  return http.get<AgentRun>(`/ai-agent/runs/${id}/`)
}
