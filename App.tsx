import React, { useState } from 'react';
import Layout from './components/Layout';
import Consultation from './components/Consultation';
import Dashboard from './components/Dashboard';
import ComplianceManager from './components/ComplianceManager';
import RegulatoryLibrary from './components/RegulatoryLibrary';
import { AppView } from './types';
import { ArrowRight, Factory, ShieldCheck, TrendingUp } from 'lucide-react';

const Landing: React.FC<{ onStart: () => void }> = ({ onStart }) => (
  <div className="flex flex-col items-center justify-center h-full p-8 text-center max-w-3xl mx-auto">
    <div className="bg-emerald-100 p-4 rounded-full mb-8">
      <Factory className="w-12 h-12 text-emerald-600" />
    </div>
    <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-6 tracking-tight">
      Automating EU ETS Compliance for the <span className="text-emerald-600">Ceramic Industry</span>
    </h1>
    <p className="text-lg text-slate-600 mb-10 leading-relaxed max-w-2xl">
      Replace expensive consultants with an AI that understands kilns, drying processes, and the latest EU ETS & CBAM legislation. Get instant strategy, reporting guidance, and decarbonization pathways.
    </p>
    
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mb-12">
      <div className="p-4 bg-white border border-slate-200 rounded-xl text-left">
        <ShieldCheck className="w-8 h-8 text-blue-500 mb-3" />
        <h3 className="font-semibold text-slate-800">Compliance Check</h3>
        <p className="text-sm text-slate-500">Instant gap analysis against MRR & AVR regulations.</p>
      </div>
      <div className="p-4 bg-white border border-slate-200 rounded-xl text-left">
        <Factory className="w-8 h-8 text-orange-500 mb-3" />
        <h3 className="font-semibold text-slate-800">Process Optimization</h3>
        <p className="text-sm text-slate-500">Fuel switching & kiln technology advice.</p>
      </div>
      <div className="p-4 bg-white border border-slate-200 rounded-xl text-left">
        <TrendingUp className="w-8 h-8 text-emerald-500 mb-3" />
        <h3 className="font-semibold text-slate-800">Market Strategy</h3>
        <p className="text-sm text-slate-500">EUA purchasing strategies and carbon exposure forecasts.</p>
      </div>
    </div>

    <button 
      onClick={onStart}
      className="group bg-emerald-600 text-white text-lg font-semibold px-8 py-4 rounded-xl shadow-lg hover:bg-emerald-700 transition-all flex items-center gap-2"
    >
      Start Consultation
      <ArrowRight className="group-hover:translate-x-1 transition-transform" />
    </button>
  </div>
);

const App: React.FC = () => {
  const [view, setView] = useState<AppView>(AppView.LANDING);
  const [reportData, setReportData] = useState<any>(null);

  return (
    <Layout currentView={view} setView={setView}>
      {view === AppView.LANDING && (
        <Landing onStart={() => setView(AppView.CONSULTATION)} />
      )}
      {view === AppView.CONSULTATION && (
        <Consultation 
          onComplete={(data) => {
            setReportData(data);
          }} 
          setView={setView}
        />
      )}
      {view === AppView.DASHBOARD && (
        <Dashboard data={reportData} />
      )}
      {view === AppView.COMPLIANCE && (
        <ComplianceManager />
      )}
      {view === AppView.LIBRARY && (
        <RegulatoryLibrary />
      )}
    </Layout>
  );
};

export default App;