import { Loader2, Trash2 } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import type { Feedback } from '../../api';

interface Props {
    deletingId: number | null;
    feedback: Feedback | undefined;
    deleteLoading: boolean;
    onClose: () => void;
    onConfirm: (id: number) => Promise<void>;
}

/** Confirm deletion of the selected conversation. */
export default function DeleteConversationDialog({
    deletingId, feedback, deleteLoading, onClose, onConfirm,
}: Props) {
    return (
                    <AnimatePresence>
            {deletingId && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/70 backdrop-blur-md"
                    onClick={() => onClose()}
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
                            Are you sure you want to delete the conversation with <strong className="text-white">{feedback?.customer_name}</strong> ({feedback?.customer_email})? All messages will be permanently removed from the database.
                        </p>

                        <div className="flex gap-3 justify-end mt-2">
                            <button
                                onClick={() => onClose()}
                                className="px-5 py-2.5 bg-white/5 hover:bg-white/10 rounded-xl text-sm font-bold text-white/80 transition-all border border-white/5"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() => onConfirm(deletingId)}
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
    );
}
