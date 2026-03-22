import { Link, Navigate, Route, Routes } from "react-router-dom";
import { useRoom } from "./state";
import LandingPage from "./pages/LandingPage";
import GamesPage from "./pages/GamesPage";
import GameDetailPage from "./pages/GameDetailPage";
import CreateRoomPage from "./pages/CreateRoomPage";
import JoinRoomPage from "./pages/JoinRoomPage";
import WorkspacePage from "./pages/WorkspacePage";
import AboutPage from "./pages/AboutPage";

export default function App() {
  const { roomCode } = useRoom();

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="brand" to="/">Emergent</Link>
        <nav>
          <Link to="/games">Games</Link>
          <Link to="/join">Join Room</Link>
          <Link to="/create">Create Room</Link>
          <Link to="/about">About</Link>
          {roomCode && <Link to="/workspace">Workspace</Link>}
        </nav>
      </header>

      <main className="main-container">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/games" element={<GamesPage />} />
          <Route path="/games/:gameKey" element={<GameDetailPage />} />
          <Route path="/create" element={<CreateRoomPage />} />
          <Route path="/join" element={<JoinRoomPage />} />
          <Route path="/workspace" element={<WorkspacePage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
