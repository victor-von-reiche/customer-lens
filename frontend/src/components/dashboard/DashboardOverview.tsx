import { useEffect } from 'react';
import { CheckCircle2, User } from 'lucide-react';
import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import type { DashboardStats } from '../../api';

const AnimatedNumber = ({ value }: { value: number }) => {
    const motionValue = useMotionValue(0);
    const rounded = useTransform(motionValue, (latest) => Math.round(latest));

    useEffect(() => {
        const controls = animate(motionValue, value, { duration: 2, ease: "easeOut" });
        return controls.stop;
    }, [value, motionValue]);

    return <motion.span>{rounded}</motion.span>;
};

/** Display ticket counts, the sentiment gauge, and the daily report. */
export default function DashboardOverview({ stats }: { stats: DashboardStats }) {
    const gaugeValue = stats.non_negative_sentiment_percent ?? 0;
    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8 mt-12">

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
                        <div className="text-white/40 text-[10px] uppercase font-bold tracking-widest mb-1">Resolved Tickets</div>
                        <div className="text-3xl font-black text-white">{stats.resolved_count}</div>
                    </div>
                    <div className="w-10 h-10 rounded-full flex items-center justify-center bg-white/5">
                        <CheckCircle2 className="w-5 h-5 text-green-500" />
                    </div>
                </div>
            </div>

            <div className="bg-[#111] border border-white/5 rounded-3xl p-6 flex flex-col relative overflow-hidden items-center text-center">
                <h2 className="text-white/40 text-[10px] font-black uppercase tracking-[0.2em] mb-4 z-10 w-full text-center">Customer Sentiment</h2>

                <div className="text-auron-orange text-xs font-black tracking-widest uppercase mb-4 z-10">
                    {stats.non_negative_sentiment_percent === null ? 'No completed analyses yet' : gaugeValue >= 80 ? 'Excellent' : gaugeValue >= 60 ? 'Fair' : 'Critical'}
                </div>

                <div className="absolute inset-x-4 top-24 bottom-4 bg-[linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:20px_20px] rounded-xl pointer-events-none border border-white/5" />

                <div className="relative w-full max-w-[300px] mt-auto flex flex-col items-center justify-center z-10 pt-8 pb-2">

                    <svg role="img" aria-label={stats.non_negative_sentiment_percent === null ? 'No completed analyses' : `Non-negative customer sentiment: ${gaugeValue} percent`} viewBox="0 0 100 56" className="w-full overflow-visible drop-shadow-[0_0_15px_rgba(0,0,0,0.5)]">
                        <defs>
                            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                <stop offset="0%" stopColor="#ef4444" />
                                <stop offset="50%" stopColor="#f59e0b" />
                                <stop offset="100%" stopColor="#22c55e" />
                            </linearGradient>
                        </defs>

                        <path d="M 5 50 A 45 45 0 0 1 95 50" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="10" strokeLinecap="round" />

                        <motion.path
                            d="M 5 50 A 45 45 0 0 1 95 50"
                            fill="none"
                            stroke="url(#gaugeGradient)"
                            strokeWidth="10"
                            strokeLinecap="round"
                            initial={{ strokeDasharray: 141.37, strokeDashoffset: 141.37 }}
                            animate={{ strokeDashoffset: 141.37 - (gaugeValue / 100) * 141.37 }}
                            transition={{ duration: 1.5, ease: "easeOut" }}
                        />

                        <motion.g
                            initial={{ rotate: -180 }}
                            animate={{ rotate: -180 + (gaugeValue / 100) * 180 }}
                            transition={{ type: "spring", bounce: 0.4, duration: 2 }}
                        >
                            {/* Transparent circle ensures the bounding box is perfectly centered for Framer Motion */}
                            <circle cx="50" cy="50" r="40" fill="transparent" />
                            <line x1="50" y1="50" x2="88" y2="50" stroke="rgba(255,255,255,0.9)" strokeWidth="1.5" strokeLinecap="round" />
                            <circle cx="88" cy="50" r="2.5" fill="white" style={{ filter: 'drop-shadow(0 0 5px rgba(255,255,255,0.8))' }} />
                        </motion.g>

                        <circle cx="50" cy="50" r="4" fill="#1a1a1a" stroke="rgba(255,255,255,0.2)" strokeWidth="1" />
                        <circle cx="50" cy="50" r="1.5" fill="rgba(255,255,255,0.5)" />
                    </svg>

                    <div className="absolute left-[-5px] bottom-[-15px] text-[12px] uppercase font-black tracking-widest text-[#ef4444] drop-shadow-[0_0_12px_rgba(239,68,68,0.7)]">Critical</div>
                    <div className="absolute right-[-15px] bottom-[-15px] text-[12px] uppercase font-black tracking-widest text-[#22c55e] drop-shadow-[0_0_12px_rgba(34,197,94,0.7)]">Excellent</div>
                </div>

                <div className="mt-2 text-6xl font-black text-white text-center w-full z-10 tracking-tighter">
                    {stats.non_negative_sentiment_percent === null ? '—' : <><AnimatedNumber value={gaugeValue} />%</>}
                </div>
                <p className="mt-3 text-[10px] text-white/40 z-10">Non-negative share of {stats.analyzed_count} analyzed tickets, including saved legacy results. Not surveyed CSAT.</p>
            </div>

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
                        <span className="text-sm"><strong className="text-white">{stats.created_today}</strong> tickets received (UTC)</span>
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
                        <span className="text-sm"><strong className="text-white">{stats.non_negative_sentiment_today_percent ?? '—'}%</strong> non-negative sentiment today</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
