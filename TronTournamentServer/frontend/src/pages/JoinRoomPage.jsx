import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { joinRoom } from "../api";
import { useRoom } from "../state";

export default function JoinRoomPage() {
  const [roomCodeInput, setRoomCodeInput] = useState("");
  const [nameInput, setNameInput] = useState("");
  const [error, setError] = useState("");
  const [joined, setJoined] = useState(null);
  const { updateRoomCode, updateGameKey, updateDisplayName } = useRoom();
  const navigate = useNavigate();

  const onJoin = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const data = await joinRoom(roomCodeInput, nameInput);
      setJoined(data);
      updateRoomCode(data.room_code);
      updateGameKey(data.game_key);
      updateDisplayName(data.display_name);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <section>
      <h1>Join Room</h1>
      <form className="stack" onSubmit={onJoin}>
        <label>Room Code
          <input value={roomCodeInput} onChange={(e) => setRoomCodeInput(e.target.value.toUpperCase())} required />
        </label>
        <label>Display Name
          <input value={nameInput} onChange={(e) => setNameInput(e.target.value)} required />
        </label>
        <button className="btn" type="submit">Join</button>
      </form>
      {error && <p className="error">{error}</p>}
      {joined && (
        <div className="panel">
          <h3>Room Ready</h3>
          <p>Game: {joined.game_key.toUpperCase()}</p>
          <p>Read rules from the game page, then start coding.</p>
          <button className="btn" onClick={() => navigate("/workspace")}>Start</button>
        </div>
      )}
    </section>
  );
}
