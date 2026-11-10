import { useCallback, useEffect, useRef, useState } from 'react';
import type { Feedback, DashboardStats, Escalation, TicketStatus } from '../api';
import { api } from '../api';
import { CheckCircle2, Loader2, Inbox, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import DashboardOverview from '../components/dashboard/DashboardOverview';
import FeedbackCard from '../components/dashboard/FeedbackCard';
import TicketConversation from '../components/dashboard/TicketConversation';
import DeleteConversationDialog from '../components/dashboard/DeleteConversationDialog';

const DashboardPage = () => {
    const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
    const [activeTicket, setActiveTicket] = useState<Feedback | null>(null);
    const [detailError, setDetailError] = useState('');
    const [page, setPage] = useState(0);
    const [hasMore, setHasMore] = useState(false);
    const fetchVersion = useRef(0);
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('All');
    const [sortBy, setSortBy] = useState('Urgency');
    const [statusFilter, setStatusFilter] = useState<TicketStatus | 'all'>('open');
    const [chattingId, setChattingId] = useState<number | null>(null);
    const [editingId, setEditingId] = useState<number | null>(null);
    const [editResponse, setEditResponse] = useState('');
    const [successMsg, setSuccessMsg] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [deletingId, setDeletingId] = useState<number | null>(null);
    const [deleteLoading, setDeleteLoading] = useState(false);
    const [sending, setSending] = useState(false);
    const [reviewer, setReviewer] = useState('Support reviewer');
    const [alerts, setAlerts] = useState<Escalation[]>([]);
    const approvalRequest = useRef({ key: '', id: crypto.randomUUID() });

    const fetchFeedback = useCallback(async () => {
        const version = ++fetchVersion.current;
        try {
            setLoading(true);
            const [data, statsData, escalations] = await Promise.all([
                api.getAllFeedback(filter.toLowerCase(), statusFilter, sortBy.toLowerCase(), page * 50, 51),
                api.getDashboardStats(),
                api.escalations()
            ]);
            if (version !== fetchVersion.current) return;
            setHasMore(data.length > 50);
            setFeedbacks(data.slice(0, 50));
            if (!data.length && page > 0) setPage(page - 1);
            setStats(statsData);
            setAlerts(escalations);
            setError(null);
        } catch (err) {
            if (version !== fetchVersion.current) return;
            console.error(err);
            setError('The dashboard could not be loaded. Please refresh the page and try again.');
        } finally {
            if (version === fetchVersion.current) setLoading(false);
        }
    }, [filter, statusFilter, sortBy, page]);

    useEffect(() => {
        void fetchFeedback();
    }, [fetchFeedback]);

    useEffect(() => {
        const ticketId = Number(new URLSearchParams(window.location.search).get('ticket'));
        if (ticketId) setChattingId(ticketId);
    }, []);

    useEffect(() => {
        let current = true;
        setDetailError('');
        if (chattingId === null) {
            setActiveTicket(null);
            return;
        }
        api.getFeedbackById(chattingId).then(ticket => {
            if (current) setActiveTicket(ticket);
        }).catch(() => {
            if (current) setDetailError('This ticket could not be loaded. Please close it and try again.');
        });
        return () => { current = false; };
    }, [chattingId]);

    /** Save the reviewed reply through the backend approval endpoint. */
    const handleApprove = async (id: number, response: string) => {
        if (sending) return;
        setSending(true);
        try {
            const ticket = activeTicket?.id === id ? activeTicket : null;
            const analysis = ticket?.analyses.at(-1);
            const analysisId = analysis?.status === 'completed' &&
                !ticket?.approvals.some(item => item.analysis_id === analysis.id)
                ? analysis.id : null;
            const key = JSON.stringify([id, response, reviewer, analysisId]);
            if (approvalRequest.current.key !== key) {
                approvalRequest.current = { key, id: crypto.randomUUID() };
            }
            const updated = await api.approve(id, response, reviewer, analysisId, approvalRequest.current.id);
            setActiveTicket(current => current?.id === id ? updated : current);
            setSuccessMsg('Reviewed reply saved to the conversation');
            setTimeout(() => setSuccessMsg(null), 3000);
            setEditingId(null);
            setEditResponse('');
            await fetchFeedback();
        } catch (err) {
            alert((err as Error).message);
        } finally {
            setSending(false);
        }
    };

    /** Refresh ticket details and queue after a backend operation. */
    const updateTicket = async (action: () => Promise<unknown>) => {
        if (sending) return;
        setSending(true);
        try {
            await action();
            if (chattingId !== null) {
                const updated = await api.getFeedbackById(chattingId);
                setActiveTicket(current => current?.id === chattingId ? updated : current);
            }
            await fetchFeedback();
        } catch (err) {
            alert((err as Error).message);
        } finally {
            setSending(false);
        }
    };

    const startChatting = (id: number) => {
        setActiveTicket(feedbacks.find(ticket => ticket.id === id) || null);
        setChattingId(id);
        setEditingId(null);
    };

    const closeChat = () => {
        setChattingId(null);
        setEditingId(null);
    };

    const handleDeleteClick = (id: number, e: React.MouseEvent) => {
        e.stopPropagation();
        setDeletingId(id);
    };

    const handleConfirmDelete = async (id: number) => {
        try {
            setDeleteLoading(true);
            await api.deleteFeedback(id);
            setSuccessMsg("Conversation deleted successfully");
            setTimeout(() => setSuccessMsg(null), 3000);
            setDeletingId(null);
            if (chattingId === id) {
                closeChat();
            }
            fetchFeedback();
        } catch (err) {
            console.error("Failed to delete conversation:", err);
            alert("Failed to delete conversation");
        } finally {
            setDeleteLoading(false);
        }
    };


    return (
        <div className="min-h-screen bg-auron-dark p-6 md:p-12">
            <header className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div>
                    <h1 className="text-4xl font-black tracking-tight text-white uppercase italic">CS Dashboard</h1>
                    <p className="text-white/50 mt-2">Manage and respond to customer feedback for AURON.</p>
                </div>

                <div className="flex flex-col gap-4 md:items-end">
                    <div className="flex items-center gap-3">
                        <span className="text-white/40 text-sm font-bold uppercase tracking-widest">Sort by:</span>
                        <select
                            value={sortBy}
                            onChange={(e) => { setSortBy(e.target.value); setPage(0); }}
                            className="bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-sm font-bold text-white focus:outline-none focus:ring-1 focus:ring-auron-orange appearance-none cursor-pointer"
                        >
                            <option value="Urgency">Urgency Priority</option>
                            <option value="Newest">Newest First</option>
                            <option value="Oldest">Oldest First</option>
                            <option value="Sentiment">Sentiment</option>
                            <option value="Category">Category</option>
                        </select>
                    </div>

                    <label className="inline-flex cursor-pointer items-center gap-3 text-sm font-bold text-white/70">
                        <input
                            type="checkbox"
                            role="switch"
                            checked={statusFilter === 'all'}
                            onChange={(event) => { setStatusFilter(event.target.checked ? 'all' : 'open'); setPage(0); }}
                            className="peer sr-only"
                        />
                        <span aria-hidden="true" className="relative h-6 w-11 rounded-full bg-white/15 transition-colors peer-checked:bg-auron-orange peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-auron-orange before:absolute before:left-1 before:top-1 before:h-4 before:w-4 before:rounded-full before:bg-white before:transition-transform peer-checked:before:translate-x-5" />
                        {statusFilter === 'all' ? 'Open tickets only' : 'Show all tickets'}
                    </label>

                    <div className="flex bg-white/5 p-1 rounded-xl border border-white/10">
                        {['All', 'Positive', 'Negative', 'Mixed'].map((f) => (
                            <button
                                key={f}
                                onClick={() => { setFilter(f); setPage(0); }}
                                className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${filter === f ? 'bg-auron-orange text-white shadow-lg' : 'text-white/40 hover:text-white/70'
                                    }`}
                            >
                                {f}
                            </button>
                        ))}
                    </div>
                </div>
            </header>

            <AnimatePresence>
                {successMsg && (
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="fixed top-24 right-12 bg-green-500 text-white px-6 py-3 rounded-full shadow-xl font-bold flex items-center gap-2 z-[60]"
                    >
                        <CheckCircle2 className="w-5 h-5" />
                        {successMsg}
                    </motion.div>
                )}
            </AnimatePresence>

            {loading ? (
                <div className="flex flex-col items-center justify-center h-64 text-white/20">
                    <Loader2 className="w-12 h-12 animate-spin mb-4" />
                    <p className="font-bold uppercase tracking-widest text-sm">Loading Intelligence...</p>
                </div>
            ) : error ? (
                <div className="text-center py-20 bg-red-500/5 rounded-3xl border border-dashed border-red-500/20">
                    <AlertCircle className="w-16 h-16 text-red-500/40 mx-auto mb-4" />
                    <p className="text-red-500/60 font-medium mb-4">{error}</p>
                    <button
                        onClick={fetchFeedback}
                        className="px-6 py-2 bg-white/5 hover:bg-white/10 rounded-full text-sm font-bold transition-all"
                    >
                        Try Again
                    </button>
                </div>
            ) : (
                <>
                    {/* Overview Dashboard Section */}
                    {stats && (
                        <DashboardOverview stats={stats} />
                    )}

                    <div className="mb-4 flex items-center justify-between gap-4 text-sm text-white/60" aria-label="Ticket pages">
                        <button className="rounded-lg border border-white/10 px-4 py-2 disabled:opacity-30" disabled={page === 0 || loading} onClick={() => setPage(page - 1)}>Previous</button>
                        <span>Page {page + 1}</span>
                        <button className="rounded-lg border border-white/10 px-4 py-2 disabled:opacity-30" disabled={!hasMore || loading} onClick={() => setPage(page + 1)}>Next</button>
                    </div>
                    {/* Feedbacks List Block */}
                    {feedbacks.length === 0 ? (
                        <div className="text-center py-20 bg-white/5 rounded-3xl border border-dashed border-white/10">
                            <Inbox className="w-16 h-16 text-white/10 mx-auto mb-4" />
                            <p className="text-white/40 font-medium">No feedback found for the current selection.</p>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 gap-8">
                            {feedbacks.map((f) => (
                                <FeedbackCard key={f.id} feedback={f} onOpen={startChatting} onDelete={handleDeleteClick} />
                            ))}
                        </div>
                    )}
                </>
            )}

            <details className="mb-8 mt-6 bg-[#111] border border-white/5 rounded-3xl p-6">
                <summary className="cursor-pointer text-sm font-bold text-white/60">Escalations · {alerts.filter(item => item.status !== 'resolved').length} active</summary>
                {alerts.filter(item => item.status !== 'resolved').map(item => <div key={item.id} className="mt-4 flex flex-wrap items-center gap-3 border-t border-white/10 pt-3 text-sm">
                    <button className="text-auron-orange" onClick={() => startChatting(item.feedback_id)}>Ticket #{item.feedback_id}</button>
                    <p className="flex-1 min-w-48 text-white/60">{item.reason.startsWith('Manual review required:') || item.reason.startsWith('Analysis failed;') ? 'This feedback needs your review.' : item.reason}</p>
                    {item.status === 'new' && <button disabled={sending} className="text-white/60 underline" onClick={() => void updateTicket(() => api.updateEscalation(item.id, 'acknowledged'))}>Acknowledge</button>}
                    <button disabled={sending} className="text-white/60 underline" onClick={() => void updateTicket(() => api.updateEscalation(item.id, 'resolved'))}>Resolve alert</button>
                </div>)}
            </details>

            <TicketConversation
                chattingId={chattingId} activeTicket={activeTicket} detailError={detailError}
                editingId={editingId} editResponse={editResponse} reviewer={reviewer}
                sending={sending} setEditingId={setEditingId} setEditResponse={setEditResponse}
                setReviewer={setReviewer} closeChat={closeChat}
                handleApprove={handleApprove} updateTicket={updateTicket}
            />
            <DeleteConversationDialog
                deletingId={deletingId} feedback={feedbacks.find(f => f.id === deletingId)}
                deleteLoading={deleteLoading} onClose={() => setDeletingId(null)}
                onConfirm={handleConfirmDelete}
            />
        </div>
    );
};

export default DashboardPage;
