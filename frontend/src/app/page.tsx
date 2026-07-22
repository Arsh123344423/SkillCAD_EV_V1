'use client';

import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Network, 
  Cpu, 
  CheckCircle2, 
  ShieldAlert, 
  Zap, 
  Send, 
  Database,
  TrendingUp
} from 'lucide-react';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ;

export default function Dashboard() {
  const [activeTrack, setActiveTrack] = useState<'trackA' | 'trackB'>('trackA');

  // Track A State
  const [evModel, setEvModel] = useState('Model C');
  const [batteryType, setBatteryType] = useState('Li-ion');
  const [currentCycle, setCurrentCycle] = useState('450');
  const [cyclesPerDay, setCyclesPerDay] = useState('1.5');
  const [apmLoading, setApmLoading] = useState(false);
  const [apmReport, setApmReport] = useState<any>(null);

  // Track B State
  const [graphData, setGraphData] = useState<{ nodes: any[]; edges: any[] }>({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState<string>('India_ACC_Gigafactories');
  const [nodeRiskDetails, setNodeRiskDetails] = useState<any>(null);
  const [nodeLoading, setNodeLoading] = useState(false);
  
  const [scQuery, setScQuery] = useState('Assess the supply chain risks for India_ACC_Gigafactories and recommend strategic solutions.');
  const [scAgentLoading, setScAgentLoading] = useState(false);
  const [scAgentResponse, setScAgentResponse] = useState<string>('');

  useEffect(() => {
    fetchGraphNodes();
  }, []);

  const fetchGraphNodes = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/supply-chain/nodes`);
      if (res.ok) {
        const data = await res.json();
        setGraphData(data);
      }
    } catch (err) {
      console.error('Failed to fetch supply chain nodes:', err);
    }
  };

  const handleApmSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApmLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/analyze/db`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ev_model: evModel,
          battery_type: batteryType,
          current_cycle: parseFloat(currentCycle),
          cycles_per_day: parseFloat(cyclesPerDay)
        })
      });
      const data = await res.json();
      setApmReport(data);
    } catch (err) {
      console.error('APM Analysis Error:', err);
    } finally {
      setApmLoading(false);
    }
  };

  const inspectNodeRisk = async (nodeId: string) => {
    setSelectedNode(nodeId);
    setNodeLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/supply-chain/analyze-node`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ supplier_id: nodeId })
      });
      const data = await res.json();
      setNodeRiskDetails(data);
    } catch (err) {
      console.error('Node inspection error:', err);
    } finally {
      setNodeLoading(false);
    }
  };

  const handleScAgentQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scQuery.trim()) return;
    setScAgentLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/supply-chain/agent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: scQuery })
      });
      const data = await res.json();
      setScAgentResponse(data.analysis || data.response || JSON.stringify(data));
    } catch (err) {
      console.error('Supply Chain Agent Error:', err);
    } finally {
      setScAgentLoading(false);
    }
  };

  // Helper functions to safely extract data from varying API responses (fixes the hardcoded bug)
  const getSoh = (report: any) => report?.current_soh_pct;
  const getRul = (report: any) => report?.remaining_useful_life;
  const getNarrative = (report: any) => report?.confidence;

  return (
    <div className="min-h-screen bg-[#000000] text-gray-200 flex flex-col font-sans selection:bg-[#1e847f] selection:text-white">
      {/* HEADER NAVBAR */}
      <header className="border-b border-[#1e847f]/30 bg-[#000000] sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg text-[#1e847f]">
            <img
              src="/SkillCAD logo.png"
              alt="Logo"
              className="w-15 h-15 object-contain"
            />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-[#eec19c]">SkillCAD EV Command Center</h1>
            <p className="text-xs text-gray-400">Multi-Agent Intelligence Platform</p>
          </div>
        </div>

        {/* TRACK TOGGLE TABS */}
        <div className="flex bg-[#0a0a0a] p-1 rounded-xl border border-[#1e847f]/20">
          <button
            onClick={() => setActiveTrack('trackA')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTrack === 'trackA'
                ? 'bg-[#1e847f] text-white shadow-lg shadow-[#1e847f]/20'
                : 'text-gray-400 hover:text-[#eec19c]'
            }`}
          >
            <Activity className="w-4 h-4" />
            Track A: Telemetry & APM
          </button>
          <button
            onClick={() => setActiveTrack('trackB')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTrack === 'trackB'
                ? 'bg-[#1e847f] text-white shadow-lg shadow-[#1e847f]/20'
                : 'text-gray-400 hover:text-[#eec19c]'
            }`}
          >
            <Network className="w-4 h-4" />
            Track B: Supply Chain Risk
          </button>
        </div>
      </header>

      {/* MAIN CONTENT AREA */}
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
        {/* ========================================================= */}
        {/* TRACK A: APM & TELEMETRY */}
        {/* ========================================================= */}
        {activeTrack === 'trackA' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Input Form Controls */}
            <div className="bg-[#0a0a0a] border border-[#1e847f]/30 rounded-2xl p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 text-[#eec19c] mb-4">
                  <Database className="w-5 h-5 text-[#1e847f]" />
                  <h2 className="font-semibold text-lg">Battery Telemetry Query</h2>
                </div>
                <p className="text-xs text-gray-400 mb-6">
                  Select EV Model parameters to run SOH degradation models and remaining useful life (RUL) predictions.
                </p>

                <form onSubmit={handleApmSubmit} className="space-y-4">
                  <div>
                    <label className="block text-xs font-medium text-[#eec19c] mb-1">EV Model</label>
                    <input
                      type="text"
                      value={evModel}
                      onChange={(e) => setEvModel(e.target.value)}
                      className="w-full bg-[#000000] border border-[#1e847f]/40 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#eec19c]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-[#eec19c] mb-1">Battery Chemistry</label>
                    <select
                      value={batteryType}
                      onChange={(e) => setBatteryType(e.target.value)}
                      className="w-full bg-[#000000] border border-[#1e847f]/40 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#eec19c]"
                    >
                      <option value="Li-ion">Li-ion (NMC)</option>
                      <option value="LFP">Lithium Iron Phosphate (LFP)</option>
                    </select>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-[#eec19c] mb-1">Current Cycle</label>
                      <input
                        type="number"
                        value={currentCycle}
                        onChange={(e) => setCurrentCycle(e.target.value)}
                        className="w-full bg-[#000000] border border-[#1e847f]/40 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#eec19c]"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-[#eec19c] mb-1">Cycles/Day</label>
                      <input
                        type="number"
                        step="0.1"
                        value={cyclesPerDay}
                        onChange={(e) => setCyclesPerDay(e.target.value)}
                        className="w-full bg-[#000000] border border-[#1e847f]/40 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#eec19c]"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={apmLoading}
                    className="w-full mt-4 bg-[#1e847f] hover:bg-[#1e847f]/80 text-white font-medium py-2.5 rounded-lg text-sm transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {apmLoading ? 'Running Predictive Model...' : 'Analyze Health & RUL'}
                    <TrendingUp className="w-4 h-4" />
                  </button>
                </form>
              </div>

              <div className="mt-6 pt-4 border-t border-[#1e847f]/20 text-xs text-[#1e847f]">
                Backend Status: Connected to MongoDB Telemetry
              </div>
            </div>

            {/* Results Display */}
            <div className="lg:col-span-2 bg-[#0a0a0a] border border-[#1e847f]/30 rounded-2xl p-6 flex flex-col">
              <h2 className="font-semibold text-lg text-[#eec19c] mb-4 flex items-center gap-2">
                <Cpu className="w-5 h-5 text-[#1e847f]" />
                Diagnostic & Predictive Report
              </h2>

              {apmReport ? (
                <div className="space-y-6 flex-1 overflow-y-auto pr-2">
                  {/* Summary Metric Cards */}
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-[#000000] border border-[#1e847f]/40 p-4 rounded-xl">
                      <p className="text-xs text-gray-400">State of Health (SOH)</p>
                      <p className="text-2xl font-bold text-[#eec19c] mt-1">
                        {getSoh(apmReport)}
                      </p>
                    </div>
                    <div className="bg-[#000000] border border-[#1e847f]/40 p-4 rounded-xl">
                      <p className="text-xs text-gray-400">RUL (Remaining Cycles)</p>
                      <p className="text-2xl font-bold text-[#1e847f] mt-1">
                        {getRul(apmReport)}
                      </p>
                    </div>
                    <div className="bg-[#000000] border border-[#1e847f]/40 p-4 rounded-xl">
                      <p className="text-xs text-gray-400">Health Status</p>
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-[#1e847f]/10 text-[#1e847f] border border-[#1e847f]/30 mt-2">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Analyzed
                      </span>
                    </div>
                  </div>

                  {/* Narrative Body */}
                  <div className="bg-[#000000] border border-[#1e847f]/30 p-5 rounded-xl text-sm leading-relaxed text-gray-300">
                    <h3 className="font-semibold text-[#eec19c] mb-2 text-xs uppercase tracking-wider">
                      AI Diagnostic Summary
                    </h3>
                    <p className="whitespace-pre-wrap font-mono text-[13px]">
                      {getNarrative(apmReport)}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-[#1e847f]/20 rounded-xl p-8 text-center text-gray-500">
                  <Activity className="w-12 h-12 mb-3 text-[#1e847f] animate-pulse" />
                  <p className="text-sm">Click "Analyze Health & RUL" to fetch real-time telemetry analytics.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ========================================================= */}
        {/* TRACK B: SUPPLY CHAIN RISK INTELLIGENCE */}
        {/* ========================================================= */}
        {activeTrack === 'trackB' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Graph Node Inspector Sidebar */}
            <div className="lg:col-span-4 space-y-6">
              <div className="bg-[#0a0a0a] border border-[#1e847f]/30 rounded-2xl p-5">
                <h2 className="font-semibold text-[#eec19c] text-sm mb-3 flex items-center justify-between">
                  <span>Supply Chain Graph Nodes</span>
                  <span className="text-xs bg-[#000000] px-2 py-0.5 rounded border border-[#1e847f]/50 text-[#1e847f]">
                    {graphData.nodes.length} Nodes
                  </span>
                </h2>
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1 custom-scrollbar">
                  {graphData.nodes.map((node) => (
                    <button
                      key={node.id}
                      onClick={() => inspectNodeRisk(node.id)}
                      className={`w-full text-left p-2.5 rounded-lg border text-xs flex items-center justify-between transition-all ${
                        selectedNode === node.id
                          ? 'bg-[#1e847f]/20 border-[#1e847f] text-white'
                          : 'bg-[#000000] border-[#1e847f]/20 text-gray-400 hover:border-[#1e847f]/60 hover:text-[#eec19c]'
                      }`}
                    >
                      <span className="font-medium truncate pr-2">{node.id}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-[#0a0a0a] border border-gray-800 text-gray-300">
                        Tier {node.tier}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Node Calculated Risk Box */}
              <div className="bg-[#0a0a0a] border border-[#1e847f]/30 rounded-2xl p-5">
                <h3 className="font-semibold text-[#eec19c] text-sm mb-3 flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-[#1e847f]" />
                  Calculated Node Risk Profile
                </h3>

                {nodeLoading ? (
                  <p className="text-xs text-[#1e847f] py-4 text-center animate-pulse">Calculating graph propagation...</p>
                ) : nodeRiskDetails ? (
                  <div className="space-y-4 text-xs height-full">
                    <div className="flex justify-between items-center p-3 bg-[#000000] rounded-lg border border-[#1e847f]/30">
                      <div>
                        <p className="text-gray-400">Local Risk</p>
                        <p className="text-lg font-bold text-white">{nodeRiskDetails.local_risk} <span className="text-[10px] font-normal text-gray-500">/ 100</span></p>
                      </div>
                      <div className="text-right">
                        <p className="text-gray-400">Propagated Risk</p>
                        <p className={`text-lg font-bold ${nodeRiskDetails.total_risk > 40 ? 'text-[#eec19c]' : 'text-[#1e847f]'}`}>
                          {nodeRiskDetails.total_risk} <span className="text-[10px] font-normal text-gray-500">/ 100</span>
                        </p>
                      </div>
                    </div>

                    <div>
                      <p className="font-semibold text-[#1e847f] mb-2">Upstream Bottlenecks</p>
                      {nodeRiskDetails.upstream_dependencies?.length > 0 ? (
                        <div className="space-y-1.5">
                          {nodeRiskDetails.upstream_dependencies.map((dep: any, i: number) => (
                            <div key={i} className="flex justify-between p-2 bg-[#000000] rounded border border-[#1e847f]/20">
                              <span className="text-gray-300 truncate pr-2">{dep.upstream_node}</span>
                              <span className="text-[#eec19c] font-medium shrink-0">{dep.concentration_percentage} share</span>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-gray-500 italic p-2">No upstream predecessors (Raw Material Source)</p>
                      )}
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-gray-500 p-2">Select a node above to run propagation math.</p>
                )}
              </div>
            </div>

            {/* Gemini Supply Chain Agent Chat */}
            <div className="lg:col-span-8 bg-[#0a0a0a] width-full-fixed border border-[#1e847f]/30 rounded-2xl p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-2 text-[#eec19c] mb-2">
                  <Network className="w-5 h-5 text-[#1e847f]" />
                  <h2 className="font-semibold text-lg">India Supply Chain Strategy Agent</h2>
                </div>

                <div className="bg-[#000000] border border-[#1e847f]/30 rounded-xl p-5 min-h-[300px] max-h-[420px] overflow-y-auto mb-6 custom-scrollbar">
                  {scAgentLoading ? (
                    <div className="flex flex-col items-center justify-center h-48 text-[#1e847f]">
                      <div className="w-8 h-8 border-2 border-[#eec19c] border-t-transparent rounded-full animate-spin mb-3"></div>
                      <p className="text-xs">Traversing supply chain graph...</p>
                    </div>
                  ) : scAgentResponse ? (
                    <div className="prose prose-invert prose-xs max-w-none text-gray-200 leading-relaxed whitespace-pre-wrap">
                      {scAgentResponse}
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-48 text-gray-600 text-center px-6">
                      <ShieldAlert className="w-10 h-10 mb-2 text-[#1e847f]" />
                      <p className="text-xs">Ask a question below to analyze India's battery dependencies.</p>
                    </div>
                  )}
                </div>
              </div>

              <form onSubmit={handleScAgentQuery} className="flex gap-3">
                <input
                  type="text"
                  value={scQuery}
                  onChange={(e) => setScQuery(e.target.value)}
                  placeholder="Ask the Supply Chain Agent..."
                  className="flex-1 bg-[#000000] border border-[#1e847f]/40 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-[#eec19c] placeholder-gray-600"
                />
                <button
                  type="submit"
                  disabled={scAgentLoading}
                  className="bg-[#1e847f] hover:bg-[#1e847f]/80 text-white font-medium px-6 py-3 rounded-xl text-sm transition-all flex items-center gap-2 disabled:opacity-50"
                >
                  <span>Query</span>
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </div>
          </div>
        )}
      </main>
      
      {/* Optional scrollbar styling for webkit */}
      <style dangerouslySetInnerHTML={{__html: `
        .custom-scrollbar::-webkit-scrollbar { width: 6px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: #000000; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #1e847f; border-radius: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #eec19c; }
      `}} />
    </div>
  );
}