import React from 'react';
import { AppView } from '../types';
import { Leaf, MessageSquare, BarChart3, Settings, ShieldCheck, FileCheck, BookOpen, Search } from 'lucide-react';

interface LayoutProps {
  currentView: AppView;
  setView: (view: AppView) => void;
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ currentView, setView, children }) => {
  const navItemClass = (view: AppView) =>
    `flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 cursor-pointer ${
      currentView === view
        ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-200'
        : 'text-slate-500 hover:bg-slate-100'
    }`;

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col p-4 z-20">
        <div className="flex items-center gap-2 px-2 mb-8 mt-2">
          <div className="w-8 h-8 bg-emerald-600 rounded-lg flex items-center justify-center">
            <Leaf className="text-white w-5 h-5" />
          </div>
          <h1 className="text-xl font-bold text-slate-800 tracking-tight">CeramETS AI</h1>
        </div>

        <nav className="space-y-2 flex-1">
          <div
            className={navItemClass(AppView.LANDING)}
            onClick={() => setView(AppView.LANDING)}
          >
            <ShieldCheck size={20} />
            <span className="font-medium">Overview</span>
          </div>
          <div
            className={navItemClass(AppView.CONSULTATION)}
            onClick={() => setView(AppView.CONSULTATION)}
          >
            <MessageSquare size={20} />
            <span className="font-medium">AI Consultant</span>
          </div>
          <div
            className={navItemClass(AppView.LIBRARY)}
            onClick={() => setView(AppView.LIBRARY)}
          >
            <BookOpen size={20} />
            <span className="font-medium">Regulatory Lib</span>
          </div>
          <div
            className={navItemClass(AppView.DASHBOARD)}
            onClick={() => setView(AppView.DASHBOARD)}
          >
            <BarChart3 size={20} />
            <span className="font-medium">Strategy & Data</span>
          </div>
          <div
            className={navItemClass(AppView.COMPLIANCE)}
            onClick={() => setView(AppView.COMPLIANCE)}
          >
            <FileCheck size={20} />
            <span className="font-medium">Compliance Tool</span>
          </div>
        </nav>

        <div className="mt-auto border-t border-slate-100 pt-4 px-2">
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <Settings size={16} />
            <span>Settings</span>
          </div>
          <p className="text-xs text-slate-300 mt-2">v0.5.0 • Phase 0.5 Build</p>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto relative">
        {children}
      </main>
    </div>
  );
};

export default Layout;