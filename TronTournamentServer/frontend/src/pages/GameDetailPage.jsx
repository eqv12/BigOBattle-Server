import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getGameDetails } from "../api";
import { Gamepad2, ChevronRight, AlertTriangle, Play, BookOpen, Terminal, CheckCircle2, Code2, Loader2, Info, Zap } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function GameDetailPage() {
  const { gameKey } = useParams();
  const [game, setGame] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("rules");

  useEffect(() => {
    if (!gameKey) return;
    setLoading(true);
    getGameDetails(gameKey)
      .then((data) => {
        setGame(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [gameKey]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-blue-400 w-full">
        <Loader2 className="w-12 h-12 animate-spin mb-4" />
        <p className="text-gray-400 font-mono animate-pulse">Loading arena protocols...</p>
      </div>
    );
  }

  if (error || !game) {
    return (
      <div className="flex justify-center items-center min-h-[60vh] w-full">
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-8 flex flex-col items-center text-center gap-4 text-red-400 max-w-md">
          <AlertTriangle className="w-12 h-12" />
          <div>
            <h3 className="text-xl font-bold mb-2">Access Denied</h3>
            <p className="text-sm opacity-80">{error || "Game not found in the registry."}</p>
          </div>
          <Link to="/games" className="mt-4 text-gray-300 hover:text-white underline text-sm">
            Return to Arena Selection
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col w-full bg-gray-950 text-gray-200">
      {/* Hero Header Area */}
      <div className="relative h-[250px] md:h-[350px] w-full overflow-hidden border-b border-gray-800 flex items-end">
        <div className="absolute inset-0 bg-gray-900">
          {game.thumbnail && (
            <img 
              src={game.thumbnail} 
              alt={game.title} 
              className="w-full h-full object-cover opacity-40 mix-blend-screen"
            />
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-gray-950 via-gray-950/80 to-transparent" />
        </div>
        
        <div className="relative z-10 w-full max-w-6xl mx-auto px-6 md:px-12 pb-8">
          <div className="flex items-center gap-3 text-sm text-gray-400 mb-4 font-mono">
            <Link to="/games" className="hover:text-blue-400 transition-colors">Games</Link>
            <ChevronRight size={14} />
            <span className="text-blue-400">{game.title}</span>
          </div>
          <h1 className="text-5xl md:text-7xl font-black text-white capitalize tracking-tight drop-shadow-lg">
            {game.title}
          </h1>
          <p className="text-xl text-gray-400 mt-2 max-w-2xl font-medium">
            {game.summary}
          </p>
        </div>
      </div>

      {/* Main Content Layout with Sticky Sidebar */}
      <div className="relative w-full max-w-6xl mx-auto px-6 md:px-12 py-12 flex flex-col lg:flex-row gap-12">
        
        {/* Left Column: Tabs & Content */}
        <div className="flex-1 min-w-0">
          {/* Custom Tabs */}
          <div className="flex gap-6 border-b border-gray-800 mb-8 overflow-x-auto no-scrollbar">
            <TabButton 
              active={activeTab === "rules"} 
              onClick={() => setActiveTab("rules")} 
              icon={<BookOpen size={18} />} 
              label="Rules & Mechanics" 
            />
            <TabButton 
              active={activeTab === "io"} 
              onClick={() => setActiveTab("io")} 
              icon={<Terminal size={18} />} 
              label="I/O Contract" 
            />
            <TabButton 
              active={activeTab === "tech"} 
              onClick={() => setActiveTab("tech")} 
              icon={<Code2 size={18} />} 
              label="Tech Specs" 
            />
          </div>

          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {activeTab === "rules" && (
                <div className="space-y-6">
                  {game.description && (
                    <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-8">
                      <h3 className="text-2xl font-bold mb-4 flex items-center gap-3">
                        <Gamepad2 className="text-blue-400" /> Overview
                      </h3>
                      <p className="text-gray-300 leading-relaxed text-lg">
                        {game.description}
                      </p>
                    </div>
                  )}

                  <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-8">
                    <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
                      <CheckCircle2 className="text-green-500" /> Key Mechanics & Rules
                    </h3>
                    <ul className="space-y-4">
                      {(game.rules || []).map((rule, idx) => (
                        <li key={idx} className="flex gap-4 items-start text-gray-300 leading-relaxed">
                          <CheckCircle2 className="w-6 h-6 text-green-500 shrink-0 mt-0.5 opacity-60" />
                          <span className="text-lg">{rule}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div className="bg-blue-500/10 border border-blue-500/20 rounded-2xl p-6 flex gap-4">
                     <Info className="text-blue-400 shrink-0" />
                     <p className="text-sm text-blue-200/80">
                       Both bots move simultaneously each turn. You must predict your opponent's move while avoiding walls and trails.
                     </p>
                  </div>
                </div>
              )}

              {activeTab === "io" && (
                <div className="space-y-8">
                  <div>
                     <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                        <Terminal size={20} className="text-yellow-400" /> Standard Input (State)
                     </h3>
                     <p className="text-gray-400 mb-4">{game.bot_io?.input || "JSON turn state via stdin"}</p>
                     
                     <div className="bg-gray-950 border border-gray-800 rounded-lg p-4 font-mono text-sm overflow-x-auto text-green-400 shadow-inner">
                        <pre>
{`{
  "turn": 1,
  "you": "p0",
  "board": [
    [0, 0, 0],
    [1, 0, 2],
    [0, 0, 0]
  ],
  "p0": {"x": 1, "y": 0},
  "p1": {"x": 1, "y": 2}
}`}
                        </pre>
                     </div>
                  </div>

                  <div>
                     <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                        <Code2 size={20} className="text-pink-400" /> Standard Output (Action)
                     </h3>
                     <p className="text-gray-400 mb-4">{game.bot_io?.output || "JSON object with \`move\` key"}</p>
                     <div className="bg-gray-950 border border-gray-800 rounded-lg p-4 font-mono text-sm overflow-x-auto text-blue-400 shadow-inner">
                        <pre>{`{"move": "UP"}`}</pre>
                     </div>
                     <p className="text-xs text-gray-500 mt-2">Valid moves: UP, DOWN, LEFT, RIGHT. Ensure newline (\`\\n\`) after output.</p>
                  </div>
                </div>
              )}

              {activeTab === "tech" && (
                <div className="space-y-6">
                  <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                    <h3 className="font-bold text-gray-300 mb-4">Supported Languages</h3>
                    <div className="flex flex-wrap gap-3">
                      {(game.supported_languages || ["python", "java", "c"]).map((lang) => (
                        <span key={lang} className="px-4 py-2 rounded bg-gray-950 border border-gray-800 text-sm font-mono capitalize">
                          {lang}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                    <h3 className="font-bold text-gray-300 mb-4">Engine Identifier</h3>
                    <code className="px-4 py-2 rounded bg-gray-950 border border-gray-800 text-sm text-pink-400 inline-block">
                      {game.key} / {game.visualizer_key}
                    </code>
                  </div>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Right Column: Sticky Action Bar */}
        <div className="lg:w-[320px] shrink-0">
          <div className="sticky top-28 bg-gray-900/80 backdrop-blur-xl border border-gray-800 rounded-3xl p-6 shadow-2xl flex flex-col">
            <div className="w-16 h-16 bg-blue-500/10 text-blue-400 rounded-2xl flex items-center justify-center mb-6 border border-blue-500/20 shadow-inner">
              <Play size={32} className="ml-1" />
            </div>
            
            <h2 className="text-2xl font-black mb-2 text-white">Ready to Battle?</h2>
            <p className="text-sm text-gray-400 mb-8 leading-relaxed">
              Create a dedicated room server for this game. You will be provided a secure room code to share with opponents before entering the workspace.
            </p>

            <div className="space-y-4">
              <Link 
                className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 px-6 rounded-xl transition-all shadow-[0_0_20px_rgba(37,99,235,0.3)] hover:shadow-[0_0_30px_rgba(37,99,235,0.5)]"
                to={`/create?game=${encodeURIComponent(gameKey || "tron")}`}
              >
                <span>Create Live Room</span>
              </Link>
              
              <Link 
                className="w-full flex items-center justify-center gap-2 bg-gray-950 hover:bg-gray-800 border border-gray-800 hover:border-gray-700 text-gray-300 font-semibold py-4 px-6 rounded-xl transition-all"
                to="/join"
              >
                <Zap size={18} className="text-yellow-400" />
                <span>Join Existing</span>
              </Link>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

function TabButton({ active, onClick, icon, label }) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 pb-4 font-bold text-sm transition-colors relative whitespace-nowrap ${
        active ? "text-blue-400" : "text-gray-500 hover:text-gray-300"
      }`}
    >
      {icon}
      {label}
      {active && (
         <motion.div 
           layoutId="activeTabIndicator"
           className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-400"
         />
      )}
    </button>
  );
}
