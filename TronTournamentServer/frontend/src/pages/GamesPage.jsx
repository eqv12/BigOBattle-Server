import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getGames } from "../api";
import { motion } from "framer-motion";
import { Gamepad2, ChevronRight, AlertTriangle, Users, Code2, Loader2, LayoutGrid, Clock } from "lucide-react";

export default function GamesPage() {
  const [games, setGames] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getGames()
      .then((data) => {
        setGames(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // Animation variants
  const containerVars = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVars = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } }
  };

  return (
    <div className="min-h-full bg-gray-950 text-gray-200 p-6 md:p-12 w-full flex flex-col items-center">
      <div className="max-w-7xl w-full mt-4">
        <div className="mb-12 border-b border-gray-800 pb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 mb-4 rounded-full bg-blue-500/10 text-blue-400 text-sm font-semibold border border-blue-500/20">
            <Gamepad2 size={16} />
            <span>Select Your Arena</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-black tracking-tight text-white mb-4">
            Available Games
          </h1>
          <p className="text-gray-400 max-w-2xl text-lg">
            Choose a game to review the rules, see the I/O contract, and spin up a live coding room to challenge your friends.
          </p>
        </div>

        {loading && (
          <div className="flex flex-col items-center justify-center py-20 text-blue-400">
            <Loader2 className="w-12 h-12 animate-spin mb-4" />
            <p className="text-gray-400 font-mono animate-pulse">Loading arenas...</p>
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6 flex items-start gap-4 text-red-400 max-w-2xl">
            <AlertTriangle className="shrink-0 mt-1" />
            <div>
              <h3 className="font-bold mb-1">Failed to connect to the registry</h3>
              <p className="text-sm opacity-80">{error}</p>
            </div>
          </div>
        )}

        {!loading && !error && games.length === 0 && (
          <div className="text-center py-20 border border-gray-800 rounded-xl bg-gray-900/30 border-dashed">
            <Code2 size={48} className="mx-auto text-gray-600 mb-4" />
            <h3 className="text-xl font-bold text-gray-400 mb-2">No games found</h3>
            <p className="text-gray-500">The server hasn't registered any game plugins yet.</p>
          </div>
        )}

        {!loading && !error && games.length > 0 && (
          <motion.div 
            variants={containerVars}
            initial="hidden"
            animate="show"
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
          >
            {games.map((game) => (
              <GameCard key={game.key} game={game} itemVars={itemVars} />
            ))}
            {/* Built-in Coming Soon Card */}
            <motion.div 
              variants={itemVars}
              className="flex flex-col items-center justify-center bg-gray-900/30 border border-gray-800 border-dashed rounded-2xl p-8 text-center"
            >
              <div className="w-16 h-16 rounded-full bg-gray-800/50 flex items-center justify-center mb-4">
                <Clock className="w-8 h-8 text-gray-500" />
              </div>
              <h3 className="text-xl font-bold text-gray-400 mb-2">More Arenas Incoming</h3>
              <p className="text-sm text-gray-600 max-w-[200px]">
                New game modes and challenges are heavily under development.
              </p>
            </motion.div>
          </motion.div>
        )}
      </div>
    </div>
  );
}

function GameCard({ game, itemVars }) {
  const navigate = useNavigate();

  return (
    <motion.div 
      variants={itemVars}
      whileHover={{ y: -6 }}
      onClick={() => navigate(`/games/${game.key}`)}
      className="group relative flex flex-col bg-gray-900 border border-gray-800 rounded-2xl overflow-hidden cursor-pointer hover:border-blue-500/50 hover:shadow-[0_0_30px_rgba(59,130,246,0.15)] transition-all duration-300"
    >
      {/* Fallback pattern for thumbnail if none exists or it fails to load, otherwise show image with a cool gradient overlay */}
      <div className="h-48 w-full bg-gray-950 relative overflow-hidden flex-shrink-0">
        <div className="absolute inset-0 bg-gradient-to-tr from-gray-900 via-gray-900/40 to-transparent z-10 mix-blend-multiply" />
        <div className="absolute inset-0 bg-gradient-to-t from-gray-900 to-transparent z-10" />
        
        {game.thumbnail ? (
          <img 
            src={game.thumbnail} 
            alt={game.title} 
            className="w-full h-full object-cover opacity-80 group-hover:opacity-100 group-hover:scale-105 transition-all duration-700"
            onError={(e) => {
              // fallback if thumbnail URL is broken
              e.target.style.display = 'none';
              if (e.target.nextSibling) {
                e.target.nextSibling.style.display = 'flex';
              }
            }}
          />
        ) : null}
        
        {/* Placeholder if no thumbnail */}
        <div className={`absolute inset-0 w-full h-full flex items-center justify-center bg-gray-950 border-b border-gray-800 ${game.thumbnail ? 'hidden' : 'flex'}`}>
           <Gamepad2 className="w-16 h-16 text-gray-800 group-hover:text-blue-500/20 transition-colors" />
        </div>

        {/* Small badge top right */}
        <div className="absolute top-4 right-4 z-20 bg-gray-950/80 backdrop-blur text-xs font-bold text-gray-300 px-2 py-1 rounded border border-gray-700">
          Ready
        </div>
      </div>

      <div className="p-6 flex flex-col flex-grow relative z-20">
        <h3 className="text-2xl font-bold text-gray-100 mb-2 group-hover:text-blue-400 transition-colors">
          {game.title}
        </h3>
        <p className="text-gray-400 text-sm mb-6 flex-grow line-clamp-3 leading-relaxed">
          {game.summary || "No description provided for this game."}
        </p>

        <div className="flex items-center justify-between border-t border-gray-800/80 pt-4 mt-auto">
          {/* Tags */}
          <div className="flex flex-wrap items-center gap-2 text-xs text-gray-400 font-mono">
             <div className="flex items-center gap-1 bg-gray-800/80 px-2 py-1 rounded border border-gray-700">
               <Users size={12} className="text-blue-400" />
               <span>Two Player</span>
             </div>
             <div className="flex items-center gap-1 bg-gray-800/80 px-2 py-1 rounded border border-gray-700">
               <LayoutGrid size={12} className="text-green-400" />
               <span>Grid</span>
             </div>
          </div>
          <div className="flex items-center text-blue-400 text-sm font-bold group-hover:text-blue-300 whitespace-nowrap">
            Details
            <ChevronRight size={16} className="ml-1 group-hover:translate-x-1 transition-transform" />
          </div>
        </div>
      </div>
    </motion.div>
  );
}
