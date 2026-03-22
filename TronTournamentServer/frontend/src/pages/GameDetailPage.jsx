import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getGameDetails } from "../api";

export default function GameDetailPage() {
  const { gameKey } = useParams();
  const [game, setGame] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!gameKey) return;
    getGameDetails(gameKey).then(setGame).catch((err) => setError(err.message));
  }, [gameKey]);

  if (error) {
    return <p className="error">{error}</p>;
  }

  if (!game) {
    return <p>Loading game details...</p>;
  }

  return (
    <section>
      <h1>{game.title} Rules</h1>
      <p>{game.summary}</p>
      <ul>
        {(game.rules || []).map((rule, idx) => <li key={idx}>{rule}</li>)}
      </ul>
      <div className="actions">
        <Link className="btn" to={`/create?game=${encodeURIComponent(gameKey || "tron")}`}>Create Room For This Game</Link>
        <Link className="btn secondary" to="/join">Join Existing Room</Link>
      </div>
    </section>
  );
}
