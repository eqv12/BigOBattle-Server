import { Link } from "react-router-dom";

export default function LandingPage() {
  return (
    <section>
      <h1>Build autonomous bots. Battle in live rooms.</h1>
      <p>Create a room for a game, or join an existing room and start coding in the integrated editor.</p>
      <div className="actions">
        <Link className="btn" to="/create">Create Room</Link>
        <Link className="btn secondary" to="/join">Join Room</Link>
      </div>
    </section>
  );
}
