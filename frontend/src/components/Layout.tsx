import React from 'react';
import { Link, NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, Search, User, ShoppingCart } from 'lucide-react';

const Layout: React.FC = () => {
    return (
        <div className="flex flex-col min-h-screen">
            <header className="sticky top-0 z-50 glass-morphism py-5 px-6 md:px-12 flex items-center justify-between border-b border-white/10">
                <Link to="/" className="flex items-center group">
                    <img src="/assets/logo/AURON_LOGO.png" alt="AURON" className="h-10 w-auto" style={{ mixBlendMode: 'screen' }} />
                </Link>

                <nav className="hidden lg:flex items-center">
                    {/* Customer Links */}
                    <div className="flex items-center gap-6 mr-8 text-[11px] font-black tracking-[0.15em] uppercase text-white/90">
                        <Link to="#" className="hover:text-auron-orange transition-colors duration-300">BIKES</Link>
                        <Link to="#" className="hover:text-auron-orange transition-colors duration-300">GEAR</Link>
                        <Link to="#" className="hover:text-auron-orange transition-colors duration-300">TECHNOLOGY</Link>
                        <Link to="#" className="hover:text-auron-orange transition-colors duration-300">COMMUNITY</Link>
                        <Link to="#" className="hover:text-auron-orange transition-colors duration-300">ABOUT US</Link>
                    </div>

                    {/* Customer Icons */}
                    <div className="flex items-center gap-5 mr-8 text-white/90">
                        <button className="hover:text-auron-orange transition-colors"><Search className="w-4 h-4" /></button>
                        <button className="hover:text-auron-orange transition-colors"><User className="w-4 h-4" /></button>
                        <button className="hover:text-auron-orange transition-colors relative">
                            <ShoppingCart className="w-4 h-4" />
                            <span className="absolute -top-1.5 -right-2 bg-auron-orange text-white text-[8px] w-3.5 h-3.5 rounded-full flex items-center justify-center font-bold">0</span>
                        </button>
                    </div>

                    {/* Employee Links (Admin tools) */}
                    <div className="flex items-center gap-6 border-l border-white/20 pl-8 text-[11px] font-bold tracking-widest uppercase">
                        <NavLink
                            to="/feedback"
                            className={({ isActive }) => `flex items-center gap-2 transition-colors ${isActive ? 'text-auron-orange' : 'text-white/50 hover:text-white'}`}
                        >
                            <MessageSquare className="w-3.5 h-3.5" />
                            <span>Contact us</span>
                        </NavLink>
                        <NavLink
                            to="/dashboard"
                            className={({ isActive }) => `flex items-center gap-2 transition-colors ${isActive ? 'text-auron-orange' : 'text-white/50 hover:text-white'}`}
                        >
                            <LayoutDashboard className="w-3.5 h-3.5" />
                            <span>Dashboard</span>
                        </NavLink>
                    </div>
                </nav>
            </header>
            <main className="flex-1">
                <Outlet />
            </main>
            <footer className="py-8 px-6 md:px-12 border-t border-white/10 text-center text-white/50 text-sm">
                © {new Date().getFullYear()} AURON Road Bikes. Performance, Redefined.
            </footer>
        </div>
    );
};

export default Layout;
