export type TicketStatus = 'open' | 'waiting_for_customer' | 'resolved';
export type Sentiment = 'positive' | 'negative' | 'neutral' | 'mixed';

export interface Source {
    id: string;
    title: string;
    version: string;
    text: string;
    score: number;
}

export interface Analysis {
    id: number;
    message_id: number;
    status: string;
    mode: 'demo' | 'live';
    model: string;
    prompt_version: string;
    result: {
        sentiment: Sentiment;
        category: string;
        urgency: string;
        explanation: string;
        response?: string;
        cited_source_ids?: string[];
        needs_review?: boolean;
    } | null;
    sources: Source[];
    error: string | null;
    latency_ms: number;
    input_tokens: number;
    output_tokens: number;
    estimated_cost_usd: number | null;
    created_at: string;
}

export interface Message {
    id: number;
    sender: 'customer' | 'agent' | 'system';
    content: string;
    timestamp: string;
}

export interface Approval {
    id: number;
    analysis_id: number | null;
    reviewer: string;
    original_response: string;
    approved_response: string;
    edited: boolean;
    created_at: string;
}

export interface Escalation {
    id: number;
    feedback_id: number;
    reason: string;
    status: 'new' | 'acknowledged' | 'resolved';
    created_at: string;
}

export interface Feedback {
    id: number;
    customer_id: number;
    customer_name: string;
    customer_email: string;
    feedback_text: string;
    sentiment: Sentiment | null;
    category: string | null;
    urgency: string | null;
    status: TicketStatus;
    analysis_status: string;
    ai_response: string | null;
    created_at: string;
    updated_at: string;
    messages: Message[];
    analyses: Analysis[];
    approvals: Approval[];
    escalations: Escalation[];
}

export interface FeedbackSubmission {
    customer_name: string;
    customer_email: string;
    feedback_text: string;
}

export interface DashboardStats {
    non_negative_sentiment_percent: number | null;
    non_negative_sentiment_today_percent: number | null;
    critical_today: number;
    critical_resolved_today: number;
    positive_today: number;
    positive_sentiment_today_percent: number | null;
    total_count: number;
    open_count: number;
    waiting_count: number;
    resolved_count: number;
    positive_sentiment_percent: number | null;
    analyzed_count: number;
    failed_count: number;
    active_escalations: number;
    created_today: number;
    resolved_today: number;
}

export interface RuntimeConfig {
    mode: 'demo' | 'live';
    model: string;
    requires_token: boolean;
    retrieval: string;
    policy_version: string;
}

const baseUrl = import.meta.env.VITE_API_URL || '/api';

/** Send a typed request and normalize validation errors. */
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const token = sessionStorage.getItem('customerlens-token');
    const response = await fetch(`${baseUrl}${path}`, {
        ...init,
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...init.headers,
        },
    });
    if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const detail = body.detail;
        throw new Error(typeof detail === 'string' ? detail :
            Array.isArray(detail) ? detail.map((e: { msg: string }) => e.msg).join('; ') :
                `Request failed (${response.status})`);
    }
    return response.status === 204 ? undefined as T : response.json();
}

export const api = {
    config: () => request<RuntimeConfig>('/config'),
    submitFeedback: (data: FeedbackSubmission) => request<Feedback>('/feedback/', {
        method: 'POST', body: JSON.stringify(data),
    }),
    getAllFeedback: (filter: string, status: string, sortBy: string, skip = 0, limit = 50) =>
        request<Feedback[]>(`/feedback/?${new URLSearchParams({
            filter, status, sort_by: sortBy, skip: String(skip), limit: String(limit),
        })}`),
    getDashboardStats: () => request<DashboardStats>('/feedback/stats'),
    getFeedbackById: (id: number) => request<Feedback>(`/feedback/${id}`),
    setStatus: (id: number, status: TicketStatus) => request<Feedback>(`/feedback/${id}/status`, {
        method: 'PATCH', body: JSON.stringify({ status }),
    }),
    analyze: (id: number) => request<Feedback>(`/feedback/${id}/analyze`, { method: 'POST' }),
    approve: (id: number, response: string, reviewer: string, analysisId: number | null, requestId: string) =>
        request<Feedback>(`/feedback/${id}/approve-and-send`, {
            method: 'POST', body: JSON.stringify({
                approved_response: response, reviewer, analysis_id: analysisId, request_id: requestId,
            }),
        }),
    sendMessage: (id: number, content: string) => request<Feedback>(`/feedback/${id}/message`, {
        method: 'POST', body: JSON.stringify({ sender: 'customer', content }),
    }),
    deleteFeedback: (id: number) => request<void>(`/feedback/${id}`, { method: 'DELETE' }),
    escalations: () => request<Escalation[]>('/feedback/escalations'),
    updateEscalation: (id: number, status: 'acknowledged' | 'resolved') =>
        request<Escalation>(`/feedback/escalations/${id}`, {
            method: 'PATCH', body: JSON.stringify({ status }),
        }),
};
