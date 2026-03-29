import React, { useState } from "react";
import { ChevronDown, ChevronRight, AlertTriangle } from "lucide-react";

export default function TurnLogsAccordion({ rawOutput }) {
  const [expandedTurn, setExpandedTurn] = useState(null);

  if (!rawOutput || (!rawOutput.turn_events && !rawOutput.bot_raw_outputs)) {
    return <div className="text-slate-500 text-sm p-4 text-center">No move telemetry available. Run a test match first.</div>;
  }

  const turn_events = rawOutput.turn_events || [];
  const bot_raw_outputs = rawOutput.bot_raw_outputs || {};

  return (
    <div className="flex flex-col gap-2 w-full">
      {turn_events.map((event) => {
        const isExpanded = expandedTurn === event.turn;
        return (
          <div key={event.turn} className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
            <button 
              onClick={() => setExpandedTurn(isExpanded ? null : event.turn)}
              className="w-full flex items-center justify-between p-3 bg-slate-900 hover:bg-slate-800/80 transition-colors text-left"
            >
              <div className="flex items-center gap-4">
                {isExpanded ? <ChevronDown className="w-4 h-4 text-emerald-400" /> : <ChevronRight className="w-4 h-4 text-slate-500" />}
                <span className="font-mono text-sm text-slate-300 font-bold bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                  TURN {event.turn}
                </span>
                
                <div className="flex gap-4 text-xs font-mono">
                  <span className="text-indigo-400">P0: <span className="text-slate-300">{event.p0_move || "none"}</span></span>
                  <span className="text-orange-400">P1: <span className="text-slate-300">{event.p1_move || "none"}</span></span>
                </div>
              </div>
              
              {(event.p0_error || event.p1_error) && (
                <AlertTriangle className="w-4 h-4 text-red-500" />
              )}
            </button>

            {isExpanded && (
              <div className="p-4 bg-slate-950 border-t border-slate-800 grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-2">
                  <h4 className="text-xs font-bold text-indigo-400 border-b border-slate-800 pb-1">Player 0 Console</h4>
                  <div className="text-xs font-mono text-slate-400 whitespace-pre-wrap">
                    <span className="text-slate-600 block mb-1">// stdout</span>
                    {event.p0_stdout || <span className="text-slate-600 italic">no output</span>}
                  </div>
                  {event.p0_error && (
                    <div className="text-xs font-mono text-red-400 whitespace-pre-wrap mt-2 p-2 bg-red-500/10 rounded border border-red-500/20">
                      {event.p0_error}
                    </div>
                  )}
                </div>

                <div className="flex flex-col gap-2 border-l border-slate-800 pl-4">
                  <h4 className="text-xs font-bold text-orange-400 border-b border-slate-800 pb-1">Player 1 Console</h4>
                  <div className="text-xs font-mono text-slate-400 whitespace-pre-wrap">
                    <span className="text-slate-600 block mb-1">// stdout</span>
                    {event.p1_stdout || <span className="text-slate-600 italic">no output</span>}
                  </div>
                  {event.p1_error && (
                    <div className="text-xs font-mono text-red-400 whitespace-pre-wrap mt-2 p-2 bg-red-500/10 rounded border border-red-500/20">
                      {event.p1_error}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
      
      {Object.keys(bot_raw_outputs).length > 0 && (
         <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden mt-4">
            <div className="px-4 py-2 bg-slate-950 border-b border-slate-800 flex justify-between items-center">
              <span className="text-xs font-mono text-slate-400">Global stderr</span>
            </div>
            <div className="p-4 grid grid-cols-2 gap-4">
                <div className="text-xs font-mono text-slate-400 overflow-y-auto max-h-40 whitespace-pre-wrap">
                  <span className="text-indigo-400 block mb-1 border-b border-slate-800 pb-1">p0.stderr</span>
                  {bot_raw_outputs.p0?.stderr?.join("\n") || "No errors"}
                </div>
                <div className="text-xs font-mono text-slate-400 overflow-y-auto max-h-40 whitespace-pre-wrap border-l border-slate-800 pl-4">
                  <span className="text-orange-400 block mb-1 border-b border-slate-800 pb-1">p1.stderr</span>
                  {bot_raw_outputs.p1?.stderr?.join("\n") || "No errors"}
                </div>
            </div>
         </div>
      )}
    </div>
  );
}
