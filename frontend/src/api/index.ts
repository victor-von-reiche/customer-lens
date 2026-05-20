const API_BASE_URL = 'http://localhost:8000';

export interface Message {
    id: number;
    feedback_id: number;
    sender: 'customer' | 'agent' | 'system';
    content: string;
    timestamp: string;
}

export interface Feedback {
    id: string;
    customer_name: string;
    customer_email: string;
    feedback_text: string;
    sentiment: 'Positive' | 'Negative' | 'Mixed';
    category: string;
    urgency?: string;
    ai_response: string;
    created_at: string;
    messages: Message[];
}

export interface FeedbackSubmission {
    customer_name: string;
    customer_email: string;
    feedback_text: string;
}

export interface DashboardStats {
    total_count: number;
    open_count: number;
    closed_count: number;
    satisfaction_score: number;
    processed_today: number;
    critical_today: number;
    critical_resolved_today: number;
    positive_today: number;
    satisfaction_today: number;
}

export const api = {
    async submitFeedback(data: FeedbackSubmission): Promise<Feedback> {
        // The backend requires a trailing slash for some reason
        const response = await fetch(`${API_BASE_URL}/feedback/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || 'Failed to submit feedback');
        }
        return response.json();
    },

    async getAllFeedback(filter: string = 'All', sortBy: string = 'Urgency'): Promise<Feedback[]> {
        const params = new URLSearchParams({
            filter: filter,
            sort_by: sortBy
        });
        
        // Trying both with and without slash
        const tryFetch = async (url: string) => {
            console.log(`Fetching feedback from: ${url}`);
            const res = await fetch(url);
            if (res.ok) return res.json();
            console.warn(`Fetch failed for ${url}: ${res.status}`);
            return null;
        };

        let data = await tryFetch(`${API_BASE_URL}/feedback/?${params.toString()}`);
        if (!data) data = await tryFetch(`${API_BASE_URL}/feedback?${params.toString()}`);

        if (!data) throw new Error('Failed to fetch feedback from all known endpoints');
        return data;
    },

    async getDashboardStats(): Promise<DashboardStats> {
        const response = await fetch(`${API_BASE_URL}/feedback/stats`);
        if (!response.ok) throw new Error('Failed to fetch dashboard stats');
        return response.json();
    },

    async getFeedbackById(id: string): Promise<Feedback> {
        const response = await fetch(`${API_BASE_URL}/feedback/${id}`);
        if (!response.ok) throw new Error('Failed to fetch feedback details');
        return response.json();
    },

    async approveFeedback(id: string, ai_response: string): Promise<void> {
        // Now "approving" means sending the AI response as an agent message
        const response = await fetch(`${API_BASE_URL}/feedback/${id}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                sender: 'agent',
                content: ai_response 
            }),
        });
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || 'Failed to send message');
        }
    },

    async sendMessage(id: string, content: string, sender: 'agent' | 'customer' = 'agent'): Promise<Feedback> {
        const response = await fetch(`${API_BASE_URL}/feedback/${id}/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sender, content }),
        });
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || 'Failed to send message');
        }
        return response.json();
    },

    async deleteFeedback(id: string): Promise<void> {
        const response = await fetch(`${API_BASE_URL}/feedback/${id}`, {
            method: 'DELETE',
        });
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || 'Failed to delete feedback');
        }
    }
};
