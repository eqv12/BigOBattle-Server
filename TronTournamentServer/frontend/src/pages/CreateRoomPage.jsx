import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { createRoom } from "../api";
import { useRoom } from "../state";

export default function CreateRoomPage() {
  const [searchParams] = useSearchParams();
  const preselectedGame = useMemo(() => searchParams.get("game") || "tron", [searchParams]);
  const [gameKey, setGameKey] = useState(preselectedGame);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const { updateRoomCode, updateGameKey } = useRoom();

  const onCreate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await createRoom(gameKey);
      setResult(data);
      updateRoomCode(data.room_code);
      updateGameKey(data.game_key);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section>
      <h1>Create Room</h1>
      <form className="stack" onSubmit={onCreate}>
        <label>Game
          <select value={gameKey} onChange={(e) => setGameKey(e.target.value)}>
            <option value="tron">Tron</option>
          </select>
        </label>
        <button className="btn" disabled={loading} type="submit">{loading ? "Creating..." : "Create Room"}</button>
      </form>
      {error && <p className="error">{error}</p>}
      {result && (
        <div className="panel">
          <p><strong>Room Code:</strong> {result.room_code}</p>
          <p><strong>Admin PIN:</strong> {result.admin_password}</p>
          <p><strong>Game:</strong> {result.game_key}</p>
        </div>
      )}
    </section>
  );
}
