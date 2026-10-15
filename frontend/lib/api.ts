// API client utility for CampusSaarthi AI

import type {
  ChatResponse,
  Document,
  DocumentListResponse,
  AdminStats,
  HealthStatus,
} from '@/types'

const BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${BASE_URL}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    let message = `HTTP ${res.status}`
    try {
      const err = await res.json()
      message = err.detail || message
    } catch {}
    throw new ApiError(res.status, message)
  }
  return res.json() as Promise<T>
}

function adminHeaders(username: string, password: string) {
  const encoded = btoa(`${username}:${password}`)
  return { Authorization: `Basic ${encoded}` }
}

// ── Chat ──────────────────────────────────────────────────────────────────────

export async function sendChat(
  question: string,
  conversationId?: string,
  history?: { role: string; content: string }[],
): Promise<ChatResponse> {
  return request<ChatResponse>('/api/v1/chat', {
    method: 'POST',
    body: JSON.stringify({
      question,
      conversation_id: conversationId,
      conversation_history: history,
    }),
  })
}

// ── Documents ─────────────────────────────────────────────────────────────────

export async function listDocuments(): Promise<DocumentListResponse> {
  return request<DocumentListResponse>('/api/v1/documents')
}

export async function getDocument(id: string): Promise<Document> {
  return request<Document>(`/api/v1/documents/${id}`)
}

export async function uploadDocument(
  file: File,
  category: string,
  isDemo: boolean,
  username: string,
  password: string,
) {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('category', category)
  fd.append('is_demo', String(isDemo))

  const url = `${BASE_URL}/api/v1/documents/upload`
  const res = await fetch(url, {
    method: 'POST',
    headers: adminHeaders(username, password),
    body: fd,
  })
  if (!res.ok) {
    let message = `HTTP ${res.status}`
    try {
      const err = await res.json()
      message = err.detail || message
    } catch {}
    throw new ApiError(res.status, message)
  }
  return res.json()
}

export async function deleteDocument(
  id: string,
  username: string,
  password: string,
) {
  const url = `${BASE_URL}/api/v1/documents/${id}`
  const res = await fetch(url, {
    method: 'DELETE',
    headers: adminHeaders(username, password),
  })
  if (!res.ok) {
    let message = `HTTP ${res.status}`
    try {
      const err = await res.json()
      message = err.detail || message
    } catch {}
    throw new ApiError(res.status, message)
  }
  return res.json()
}

export async function reindexDocument(
  id: string,
  username: string,
  password: string,
) {
  return request(`/api/v1/documents/${id}/reindex`, {
    method: 'POST',
    headers: adminHeaders(username, password),
  })
}

// ── Admin ─────────────────────────────────────────────────────────────────────

export async function getAdminStats(
  username: string,
  password: string,
): Promise<AdminStats> {
  return request<AdminStats>('/api/v1/admin/stats', {
    headers: adminHeaders(username, password),
  })
}

// ── Health ────────────────────────────────────────────────────────────────────

export async function getHealth(): Promise<HealthStatus> {
  return request<HealthStatus>('/health')
}

export { ApiError }
