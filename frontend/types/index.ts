// Shared TypeScript types for CampusSaarthi AI frontend

export interface SourceCitation {
  source_id: string
  document_id: string
  filename: string
  page: number | null
  excerpt: string
  relevance_score: number
}

export interface ChatResponse {
  request_id: string
  conversation_id: string
  answer: string
  abstained: boolean
  abstention_reason: string | null
  citations: SourceCitation[]
  conflict_detected: boolean
  conflict_note: string | null
  retrieval_count: number
  processing_time_ms: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: SourceCitation[]
  abstained?: boolean
  abstention_reason?: string | null
  conflict_detected?: boolean
  conflict_note?: string | null
  processing_time_ms?: number
  timestamp: Date
}

export interface Document {
  id: string
  filename: string
  original_filename: string
  file_size_bytes: number
  file_type: string
  category: string | null
  status: 'pending' | 'processing' | 'indexed' | 'failed' | 'deleted'
  total_pages: number
  total_chunks: number
  error_message: string | null
  is_demo: boolean
  uploaded_at: string
  indexed_at: string | null
}

export interface DocumentListResponse {
  documents: Document[]
  total: number
}

export interface AdminStats {
  documents: {
    total: number
    indexed: number
    processing: number
    failed: number
    pending: number
  }
  content: {
    total_indexed_pages: number
    total_indexed_chunks: number
  }
  vector_store: {
    total_vectors: number
    embedding_model: string
  }
}

export interface HealthStatus {
  status: string
  app: string
  version: string
  environment: string
  model_available: boolean
  model_id: string
  embedding_model: string
  indexed_vectors: number
}
