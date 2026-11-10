import type { MouseEvent } from 'react';
import { Clock, Trash2, User } from 'lucide-react';
import { motion } from 'framer-motion';
import type { Feedback } from '../../api';

interface Props {
    feedback: Feedback;
    onOpen: (id: number) => void;
    onDelete: (id: number, event: MouseEvent) => void;
}

/** Display one ticket with its current classification. */
export default function FeedbackCard({ feedback: f, onOpen, onDelete }: Props) {
    return (
        <motion.div
            layout
            key={f.id}
            className={`cursor-pointer transition-all hover:scale-[1.01] hover:bg-white/[0.07] glass-morphism rounded-3xl overflow-hidden border-l-4 ${f.sentiment?.toLowerCase() === 'negative' ? 'border-l-red-500' :
                f.sentiment?.toLowerCase() === 'positive' ? 'border-l-green-500' : 'border-l-yellow-500'
                }`}
            onClick={() => onOpen(f.id)}
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
                                {f.analysis_status === 'failed' ? 'Analysis failed' : f.sentiment || 'Not analyzed'}
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
                                {f.category || 'Unclassified'}
                            </span>
                        </div>
                        <div className="text-[10px] text-white/20 uppercase font-black tracking-widest flex items-center gap-2">
                            <Clock className="w-3 h-3" />
                            Received on {new Date(f.created_at).toLocaleDateString()}
                        </div>
                        <button
                            onClick={(e) => onDelete(f.id, e)}
                            className="p-2 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 hover:border-red-500/40 rounded-xl text-red-400 hover:text-red-300 transition-all flex items-center justify-center"
                            title="Delete Conversation"
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                    </div>
                </div>

                {f.analysis_status === 'pending' && !f.analyses.length && f.sentiment && <p className="mb-3 text-xs text-white/40">Legacy result — reanalyze to verify.</p>}
                {['failed', 'partial'].includes(f.analysis_status) && <p role="status" className="mb-3 text-xs text-white/60">{f.analysis_status === 'partial' ? 'Please write a reply or try again.' : 'Please review this feedback or try again.'}</p>}
                <div className="bg-white/5 rounded-2xl p-6 border border-white/5">
                    <p className="text-white/80 leading-relaxed italic line-clamp-2">"{f.feedback_text}"</p>
                </div>
            </div>
        </motion.div>
    );
}
