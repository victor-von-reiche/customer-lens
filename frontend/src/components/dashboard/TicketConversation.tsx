import type { Dispatch, SetStateAction } from 'react';
import { Edit3, Send, User } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import type { Feedback, Message, TicketStatus } from '../../api';
import { api } from '../../api';

interface Props {
    chattingId: number | null;
    activeTicket: Feedback | null;
    detailError: string;
    editingId: number | null;
    editResponse: string;
    reviewer: string;
    sending: boolean;
    setEditingId: Dispatch<SetStateAction<number | null>>;
    setEditResponse: Dispatch<SetStateAction<string>>;
    setReviewer: Dispatch<SetStateAction<string>>;
    closeChat: () => void;
    handleApprove: (id: number, response: string) => Promise<void>;
    updateTicket: (action: () => Promise<unknown>) => Promise<void>;
}

const usableDraft = (response: string | null) => {
    const text = response?.trim() || '';
    return /^thank you for contacting auron\.?\s*we will review your feedback and respond shortly\.?$/i.test(text) ? '' : text;
};

/** Render the conversation, evidence, and reply controls for a ticket. */
export default function TicketConversation({
    chattingId, activeTicket, detailError, editingId, editResponse, reviewer,
    sending, setEditingId, setEditResponse, setReviewer, closeChat,
    handleApprove, updateTicket,
}: Props) {
    return (
<AnimatePresence>
    {chattingId && (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            onClick={closeChat}
        >
            {(() => {
                const activeFeedback = activeTicket?.id === chattingId ? activeTicket : null;
                if (!activeFeedback) return <div className="rounded-3xl border border-white/10 bg-auron-dark p-8 text-center" onClick={event => event.stopPropagation()}>
                    <p role="status">{detailError || 'Loading ticket…'}</p>
                    <button className="mt-4 text-auron-orange" onClick={closeChat}>Close</button>
                </div>;

                return (
                    <motion.div
                        initial={{ scale: 0.95, y: 20 }}
                        animate={{ scale: 1, y: 0 }}
                        exit={{ scale: 0.95, y: 20 }}
                        onClick={(e) => e.stopPropagation()}
                        className="bg-auron-dark w-full max-w-3xl max-h-[90vh] rounded-3xl overflow-hidden border border-white/10 flex flex-col shadow-2xl"
                    >

                        <div className="p-6 border-b border-white/10 flex items-center justify-between bg-white/[0.02]">
                            <div className="flex items-center gap-4">
                                <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center text-auron-orange">
                                    <User className="w-5 h-5" />
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold">{activeFeedback.customer_name}</h3>
                                    <p className="text-white/40 text-xs">{activeFeedback.customer_email}</p>
                                </div>
                            </div>
                            <button onClick={closeChat} className="text-white/40 hover:text-white transition-colors">
                                ✕
                            </button>
                        </div>

                        <div className="px-6 py-3 border-b border-white/10 flex flex-wrap items-center gap-3 text-sm">
                            <label className="text-white/60">Status
                                <select aria-label="Ticket status" value={activeFeedback.status} disabled={sending} onChange={event => void updateTicket(() => api.setStatus(activeFeedback.id, event.target.value as TicketStatus))} className="ml-2 bg-auron-dark border border-white/20 rounded-lg p-2 text-white">
                                    <option value="open">Open</option>
                                    <option value="waiting_for_customer">Waiting for customer</option>
                                    <option value="resolved">Resolved</option>
                                </select>
                            </label>
                            <button disabled={sending || activeFeedback.status === 'resolved'} className="text-auron-orange underline disabled:opacity-40" onClick={() => void updateTicket(() => api.analyze(activeFeedback.id))}>Analyze again</button>
                        </div>
                        {['failed', 'partial'].includes(activeFeedback.analysis_status) && <p role="alert" className="px-6 py-3 text-sm text-red-300">{activeFeedback.analysis_status === 'partial' ? 'Please write a reply or try again.' : 'Please review this feedback or try again.'}</p>}

                        <div className="flex-1 overflow-y-auto p-6 bg-black/20">

                            {activeFeedback.messages && activeFeedback.messages.map((msg: Message, idx: number) => {
                                const msgDate = new Date(msg.timestamp).toDateString();
                                const prevMsgDate = idx > 0 ? new Date(activeFeedback.messages[idx - 1].timestamp).toDateString() : null;
                                const showDateSeparator = msgDate !== prevMsgDate;

                                return (
                                            <div key={msg.id}>
                                                {showDateSeparator && (
                                                    <div className="flex items-center gap-4 mb-8 mt-4">
                                                        <div className="h-px flex-1 bg-white/5" />
                                                        <span className="text-[10px] uppercase font-black tracking-[0.3em] text-white/20 whitespace-nowrap">
                                                            {new Date(msg.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                                                        </span>
                                                        <div className="h-px flex-1 bg-white/5" />
                                                    </div>
                                                )}
                                                <div className={`flex flex-col ${msg.sender === 'customer' ? 'items-start mr-auto' : 'items-end ml-auto'} max-w-[85%] mb-6`}>
                                                    <div className="flex items-end gap-2 mb-1">
                                                        {msg.sender === 'customer' ? (
                                                            <>
                                                                <span className="text-xs font-bold text-white/40 ml-2">{activeFeedback.customer_name}</span>
                                                                <span className="text-[10px] text-white/20">{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                                            </>
                                                        ) : (
                                                            <>
                                                                <span className="text-[10px] text-white/20">{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                                                <span className="text-xs font-bold text-auron-orange mr-2">AURON Support</span>
                                                            </>
                                                        )}
                                                    </div>
                                                    <div className={`p-4 rounded-2xl border ${msg.sender === 'customer'
                                                            ? 'bg-white/10 text-white/90 rounded-tl-sm border-white/10'
                                                            : 'bg-auron-orange/20 text-white/95 rounded-tr-sm border-auron-orange/30'
                                                        }`}>
                                                        <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>

                                <div className="p-4 border-t border-white/10 bg-white/[0.02] max-h-[45vh] overflow-y-auto">
                                    <details className="mb-3 text-sm text-white/70">
                                        <summary className="cursor-pointer">Evidence & approval history</summary>
                                        {activeFeedback.analyses.at(-1)?.result?.explanation && <p className="mt-3 text-xs">{activeFeedback.analyses.at(-1)?.result?.explanation}</p>}
                                        {activeFeedback.analyses.at(-1)?.sources.map(source => <details key={source.id} className="mt-3 p-3 bg-white/5 rounded-xl">
                                            <summary className="cursor-pointer">{source.title}</summary>
                                            <p className="mt-2 leading-relaxed">{source.text}</p>
                                            <p className="mt-2 text-xs text-white/40">{source.id} · Version {source.version}</p>
                                        </details>)}
                                        {activeFeedback.approvals.map(approval => <details key={approval.id} className="mt-3 p-3 bg-white/5 rounded-xl">
                                            <summary className="cursor-pointer">{approval.reviewer} · {new Date(approval.created_at).toLocaleString()}</summary>
                                            {approval.original_response && <p className="mt-2">Original: {approval.original_response}</p>}
                                            <p className="mt-2">Approved: {approval.approved_response}</p>
                                        </details>)}
                                    </details>
                                    <label className="mb-3 flex flex-wrap items-center gap-2 text-xs text-white/50">Reviewer (self-reported)
                                        <input aria-label="Reviewer name" value={reviewer} maxLength={100} onChange={event => setReviewer(event.target.value)} className="bg-white/5 border border-white/10 rounded-lg p-2 text-white" />
                                    </label>
                                    {usableDraft(activeFeedback.ai_response) && activeFeedback.messages?.[activeFeedback.messages.length - 1]?.sender === 'customer' && editingId !== activeFeedback.id && (
                                        <div className="flex items-center gap-2 mb-2">
                                            <span className="text-[10px] text-auron-orange/50">Suggested reply · review before sending</span>
                                        </div>
                                    )}
                                    <div className="flex gap-3">
                                        <textarea
                                            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white/90 leading-relaxed focus:outline-none focus:border-auron-orange focus:ring-1 focus:ring-auron-orange resize-none min-h-[80px]"
                                            placeholder="Type your reply..."
                                            value={editingId === activeFeedback.id ? editResponse : (
                                                activeFeedback.messages?.[activeFeedback.messages.length - 1]?.sender === 'customer'
                                                ? usableDraft(activeFeedback.ai_response)
                                                : ''
                                            )}
                                            onChange={(e) => {
                                                if (editingId !== activeFeedback.id) {
                                                    setEditingId(activeFeedback.id);
                                                }
                                                setEditResponse(e.target.value);
                                            }}
                                            onFocus={() => {
                                                if (editingId !== activeFeedback.id) {
                                                    const currentVal = activeFeedback.messages?.[activeFeedback.messages.length - 1]?.sender === 'customer'
                                                        ? usableDraft(activeFeedback.ai_response)
                                                        : '';
                                                    setEditingId(activeFeedback.id);
                                                    setEditResponse(currentVal);
                                                }
                                            }}
                                        />
                                        <div className="flex flex-col gap-2 self-end">
                                            {usableDraft(activeFeedback.ai_response) && activeFeedback.messages?.[activeFeedback.messages.length - 1]?.sender === 'customer' && (
                                                <button
                                                    onClick={() => {
                                                        if (editingId === activeFeedback.id) {
                                                            setEditingId(null);
                                                        } else {
                                                            setEditingId(activeFeedback.id);
                                                            setEditResponse(usableDraft(activeFeedback.ai_response));
                                                        }
                                                    }}
                                                    className="flex items-center justify-center gap-2 bg-blue-600/80 hover:bg-blue-500 text-white text-xs font-bold py-3 px-5 rounded-xl transition-all border border-blue-500/50"
                                                >
                                                    <Edit3 className="w-4 h-4" />
                                                    {editingId === activeFeedback.id ? 'Cancel' : 'Edit'}
                                                </button>
                                            )}
                                            <button
                                                disabled={sending || !reviewer.trim() || activeFeedback.status === 'resolved'}
                                                onClick={() => {
                                                    const content = editingId === activeFeedback.id
                                                        ? editResponse
                                                        : (activeFeedback.messages?.[activeFeedback.messages.length - 1]?.sender === 'customer' ? usableDraft(activeFeedback.ai_response) : '');
                                                    if (content.trim()) {
                                                        handleApprove(activeFeedback.id, content);
                                                    }
                                                }}
                                                className="flex items-center justify-center gap-2 bg-green-600/80 hover:bg-green-500 text-white text-xs font-bold py-3 px-5 rounded-xl transition-all border border-green-500/50"
                                            >
                                                <Send className="w-4 h-4" />
                                                {sending ? 'Saving…' : 'Send'}
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </motion.div>
                        );
                    })()}
                </motion.div>
            )}
        </AnimatePresence>
    );
}
