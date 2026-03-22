import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getGames } from "../api";

export default function GamesPage() {
  const [games, setGames] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getGames().then(setGames).catch((err) => setError(err.message));
  }, []);

  return (
    <section>
      <h1>Games</h1>
      {error && <p className="error">{error}</p>}
      <div className="cards">
        {games.map((game) => (
          <article key={game.key} className="game-card">
            <img src={game.thumbnail} alt={game.title} />
            <div>
              <h3>{game.title}</h3>
              <p>{game.summary}</p>
              <Link className="btn" to={`/games/${game.key}`}>View Game</Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
