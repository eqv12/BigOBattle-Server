import { useEffect, useMemo, useState, useRef } from "react";
import { Play, Pause, FastForward, SkipBack, SkipForward, RotateCcw } from "lucide-react";

export default function TronReplayViewer({ replay, p0Name, p1Name }) {
  const frames = useMemo(() => replay?.frames || [], [replay]);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speedMult, setSpeedMult] = useState(1);
  const canvasRef = useRef(null);

  useEffect(() => {
    setIndex(0);
    setPlaying(false);
  }, [replay]);

  const drawFrame = (canvas, frame) => {
    if (!canvas || !frame || !frame.board) return;
    const ctx = canvas.getContext("2d");
    const width = frame.board.width;
    const height = frame.board.height;

    const parent = canvas.parentElement;
    const minDim = Math.min(parent.clientWidth - 32, 600);
    const CELL = Math.floor(minDim / Math.max(width, height));

    canvas.width = width * CELL;
    canvas.height = height * CELL;

    ctx.fillStyle = "#0f172a"; // slate-950
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = "#1e293b"; // slate-800
    ctx.lineWidth = 1;
    for (let x = 0; x <= width; x++) {
      ctx.beginPath();
      ctx.moveTo(x * CELL, 0);
      ctx.lineTo(x * CELL, canvas.height);
      ctx.stroke();
    }
    for (let y = 0; y <= height; y++) {
      ctx.beginPath();
      ctx.moveTo(0, y * CELL);
      ctx.lineTo(canvas.width, y * CELL);
      ctx.stroke();
    }

    const p0 = frame.p0 || { body: [] };
    const p1 = frame.p1 || { body: [] };

    ctx.fillStyle = "#34d399"; // emerald-400
    for (const part of p0.body || []) {
      ctx.fillRect(part.x * CELL + 1, part.y * CELL + 1, CELL - 2, CELL - 2);
    }
    // Head P0
    if (p0.body && p0.body.length > 0) {
      ctx.fillStyle = "#10b981"; // emerald-500
      ctx.fillRect(p0.body[0].x * CELL + 1, p0.body[0].y * CELL + 1, CELL - 2, CELL - 2);
    }

    ctx.fillStyle = "#f43f5e"; // rose-500
    for (const part of p1.body || []) {
      ctx.fillRect(part.x * CELL + 1, part.y * CELL + 1, CELL - 2, CELL - 2);
    }
    // Head P1
    if (p1.body && p1.body.length > 0) {
      ctx.fillStyle = "#e11d48"; // rose-600
      ctx.fillRect(p1.body[0].x * CELL + 1, p1.body[0].y * CELL + 1, CELL - 2, CELL - 2);
    }
  };

  useEffect(() => {
    if (!playing || frames.length === 0) return;
    const isFinished = index >= frames.length - 1;
    if (isFinished) {
      setPlaying(false);
      return;
    }
    const timer = setInterval(() => {
      setIndex((prev) => Math.min(frames.length - 1, prev + 1));
    }, 150 / speedMult);
    return () => clearInterval(timer);
  }, [playing, frames.length, index, speedMult]);

  useEffect(() => {
    drawFrame(canvasRef.current, frames[index]);
  }, [frames, index]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => drawFrame(canvasRef.current, frames[index]);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [frames, index]);

  if (!frames.length) {
    return <div className="text-slate-400 italic">No replay data yet.</div>;
  }

  const isFinished = index >= frames.length - 1;

  const togglePlay = () => {
    if (isFinished) {
      setIndex(0);
      setPlaying(true);
    } else {
      setPlaying((v) => !v);
    }
  };

  const cycleSpeed = () => {
    setSpeedMult(s => s === 1 ? 2 : s === 2 ? 4 : 1);
  };

  return (
    <div className="flex flex-col h-full w-full bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
      <div className="bg-slate-950 px-4 py-3 border-b border-slate-800 flex justify-between items-center">
        <h3 className="font-bold text-slate-300 text-sm flex items-center gap-2">
          Match Visualizer
        </h3>
        <div className="flex gap-4 text-xs font-mono text-slate-400">
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-emerald-400 inline-block shadow-[0_0_8px_rgba(52,211,153,0.4)]"></span> {p0Name || "P0 (Emerald)"}</span>
          <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-rose-500 inline-block shadow-[0_0_8px_rgba(244,63,94,0.4)]"></span> {p1Name || "P1 (Rose)"}</span>
        </div>
      </div>
      
      <div className="flex-grow flex items-center justify-center p-4 bg-[#0a0f18] relative min-h-0 overflow-hidden">
        <canvas ref={canvasRef} className="shadow-2xl rounded-sm border border-slate-800/50 max-w-full max-h-full object-contain" />
      </div>

      <div className="p-4 bg-slate-950 border-t border-slate-800 flex flex-col gap-4 relative z-10">
        <div className="flex items-center gap-4">
          <span className="text-xs font-mono text-slate-500 w-12 text-right">{index}</span>
          <input
            type="range"
            min="0"
            max={Math.max(0, frames.length - 1)}
            value={index}
            onChange={(e) => {
              setIndex(Number(e.target.value));
              setPlaying(false);
            }}
            className="flex-grow h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-500"
          />
          <span className="text-xs font-mono text-slate-500 w-12">{frames.length - 1}</span>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 bg-slate-900 rounded-lg p-1 border border-slate-800">
            <button title="Previous Move" onClick={() => { setIndex((v) => Math.max(0, v - 1)); setPlaying(false); }} className="p-2 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded transition-colors">
              <SkipBack className="w-4 h-4" />
            </button>
            <button 
              title={isFinished ? "Replay" : playing ? "Pause" : "Play"} 
              onClick={togglePlay} 
              className="p-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 rounded transition-colors"
            >
              {isFinished ? <RotateCcw className="w-4 h-4" /> : playing ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </button>
            <button title="Next Move" onClick={() => { setIndex((v) => Math.min(frames.length - 1, v + 1)); setPlaying(false); }} className="p-2 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded transition-colors">
              <SkipForward className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center gap-4 text-sm font-mono text-slate-400">
            <span>Result: <span className="text-emerald-400">{replay?.result?.winner || "draw"}</span></span>
            <span className="text-slate-600">|</span>
            <span>Reason: {replay?.result?.termination || "-"}</span>
          </div>

          <button onClick={cycleSpeed} className="px-3 py-1.5 bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 rounded font-mono text-xs transition-colors flex items-center gap-1">
            <FastForward className="w-3 h-3" /> {speedMult}x
          </button>
        </div>
      </div>
    </div>
  );
}
