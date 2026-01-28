
import React, { useState } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  LineChart, Line
} from 'recharts';
import { AlertCircle, CheckCircle2, TrendingUp, Zap, Factory, Plus } from 'lucide-react';
import { ETSMetric, StrategicAdvice } from '../types';
import SetupWizard from './SetupWizard';

interface DashboardProps {
  data: {
    summary?: string;
    metrics?: ETSMetric[];
    advice?: StrategicAdvice[];
  } | null;
}

const Dashboard: React.FC<DashboardProps> = ({ data }) => {
  const [showWizard, setShowWizard] = useState(false);

  // Fallback data if user skips consultation or AI fails
  const metrics = data?.metrics || [
    { year: 2023, verifiedEmissions: 22000, freeAllocation: 24000, carbonPrice: 85 },
    { year: 2024, verifiedEmissions: 21800, freeAllocation: 22000, carbonPrice: 90 },
    { year: 2025, verifiedEmissions: 21500, freeAllocation: 18000, carbonPrice: 100 },
    { year: 2026, verifiedEmissions: 21000, freeAllocation: 14000, carbonPrice: 120 },
  ];

  const advice = data?.advice || [
    { title: "Kiln Electrification Study", description: "Feasibility study for replacing tunnel kiln gas burners with electric elements.", impact: "High", cost: "$$$", timeframe: "2-3 Years" },
    { title: "Waste Heat Recovery", description: "Install heat exchangers to preheat drying air using kiln exhaust.", impact: "Medium", cost: "$$", timeframe: "1 Year" },
  ];

  const summary = data?.summary || "Based on initial data, your installation faces a significant reduction in Free Allocation starting 2026 due to the new benchmarking rules for ceramic products. Immediate action is required to reduce specific emissions per ton of product.";

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 relative">
      
      {/* Wizard Modal */}
      {showWizard && (
        <SetupWizard 
            onComplete={() => setShowWizard(false)} 
            onCancel={() => setShowWizard(false)} 
        />
      )}

      {/* Header Section */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">Strategic Compliance Dashboard</h1>
          <p className="text-slate-500 mt-1">Real-time analysis of your EU ETS position and decarbonization roadmap.</p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => setShowWizard(true)}
            className="flex items-center gap-2 bg-emerald-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-emerald-700 shadow-sm transition-colors"
          >
            <Plus size={18} /> Setup New Installation
          </button>
          <div className="flex gap-2">
            <span className="bg-emerald-100 text-emerald-800 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide">
                ETS Phase 4
            </span>
          </div>
        </div>
      </div>

      {/* Summary Card */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 border-l-4 border-l-emerald-500">
        <h3 className="text-lg font-semibold text-slate-800 mb-2 flex items-center gap-2">
          <AlertCircle className="text-emerald-500 w-5 h-5" /> Executive Summary
        </h3>
        <p className="text-slate-600 leading-relaxed">{summary}</p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Chart 1: Allocation vs Emissions */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <h3 className="text-lg font-semibold text-slate-800 mb-6">Emissions vs. Free Allocation</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="year" axisLine={false} tickLine={false} />
                <YAxis axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                />
                <Legend iconType="circle" />
                <Bar dataKey="verifiedEmissions" name="Verified Emissions (tCO2)" fill="#ef4444" radius={[4, 4, 0, 0]} />
                <Bar dataKey="freeAllocation" name="Free Allocation (EUA)" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="text-xs text-slate-400 mt-4 text-center">
            Red bars exceeding green bars indicate a need to purchase allowances (EUA).
          </p>
        </div>

        {/* Chart 2: Financial Exposure */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <h3 className="text-lg font-semibold text-slate-800 mb-6">Estimated Carbon Cost Exposure</h3>
          <div className="h-72">
             <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="year" axisLine={false} tickLine={false} />
                <YAxis axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: '1px solid #e2e8f0' }}
                  formatter={(value: number) => [`€${value}`, 'Price']}
                />
                <Legend />
                <Line type="monotone" dataKey="carbonPrice" name="Carbon Price Forecast (€/t)" stroke="#6366f1" strokeWidth={3} dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
           <p className="text-xs text-slate-400 mt-4 text-center">
            Projected carbon price increases based on market volatility and cap tightening.
          </p>
        </div>
      </div>

      {/* Strategic Advice Section */}
      <div>
        <h2 className="text-2xl font-bold text-slate-800 mb-6 flex items-center gap-2">
          <Zap className="text-yellow-500 w-6 h-6" /> Decarbonization Roadmap
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {advice.map((item, idx) => (
            <div key={idx} className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2">
                  <Factory className="text-slate-400 w-5 h-5" />
                  <h4 className="font-semibold text-slate-800">{item.title}</h4>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-bold ${
                  item.impact === 'High' ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700'
                }`}>
                  {item.impact} Impact
                </span>
              </div>
              <p className="text-slate-600 text-sm mb-4 min-h-[40px]">{item.description}</p>
              <div className="flex items-center justify-between pt-4 border-t border-slate-100 text-xs text-slate-500 font-medium">
                <span className="flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" /> Cost: {item.cost}
                </span>
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Time: {item.timeframe}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
