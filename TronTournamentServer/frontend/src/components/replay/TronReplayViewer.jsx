import { useEffect, useMemo, useState } from "react";

const CELL = 16;

function drawFrame(canvas, frame) {
  if (!canvas || !frame || !frame.board) return;
  const ctx = canvas.getContext("2d");
  const width = frame.board.width;
  const height = frame.board.height;

  canvas.width = width * CELL;
  canvas.height = height * CELL;

  ctx.fillStyle = "#0e1219";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.strokeStyle = "#1f2a38";
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

  ctx.fillStyle = "#3c8cf5";
  for (const part of p0.body || []) {
    ctx.fillRect(part.x * CELL + 1, part.y * CELL + 1, CELL - 2, CELL - 2);
  }

  ctx.fillStyle = "#f5953c";
  for (const part of p1.body || []) {
    ctx.fillRect(part.x * CELL + 1, part.y * CELL + 1, CELL - 2, CELL - 2);
  }
}

export default function TronReplayViewer({ replay }) {
  const frames = useMemo(() => replay?.frames || [], [replay]);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    setIndex(0);
    setPlaying(false);
  }, [replay]);

  useEffect(() => {
    if (!playing || frames.length === 0) return;
    const timer = setInterval(() => {
      setIndex((prev) => {
        if (prev >= frames.length - 1) {
          setPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 120);
    return () => clearInterval(timer);
  }, [playing, frames.length]);

  useEffect(() => {
    const canvas = document.getElementById("tron-replay-canvas");
    drawFrame(canvas, frames[index]);
  }, [frames, index]);

  if (!frames.length) {
    return <p>No replay data yet.</p>;
  }

  return (
    <div>
      <div className="replay-controls">
        <button onClick={() => setPlaying((v) => !v)}>{playing ? "Pause" : "Play"}</button>
        <button onClick={() => setIndex((v) => Math.max(0, v - 1))}>Prev</button>
        <button onClick={() => setIndex((v) => Math.min(frames.length - 1, v + 1))}>Next</button>
        <span>Turn {index} / {frames.length - 1}</span>
      </div>
      <input
        type="range"
        min="0"
        max={Math.max(0, frames.length - 1)}
        value={index}
        onChange={(e) => setIndex(Number(e.target.value))}
      />
      <canvas id="tron-replay-canvas" />
      <p>
        Result: {replay?.result?.winner || "draw"} | Termination: {replay?.result?.termination || "-"}
      </p>
    </div>
  );
}
