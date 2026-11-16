import React, { useState, useEffect } from 'react';
import { Info, Calculator, Save, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useGuideSection } from './guide/GuideContext';

interface SchemaProperty {
  type: string;
  title: string;
  description?: string;
  unit?: string;
  minimum?: number;
  format?: string;
}

interface JsonSchema {
  type: string;
  title?: string;
  properties: Record<string, SchemaProperty>;
  required?: string[];
}

interface FormDefinition {
  source_stream_id: number;
  source_stream_name: string;
  json_schema: JsonSchema;
  ui_schema?: any;
}

interface DynamicEmissionFormProps {
  sourceStreamId: number;
  onSuccess: () => void;
}

// Mock API Call (In real app, this uses fetch)
const mockFetchFormDef = async (id: number): Promise<FormDefinition> => {
    // Return mock matching the seed data
    return {
        source_stream_id: id,
        source_stream_name: "Natural Gas Combustion Line 1",
        json_schema: {
            type: "object",
            title: "Natural Gas Consumption",
            properties: {
                activity_data: {
                    type: "number",
                    title: "Meter Reading (Consumo)",
                    description: "Total natural gas consumption for the period in Nm³.",
                    minimum: 0,
                    unit: "Nm³"
                }
            },
            required: ["activity_data"]
        }
    };
};

const mockSubmitEntry = async (data: any) => {
    // Simulate backend calculation delay
    await new Promise(r => setTimeout(r, 800));
    // Simulate return
    const activity = parseFloat(data.input_data.activity_data);
    const result = activity * 0.03854 * 56.1 * 0.001; 
    return {
        id: 123,
        calculated_tco2: result,
        calculation_trace: {
            value: result,
            unit: "tCO2",
            formula: "activity * ncv * ef * of * 0.001",
            factors_snapshot: { ncv: 0.03854, ef: 56.1 }
        }
    };
};

const DynamicEmissionForm: React.FC<DynamicEmissionFormProps> = ({ sourceStreamId, onSuccess }) => {
  const [definition, setDefinition] = useState<FormDefinition | null>(null);
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<any | null>(null);

  useGuideSection('formularioRegisto', {
    fluxoFonte: definition?.source_stream_name ?? null,
    campos: definition
      ? Object.entries(definition.json_schema.properties).map(([key, p]) => ({
          campo: p.title,
          unidade: p.unit,
          obrigatorio: definition.json_schema.required?.includes(key) ?? false,
          valorPreenchido: formData[key] ?? null,
        }))
      : [],
    aCalcular: submitting,
    resultado: result ? { tCO2: result.calculated_tco2, formula: result.calculation_trace.formula } : null,
  });

  useEffect(() => {
    const load = async () => {
        setLoading(true);
        // Swap with real API call later: fetch(`/api/v1/source-streams/${sourceStreamId}/form-definition`)
        const def = await mockFetchFormDef(sourceStreamId);
        setDefinition(def);
        setLoading(false);
    };
    load();
  }, [sourceStreamId]);

  const handleChange = (key: string, value: any) => {
    setFormData(prev => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
        const payload = {
            source_stream_id: sourceStreamId,
            period_start: "2025-01-01", // TODO: Make dynamic
            period_end: "2025-01-31",
            input_data: formData
        };
        const res = await mockSubmitEntry(payload);
        setResult(res);
        if(onSuccess) onSuccess();
    } catch (err) {
        console.error(err);
    } finally {
        setSubmitting(false);
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-400">Loading Form Configuration...</div>;
  if (!definition) return <div className="p-8 text-center text-red-500">Error loading form.</div>;

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      <div className="bg-emerald-50 border-b border-emerald-100 p-4">
         <h3 className="font-bold text-emerald-800 flex items-center gap-2">
            <Calculator size={20} />
            {definition.source_stream_name}
         </h3>
         <p className="text-xs text-emerald-600 mt-1">Configured Method: Standard Tier 2 (MRR Annex VI)</p>
      </div>

      <div className="p-6">
          {!result ? (
            <form onSubmit={handleSubmit} className="space-y-6">
                {(Object.entries(definition.json_schema.properties) as [string, SchemaProperty][]).map(([key, prop]) => (
                    <div key={key}>
                        <label className="block text-sm font-semibold text-slate-700 mb-1">
                            {prop.title} {definition.json_schema.required?.includes(key) && <span className="text-red-500">*</span>}
                        </label>
                        <div className="relative">
                            <input
                                type={prop.type === 'number' ? 'number' : 'text'}
                                className="w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                                placeholder={`Enter ${prop.title}`}
                                onChange={(e) => handleChange(key, e.target.value)}
                                required={definition.json_schema.required?.includes(key)}
                            />
                            {prop.unit && (
                                <span className="absolute right-4 top-3.5 text-slate-400 text-sm font-medium">
                                    {prop.unit}
                                </span>
                            )}
                        </div>
                        {prop.description && (
                            <p className="text-xs text-slate-500 mt-1.5 flex items-center gap-1">
                                <Info size={12} /> {prop.description}
                            </p>
                        )}
                    </div>
                ))}

                <button 
                    type="submit" 
                    disabled={submitting}
                    className="w-full bg-emerald-600 text-white py-3 rounded-xl font-semibold hover:bg-emerald-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-70"
                >
                    {submitting ? 'Calculating...' : 'Calculate & Submit Entry'}
                </button>
            </form>
          ) : (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="flex items-center gap-2 text-emerald-600 mb-4 font-bold">
                    <CheckCircle2 size={24} /> Calculation Verified
                </div>
                <div className="bg-slate-50 rounded-xl p-4 border border-slate-200 mb-4">
                    <div className="text-sm text-slate-500 mb-1">Total Emissions</div>
                    <div className="text-3xl font-bold text-slate-800">
                        {result.calculated_tco2.toFixed(4)} <span className="text-lg text-slate-400 font-normal">tCO2</span>
                    </div>
                </div>
                <div className="text-xs font-mono bg-slate-100 p-3 rounded-lg text-slate-600 mb-4 border border-slate-200">
                    <strong>Trace:</strong> {result.calculation_trace.formula}
                    <br/>
                    <strong>Factors:</strong> EF={result.calculation_trace.factors_snapshot.ef}, NCV={result.calculation_trace.factors_snapshot.ncv}
                </div>
                <button 
                    onClick={() => setResult(null)} 
                    className="w-full text-slate-500 hover:text-slate-700 text-sm font-medium"
                >
                    Submit Another Entry
                </button>
            </div>
          )}
      </div>
    </div>
  );
};

export default DynamicEmissionForm;