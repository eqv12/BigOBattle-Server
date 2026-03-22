import TronReplayViewer from "./TronReplayViewer";

export default function ReplayViewer({ gameKey, replay }) {
  if (!replay) {
    return <p>No replay selected.</p>;
  }

  const renderers = {
    tron: TronReplayViewer,
  };

  const Renderer = renderers[gameKey] || null;
  if (!Renderer) {
    return <pre>{JSON.stringify(replay, null, 2)}</pre>;
  }

  return <Renderer replay={replay} />;
}
