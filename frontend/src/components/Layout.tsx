import { useEffect, useState } from 'react';
import { Link, NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, MessageSquare } from 'lucide-react';
import { api, type RuntimeConfig } from '../api';

/** Show navigation and disclose whether results are simulated. */
export default function Layout() {
    const [config, setConfig] = useState<RuntimeConfig | null>(null);
    const [error, setError] = useState('');
    const [token, setToken] = useState('');

    useEffect(() => {
        api.config().then(setConfig).catch(() => setError('Backend unavailable. Check that it is running.'));
    }, []);

    return <div className="flex min-h-screen flex-col">
        <a href="#main" className="skip-link">Skip to content</a>
        <header className="glass-morphism border-b border-white/10 px-5 py-5 md:px-12">
            <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-5">
                <Link to="/" aria-label="AURON overview">
                    <img src="/assets/logo/AURON_LOGO.png" alt="AURON" className="h-9 w-auto" />
                </Link>
                <nav aria-label="Main navigation" className="flex flex-wrap gap-5 text-sm font-semibold">
                    <NavLink to="/" end>Overview</NavLink>
                    <NavLink to="/feedback" className="flex items-center gap-2"><MessageSquare size={16} />Contact us</NavLink>
                    <NavLink to="/dashboard" className="flex items-center gap-2"><LayoutDashboard size={16} />Dashboard</NavLink>
                </nav>
            </div>
        </header>
        {(!config || config.mode === 'demo') && <div className="border-b border-white/10 bg-white/[0.04] px-5 py-3 text-center text-sm text-white/75" role="status">
            {config?.mode === 'demo'
                ? 'Demo mode · Synthetic examples and simulated English keyword analysis. No API calls or emails.'
                : error || 'Connecting to CustomerLens…'}
        </div>}
        {config?.requires_token && <form className="mx-auto flex w-full max-w-xl flex-wrap gap-3 p-4" onSubmit={event => {
            event.preventDefault();
            sessionStorage.setItem('customerlens-token', token);
            window.location.reload();
        }}>
            <label htmlFor="access-token" className="w-full text-sm">API access token</label>
            <input id="access-token" type="password" autoComplete="off" value={token} onChange={event => setToken(event.target.value)} className="field flex-1" required />
            <button className="action" type="submit">Connect</button>
        </form>}
        <main id="main" className="flex-1"><Outlet /></main>
        <footer className="border-t border-white/10 px-6 py-8 text-center text-sm text-white/50">
            CustomerLens · A portfolio project for fictional bike brand AURON
        </footer>
    </div>;
}
