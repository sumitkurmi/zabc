export type ProblemType =
  | 'LAN_PROBLEM'
  | 'IP_ADDRESS_ISSUE'
  | 'PROXY_ISSUE'
  | 'LAN_PORT_BROKEN'
  | 'WIFI_PROBLEM';

export type ComplaintStatus = 'NEW' | 'IN_PROGRESS' | 'RESOLVED';
export type ChatStatus = 'UNASSIGNED' | 'REFERENCE';
export type DocumentSourceType = 'UPLOAD' | 'CHAT' | 'COMPLAINT';
export type DocumentStatus = 'PROCESSING' | 'INDEXED' | 'FAILED';

export interface LocationOption {
  id: string;
  name: string;
}

export interface ProblemTypeOption {
  value: ProblemType;
  label: string;
}

export interface ConfigResponse {
  college_name: string;
  locations: LocationOption[];
  problem_types: ProblemTypeOption[];
  max_chat_messages: number;
  max_upload_mb: number;
}

export interface ComplaintCreateRequest {
  name: string;
  email: string;
  mobile: string;
  location: string;
  address_room: string;
  preferred_from: string;
  preferred_to: string;
  problem_type: ProblemType;
  additional_comment?: string;
  chat_id?: string;
  filled_by_ai?: boolean;
  honeypot?: string;
}

export interface ComplaintCreateResponse {
  id: string;
  ref_no: string;
  message: string;
}

export interface ChatTurn {
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  is_off_topic?: boolean;
}

export interface ChatMessageResponse {
  reply: string;
  detected_category: ProblemType | null;
  on_topic: boolean;
  messages_used: number;
  messages_remaining: number;
}

export interface ChatTranscriptResponse {
  chat_id: string;
  message_count: number;
  messages_remaining: number;
  detected_category: ProblemType | null;
  messages: ChatTurn[];
}

export interface SummarizeResponse {
  problem_type: ProblemType;
  additional_comment: string;
}

export interface AdminLoginResponse {
  token: string;
  expires_at: string;
}

export interface AdminStatsResponse {
  unassigned_chats_count: number;
  reference_documents_count: number;
  complaints_today_count: number;
  total_chats_count: number;
}

export interface ChatSummary {
  id: string;
  preview: string;
  message_count: number;
  detected_category: ProblemType | null;
  created_at: string;
  status: ChatStatus;
  reference_category_slug: string | null;
}

export interface ChatListResponse {
  chats: ChatSummary[];
  total: number;
  page: number;
  pages: number;
}

export interface CategorySummary {
  slug: string;
  name: string;
  description: string;
  chats_count: number;
  documents_count: number;
}

export interface DocumentResponse {
  id: string;
  category_slug: string;
  source_type: DocumentSourceType;
  chat_id: string | null;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  status: DocumentStatus;
  error_message: string | null;
  chunk_count: number;
  uploaded_at: string;
}

export interface CategoryDetailResponse {
  category: CategorySummary;
  chats: ChatSummary[];
  documents: DocumentResponse[];
}
