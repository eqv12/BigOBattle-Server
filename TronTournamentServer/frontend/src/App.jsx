import { Link, Navigate, Route, Routes } from "react-router-dom";
import { useRoom } from "./state";
import LandingPage from "./pages/LandingPage";
import GamesPage from "./pages/GamesPage";
import GameDetailPage from "./pages/GameDetailPage";
import CreateRoomPage from "./pages/CreateRoomPage";
import JoinRoomPage from "./pages/JoinRoomPage";
import WorkspacePage from "./pages/WorkspacePage";
import AboutPage from "./pages/AboutPage";
import { Terminal } from "lucide-react";

export default function App() {
  const { roomCode } = useRoom();

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col font-mono text-gray-200">
      <header className="sticky top-0 z-50 bg-gray-950/80 backdrop-blur-md border-b border-gray-800 px-6 py-4 flex justify-between items-center w-full">
        <Link className="flex items-center gap-2 font-bold text-xl text-green-400 tracking-tight" to="/">
          <Terminal size={24} />
          EMERGENT
        </Link>
        <nav className="flex gap-6 text-sm font-semibold">
          <Link className="hover:text-green-400 transition-colors" to="/games">Games</Link>
          <Link className="hover:text-green-400 transition-colors" to="/join">Join</Link>
          <Link className="hover:text-blue-400 transition-colors" to="/create">Create Room</Link>
          {roomCode && <Link className="text-yellow-400 hover:text-yellow-300 transition-colors" to="/workspace">Workspace</Link>}
        </nav>
      </header>

      <main className="flex-grow flex flex-col w-full">
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
