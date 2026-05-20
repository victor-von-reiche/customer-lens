import { useEffect, useState } from 'react';
import type { Feedback, Message, DashboardStats } from '../api';
import { api } from '../api';
import {
    CheckCircle2,
    Clock,
    Edit3,
    Send,
    User,
    Loader2,
    Inbox,
    AlertCircle,
    Trash2
} from 'lucide-react';
import { motion, AnimatePresence, useMotionValue, useTransform, animate } from 'framer-motion';

const AnimatedNumber = ({ value }: { value: number }) => {
    const motionValue = useMotionValue(0);
    const rounded = useTransform(motionValue, (latest) => Math.round(latest));

    useEffect(() => {
        const controls = animate(motionValue, value, { duration: 2, ease: "easeOut" });
        return controls.stop;
    }, [value, motionValue]);

    return <motion.span>{rounded}</motion.span>;
};

const DashboardPage = () => {
    const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
    const [stats, setStats] = useState<DashboardStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('All');
    const [sortBy, setSortBy] = useState('Urgency');
    const [chattingId, setChattingId] = useState<string | null>(null);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editResponse, setEditResponse] = useState('');
    const [successMsg, setSuccessMsg] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [deletingId, setDeletingId] = useState<string | null>(null);
    const [deleteLoading, setDeleteLoading] = useState(false);

    const fetchFeedback = async () => {
        try {
            setLoading(true);
            const [data, statsData] = await Promise.all([
                api.getAllFeedback(filter, sortBy),
                api.getDashboardStats()
            ]);
            setFeedbacks(data);
            setStats(statsData);
            setError(null);
        } catch (err) {
            console.error(err);
            setError((err as Error).message || "Failed to fetch dashboard data. Make sure the backend is running at http://localhost:8000");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchFeedback();
    }, [filter, sortBy]);

    const handleApprove = async (id: string, response: string) => {
        try {
            await api.approveFeedback(id, response);
            setSuccessMsg("Response sent to customer");
            setTimeout(() => setSuccessMsg(null), 3000);
            setEditingId(null);
            setEditResponse('');
            // Refresh to show the new message in history
            fetchFeedback();
        } catch (err) {
            console.error("Failed to approve:", err);
            alert("Failed to approve");
        }
    };

    const startEditing = (id: string, currentResponse: string) => {
        setEditingId(id);
        setEditResponse(currentResponse);
    };

    const startWritingOwn = (id: string, e?: React.MouseEvent) => {
        if (e) e.stopPropagation();
        setEditingId(id);
        setEditResponse('');
    };

    const startChatting = (id: string) => {
        setChattingId(id);
        setEditingId(null);
    };

    const closeChat = () => {
        setChattingId(null);
        setEditingId(null);
    };

    const handleDeleteClick = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setDeletingId(id);
    };

    const handleConfirmDelete = async (id: string) => {
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
                            onChange={(e) => setSortBy(e.target.value)}
                            className="bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-sm font-bold text-white focus:outline-none focus:ring-1 focus:ring-auron-orange appearance-none cursor-pointer"
                        >
                            <option value="Urgency">Urgency Priority</option>
                            <option value="Newest">Newest First</option>
                            <option value="Oldest">Oldest First</option>
                            <option value="Sentiment">Sentiment</option>
                            <option value="Category">Category</option>
                        </select>
                    </div>

                    <div className="flex bg-white/5 p-1 rounded-xl border border-white/10">
                        {['All', 'Positive', 'Negative', 'Mixed'].map((f) => (
                            <button
                                key={f}
                                onClick={() => setFilter(f)}
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
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8 mt-12">
                                {/* STATS OVERVIEW */}
                                <div className="bg-[#111] border border-white/5 rounded-3xl p-6 flex flex-col gap-4">
                                    <h2 className="text-white/40 text-[10px] font-black uppercase tracking-[0.2em] mb-2">Stats Overview</h2>
                                    
                                    <div className="flex items-center justify-between p-4 bg-white/[0.03] rounded-2xl border border-white/5">
                                        <div>
                                            <div className="text-white/40 text-[10px] uppercase font-bold tracking-widest mb-1">Total Feedbacks</div>
                                            <div className="text-3xl font-black text-white">{stats.total_count}</div>
                                        </div>
                                        <div className="w-10 h-10 rounded-full flex items-center justify-center bg-white/5">
                                            <User className="w-4 h-4 text-white/40" />
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-between p-4 bg-white/[0.03] rounded-2xl border border-white/5">
                                        <div>
                                            <div className="text-white/40 text-[10px] uppercase font-bold tracking-widest mb-1">Open Tickets</div>
                                            <div className="text-3xl font-black text-white">{stats.open_count}</div>
                                        </div>
                                        <div className="w-10 h-10 rounded-full flex items-center justify-center bg-white/5">
                                            <div className="w-3 h-3 rounded-full bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]"></div>
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-between p-4 bg-white/[0.03] rounded-2xl border border-white/5">
                                        <div>
                                            <div className="text-white/40 text-[10px] uppercase font-bold tracking-widest mb-1">Closed Tickets</div>
                                            <div className="text-3xl font-black text-white">{stats.closed_count}</div>
                                        </div>
                                        <div className="w-10 h-10 rounded-full flex items-center justify-center bg-white/5">
                                            <CheckCircle2 className="w-5 h-5 text-green-500" />
                                        </div>
                                    </div>
                                </div>

                                {/* AVERAGE CUSTOMER SATISFACTION (GAUGE) */}
                                <div className="bg-[#111] border border-white/5 rounded-3xl p-6 flex flex-col relative overflow-hidden items-center text-center">
                                    <h2 className="text-white/40 text-[10px] font-black uppercase tracking-[0.2em] mb-4 z-10 w-full text-center">Average Customer Satisfaction</h2>

                                    <div className="text-auron-orange text-xs font-black tracking-widest uppercase mb-4 z-10">
                                        {stats.satisfaction_score >= 80 ? 'Excellent' : stats.satisfaction_score >= 60 ? 'Fair' : 'Critical'}
                                    </div>

                                    {/* Grid Background */}
                                    <div className="absolute inset-x-4 top-24 bottom-4 bg-[linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:20px_20px] rounded-xl pointer-events-none border border-white/5" />
                                    
                                    <div className="relative w-full max-w-[300px] mt-auto flex flex-col items-center justify-center z-10 pt-8 pb-2">
                                        {/* Half Gauge SVG */}
                                        <svg viewBox="0 0 100 56" className="w-full overflow-visible drop-shadow-[0_0_15px_rgba(0,0,0,0.5)]">
                                            <defs>
                                                <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                                    <stop offset="0%" stopColor="#ef4444" />
                                                    <stop offset="50%" stopColor="#f59e0b" />
                                                    <stop offset="100%" stopColor="#22c55e" />
                                                </linearGradient>
                                            </defs>
                                            
                                            {/* Gauge Arc Background Track */}
                                            <path d="M 5 50 A 45 45 0 0 1 95 50" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" strokeLinecap="round" />
                                            
                                            {/* Gauge Arc Color Fill */}
                                            <motion.path 
                                                d="M 5 50 A 45 45 0 0 1 95 50" 
                                                fill="none" 
                                                stroke="url(#gaugeGradient)" 
                                                strokeWidth="10" 
                                                strokeLinecap="round"
                                                initial={{ strokeDasharray: 141.37, strokeDashoffset: 141.37 }}
                                                animate={{ strokeDashoffset: 141.37 - (stats.satisfaction_score / 100) * 141.37 }}
                                                transition={{ duration: 1.5, ease: "easeOut" }}
                                            />

                                            {/* Needle Group */}
                                            <motion.g 
                                                initial={{ rotate: -180 }}
                                                animate={{ rotate: -180 + (stats.satisfaction_score / 100) * 180 }}
                                                transition={{ type: "spring", bounce: 0.4, duration: 2 }}
                                            >
                                                {/* Transparent circle ensures the bounding box is perfectly centered for Framer Motion */}
                                                <circle cx="50" cy="50" r="40" fill="transparent" />
                                                <line x1="50" y1="50" x2="88" y2="50" stroke="rgba(255,255,255,0.9)" strokeWidth="1.5" strokeLinecap="round" />
                                                <circle cx="88" cy="50" r="2.5" fill="white" style={{ filter: 'drop-shadow(0 0 5px rgba(255,255,255,0.8))' }} />
                                            </motion.g>

                                            {/* Center Pin */}
                                            <circle cx="50" cy="50" r="4" fill="#1a1a1a" stroke="rgba(255,255,255,0.2)" strokeWidth="1" />
                                            <circle cx="50" cy="50" r="1.5" fill="rgba(255,255,255,0.5)" />
                                        </svg>

                                        <div className="absolute left-[-5px] bottom-[-15px] text-[12px] uppercase font-black tracking-widest text-[#ef4444] drop-shadow-[0_0_12px_rgba(239,68,68,0.7)]">Critical</div>
                                        <div className="absolute right-[-15px] bottom-[-15px] text-[12px] uppercase font-black tracking-widest text-[#22c55e] drop-shadow-[0_0_12px_rgba(34,197,94,0.7)]">Excellent</div>
                                    </div>

                                    <div className="mt-2 text-6xl font-black text-white text-center w-full z-10 tracking-tighter">
                                        <AnimatedNumber value={stats.satisfaction_score} />%
                                    </div>
                                </div>

                                {/* DAILY REPORT */}
                                <div className="bg-[#111] border border-white/5 rounded-3xl p-6 flex flex-col gap-6">
                                    <h2 className="text-white/40 text-[10px] font-black uppercase tracking-[0.2em]">Daily Report</h2>
                                    
                                    <div className="flex items-center gap-3">
                                        <div className="text-xl">📊</div>
                                        <h3 className="text-white font-bold text-lg">Daily Report - {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</h3>
                                    </div>

                                    <div className="flex flex-col gap-5 mt-2">
                                        <div className="flex items-center gap-4 text-white/80">
                                            <div className="w-6 h-6 rounded flex items-center justify-center flex-shrink-0 relative">
                                                 <div className="absolute inset-0 bg-green-500/20 rounded"></div>
                                                 <CheckCircle2 className="w-4 h-4 text-green-500 relative z-10" />
                                            </div>
                                            <span className="text-sm"><strong className="text-white">{stats.processed_today}</strong> feedbacks processed</span>
                                        </div>
                                        
                                        <div className="flex items-center gap-4 text-white/80">
                                            <div className="w-6 h-6 rounded flex items-center justify-center flex-shrink-0 relative">
                                                <div className="absolute inset-0 bg-red-500/20 rounded"></div>
                                                <div className="text-red-500 relative z-10 font-bold text-xs">✕</div>
                                            </div>
                                            <span className="text-sm"><strong className="text-white">{stats.critical_today}</strong> critical ({stats.critical_resolved_today} resolved)</span>
                                        </div>
                                        
                                        <div className="flex items-center gap-4 text-white/80">
                                            <div className="w-6 h-6 rounded flex items-center justify-center flex-shrink-0 relative">
                                                <div className="absolute inset-0 bg-yellow-500/20 rounded"></div>
                                                <div className="text-yellow-500 relative z-10 text-xs">⭐</div>
                                            </div>
                                            <span className="text-sm"><strong className="text-white">{stats.positive_today}</strong> positive</span>
                                        </div>
                                        
                                        <div className="flex items-center gap-4 text-white/80">
                                            <div className="w-6 h-6 rounded flex items-center justify-center flex-shrink-0 relative">
                                                <div className="absolute inset-0 bg-blue-500/20 rounded"></div>
                                                <div className="text-blue-500 relative z-10 text-xs text-center flex items-end justify-center h-full pb-1"><div className="w-[2px] h-[6px] bg-blue-500 mx-[1px]" /><div className="w-[2px] h-[10px] bg-blue-500 mx-[1px]" /><div className="w-[2px] h-[14px] bg-blue-500 mx-[1px]" /></div>
                                            </div>
                                            <span className="text-sm"><strong className="text-white">{stats.satisfaction_today}%</strong> satisfaction today</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                    )}

                    {/* Feedbacks List Block */}
                    {feedbacks.length === 0 ? (
                        <div className="text-center py-20 bg-white/5 rounded-3xl border border-dashed border-white/10">
                            <Inbox className="w-16 h-16 text-white/10 mx-auto mb-4" />
                            <p className="text-white/40 font-medium">No feedback found for the current selection.</p>
                        </div>
                    ) : (
                                <div className="grid grid-cols-1 gap-8">
                                    {feedbacks.map((f) => (
                                        <motion.div
                                            layout
                                            key={f.id}
                                            className={`cursor-pointer transition-all hover:scale-[1.01] hover:bg-white/[0.07] glass-morphism rounded-3xl overflow-hidden border-l-4 ${f.sentiment?.toLowerCase() === 'negative' ? 'border-l-red-500' :
                                                f.sentiment?.toLowerCase() === 'positive' ? 'border-l-green-500' : 'border-l-yellow-500'
                                                }`}
                                            onClick={() => startChatting(f.id)}
                                        >
                                            <div className="p-8">
                                                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
                                                    <div className="flex items-center gap-4">
                                                        <div className="w-12 h-12 rounded-full bg-white/10 flex items-center justify-center text-auron-orange">
                                                            <User className="w-6 h-6" />
                                                        </div>
                                                        <div>
                                                            <h3 className="text-xl font-bold">{f.customer_name}</h3>
                                                            <p className="text-white/40 text-sm">{f.customer_email}</p>
                                                        </div>
                                                    </div>
                                                    <div className="flex flex-wrap items-center gap-3">
                                                        <div className="flex gap-2">
                                                            <span className={`px-4 py-1.5 rounded-full text-xs font-black uppercase tracking-widest ${f.sentiment?.toLowerCase() === 'positive' ? 'bg-green-500/10 text-green-400 border border-green-500/20' :
                                                                f.sentiment?.toLowerCase() === 'negative' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                                                                    'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                                                                }`}>
                                                                {f.sentiment}
                                                            </span>
                                                            {f.urgency && (
                                                                <span className={`px-4 py-1.5 rounded-full text-xs font-black uppercase tracking-widest ${
                                                                    f.urgency.toLowerCase() === 'critical' ? 'bg-red-600/20 text-red-500 border border-red-600/30 shadow-[0_0_15px_rgba(239,68,68,0.3)]' :
                                                                    f.urgency.toLowerCase() === 'high' ? 'bg-orange-500/20 text-auron-orange border border-orange-500/30' :
                                                                    f.urgency.toLowerCase() === 'medium' ? 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' :
                                                                    'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                                                                }`}>
                                                                    {f.urgency} Urgency
                                                                </span>
                                                            )}
                                                            <span className="bg-white/5 px-4 py-1.5 rounded-full text-xs font-black uppercase tracking-widest text-white/60 border border-white/10">
                                                                {f.category}
                                                            </span>
                                                        </div>
                                                        <div className="text-[10px] text-white/20 uppercase font-black tracking-widest flex items-center gap-2">
                                                            <Clock className="w-3 h-3" />
                                                            Received on {new Date(f.created_at).toLocaleDateString()}
                                                        </div>
                                                        <button
                                                            onClick={(e) => handleDeleteClick(f.id, e)}
                                                            className="p-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 hover:border-red-500/40 rounded-xl text-red-400 hover:text-red-300 transition-all flex items-center justify-center"
                                                            title="Delete Conversation"
                                                        >
                                                            <Trash2 className="w-4 h-4" />
                                                        </button>
                                                    </div>
                                                </div>

                                                <div className="bg-white/5 rounded-2xl p-6 border border-white/5">
                                                    <p className="text-white/80 leading-relaxed italic line-clamp-2">"{f.feedback_text}"</p>
                                                </div>
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>
                            )}
                        </>
                    )}

            {/* Chat Window Modal */}
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
                            const activeFeedback = feedbacks.find(f => f.id === chattingId);
                            if (!activeFeedback) return null;
                            
                            return (
                                <motion.div
                                    initial={{ scale: 0.95, y: 20 }}
                                    animate={{ scale: 1, y: 0 }}
                                    exit={{ scale: 0.95, y: 20 }}
                                    onClick={(e) => e.stopPropagation()}
                                    className="bg-auron-dark w-full max-w-3xl max-h-[90vh] rounded-3xl overflow-hidden border border-white/10 flex flex-col shadow-2xl"
                                >
                                    {/* Chat Header */}
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

                                    {/* Chat Messages */}
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

                                    {/* Permanent Reply Area */}
                                    <div className="p-4 border-t border-white/10 bg-white/[0.02]">
                                        {activeFeedback.ai_response && activeFeedback.messages?.[activeFeedback.messages.length - 1]?.sender === 'customer' && editingId !== activeFeedback.id && (
                                            <div className="flex items-center gap-2 mb-2">
                                                <span className="text-[10px] text-auron-orange/50">Draft created by AI</span>
                                            </div>
                                        )}
                                        <div className="flex gap-3">
                                            <textarea
                                                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white/90 leading-relaxed focus:outline-none focus:border-auron-orange focus:ring-1 focus:ring-auron-orange resize-none min-h-[80px]"
                                                placeholder="Type your reply..."
                                                value={editingId === activeFeedback.id ? editResponse : (
                                                    activeFeedback.messages?.[activeFeedback.messages.length - 1]?.sender === 'customer' 
                                                    ? (activeFeedback.ai_response || '') 
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
                                                            ? (activeFeedback.ai_response || '')
                                                            : '';
                                                        setEditingId(activeFeedback.id);
                                                        setEditResponse(currentVal);
                                                    }
                                                }}
                                            />
                                            <div className="flex flex-col gap-2 self-end">
                                                {activeFeedback.ai_response && activeFeedback.messages?.[activeFeedback.messages.length - 1]?.sender === 'customer' && (
                                                    <button
                                                        onClick={() => {
                                                            if (editingId === activeFeedback.id) {
                                                                setEditingId(null);
                                                            } else {
                                                                setEditingId(activeFeedback.id);
                                                                setEditResponse(activeFeedback.ai_response);
                                                            }
                                                        }}
                                                        className="flex items-center justify-center gap-2 bg-blue-600/80 hover:bg-blue-500 text-white text-xs font-bold py-3 px-5 rounded-xl transition-all border border-blue-500/50"
                                                    >
                                                        <Edit3 className="w-4 h-4" />
                                                        {editingId === activeFeedback.id ? 'Cancel' : 'Edit'}
                                                    </button>
                                                )}
                                                <button
                                                    onClick={() => {
                                                        const content = editingId === activeFeedback.id 
                                                            ? editResponse 
                                                            : (activeFeedback.messages?.[activeFeedback.messages.length - 1]?.sender === 'customer' ? (activeFeedback.ai_response || '') : '');
                                                        if (content.trim()) {
                                                            handleApprove(activeFeedback.id, content);
                                                        }
                                                    }}
                                                    className="flex items-center justify-center gap-2 bg-green-600/80 hover:bg-green-500 text-white text-xs font-bold py-3 px-5 rounded-xl transition-all border border-green-500/50"
                                                >
                                                    <Send className="w-4 h-4" />
                                                    Send
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

            {/* Delete Confirmation Modal */}
            <AnimatePresence>
                {deletingId && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/70 backdrop-blur-md"
                        onClick={() => setDeletingId(null)}
                    >
                        <motion.div
                            initial={{ scale: 0.95, y: 20 }}
                            animate={{ scale: 1, y: 0 }}
                            exit={{ scale: 0.95, y: 20 }}
                            onClick={(e) => e.stopPropagation()}
                            className="bg-[#111] border border-white/10 w-full max-w-md rounded-3xl p-8 flex flex-col gap-6 shadow-2xl relative overflow-hidden"
                        >
                            <div className="absolute top-0 left-0 w-full h-1.5 bg-red-500" />
                            
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-full bg-red-500/15 flex items-center justify-center text-red-500 border border-red-500/10">
                                    <Trash2 className="w-6 h-6" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-bold text-white">Delete Conversation</h3>
                                    <p className="text-white/40 text-xs mt-1">This action cannot be undone.</p>
                                </div>
                            </div>
                            
                            <p className="text-white/70 text-sm leading-relaxed">
                                Are you sure you want to delete the conversation with <strong className="text-white">{feedbacks.find(f => f.id === deletingId)?.customer_name}</strong> ({feedbacks.find(f => f.id === deletingId)?.customer_email})? All messages will be permanently removed from the database.
                            </p>
                            
                            <div className="flex gap-3 justify-end mt-2">
                                <button
                                    onClick={() => setDeletingId(null)}
                                    className="px-5 py-2.5 bg-white/5 hover:bg-white/10 rounded-xl text-sm font-bold text-white/80 transition-all border border-white/5"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={() => handleConfirmDelete(deletingId)}
                                    disabled={deleteLoading}
                                    className="px-5 py-2.5 bg-red-600/80 hover:bg-red-500 disabled:bg-red-600/40 text-white rounded-xl text-sm font-bold transition-all border border-red-500/50 flex items-center gap-2"
                                >
                                    {deleteLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                                    Delete
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default DashboardPage;
