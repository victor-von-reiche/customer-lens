import { useState, type FormEvent } from 'react';
import type { Feedback } from '../api';
import { api } from '../api';
import { Send, CheckCircle2, MessageSquare, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const FeedbackPage = () => {
    const [formData, setFormData] = useState({
        customer_name: '',
        customer_email: '',
        feedback_text: ''
    });
    const [loading, setLoading] = useState(false);
    const [submitted, setSubmitted] = useState<Feedback | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        try {
            const result = await api.submitFeedback(formData);
            setSubmitted(result);
        } catch (error) {
            console.error("Feedback submission error:", error);
            setError('Something went wrong. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-auron-navy">
            {/* Hero Section */}
            <section className="relative h-[60vh] flex items-center justify-center overflow-hidden">
                <div className="absolute inset-0">
                    <img
                        src="/assets/bikes/feedback_background.png"
                        alt="AURON Premium Bike"
                        className="w-full h-full object-cover opacity-60 scale-105"
                    />
                    <div className="absolute inset-0 bg-gradient-to-b from-auron-navy/20 via-auron-navy/40 to-auron-navy" />
                </div>

                <div className="relative z-10 text-center px-4">
                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-5xl md:text-7xl font-black tracking-tighter text-white uppercase italic mb-4"
                    >
                        Your Feedback <span className="text-auron-orange">Drives Us</span>
                    </motion.h1>
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="text-xl text-white/80 max-w-2xl mx-auto"
                    >
                        Help us redefine the boundaries of performance and engineering.
                    </motion.p>
                </div>
            </section>

            {/* Form Section */}
            <section className="max-w-4xl mx-auto px-6 pb-24 -mt-20 relative z-20">
                <AnimatePresence mode="wait">
                    {!submitted ? (
                        <motion.div
                            key="form"
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            className="glass-morphism rounded-3xl p-8 md:p-12 shadow-2xl shadow-black/50"
                        >
                            <h2 className="text-3xl font-bold mb-8 flex items-center gap-3">
                                <MessageSquare className="text-auron-orange w-8 h-8" />
                                Share Your Experience
                            </h2>

                            <form onSubmit={handleSubmit} className="space-y-6">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                    <div>
                                        <label className="block text-sm font-medium text-white/60 mb-2">Full Name</label>
                                        <input
                                            required
                                            type="text"
                                            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-auron-orange focus:ring-1 focus:ring-auron-orange transition-all"
                                            placeholder="Enter your name"
                                            value={formData.customer_name}
                                            onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-white/60 mb-2">Email Address</label>
                                        <input
                                            required
                                            type="email"
                                            className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-auron-orange focus:ring-1 focus:ring-auron-orange transition-all"
                                            placeholder="Enter your email"
                                            value={formData.customer_email}
                                            onChange={(e) => setFormData({ ...formData, customer_email: e.target.value })}
                                        />
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-white/60 mb-2">Your Feedback</label>
                                    <textarea
                                        required
                                        rows={5}
                                        className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 focus:outline-none focus:border-auron-orange focus:ring-1 focus:ring-auron-orange transition-all resize-none"
                                        placeholder="Tell us about your AURON experience..."
                                        value={formData.feedback_text}
                                        onChange={(e) => setFormData({ ...formData, feedback_text: e.target.value })}
                                    />
                                </div>

                                {error && (
                                    <div className="bg-red-500/10 border border-red-500/50 text-red-500 px-4 py-3 rounded-xl text-sm">
                                        {error}
                                    </div>
                                )}

                                <button
                                    disabled={loading}
                                    type="submit"
                                    className="btn-primary w-full md:w-auto flex items-center justify-center gap-3"
                                >
                                    {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                                    {loading ? 'Submitting...' : 'Submit Feedback'}
                                </button>
                            </form>
                        </motion.div>
                    ) : (
                        <motion.div
                            key="success"
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="glass-morphism rounded-3xl p-8 md:p-24 shadow-2xl text-center"
                        >
                            <div className="bg-green-500/20 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-10 border border-green-500/30">
                                <CheckCircle2 className="w-10 h-10 text-green-500" />
                            </div>
                            <h2 className="text-4xl md:text-5xl font-black mb-6 uppercase italic">Thank You, {submitted.customer_name}!</h2>
                            <p className="text-white/60 text-xl font-medium">Your feedback has been received and is being reviewed by our team.</p>

                            <button
                                onClick={() => setSubmitted(null)}
                                className="mt-16 text-auron-orange font-black uppercase tracking-widest text-sm hover:underline"
                            >
                                Submit another feedback
                            </button>
                        </motion.div>
                    )}
                </AnimatePresence>
            </section>
        </div>
    );
};

export default FeedbackPage;
