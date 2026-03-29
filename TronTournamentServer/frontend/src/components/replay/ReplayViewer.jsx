import TronReplayViewer from "./TronReplayViewer";

export default function ReplayViewer({ gameKey, replay, p0Name, p1Name }) {
  if (!replay) {
    return <div className="text-slate-400 italic">No replay selected.</div>;
  }

  const renderers = {
    tron: TronReplayViewer,
  };

  const Renderer = renderers[gameKey] || null;
  if (!Renderer) {
    return <pre className="text-slate-300">{JSON.stringify(replay, null, 2)}</pre>;
  }

  return <Renderer replay={replay} p0Name={p0Name} p1Name={p1Name} />;
}
