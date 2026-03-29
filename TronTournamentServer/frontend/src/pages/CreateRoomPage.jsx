import { useMemo, useState, useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { createRoom, getGames } from "../api";
import { useRoom } from "../state";
import { Server, Lock, Copy, CheckCircle2, AlertTriangle, ArrowRight, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function CreateRoomPage() {
  const [searchParams] = useSearchParams();
  const preselectedGame = useMemo(() => searchParams.get("game") || "tron", [searchParams]);
  const [gameKey, setGameKey] = useState(preselectedGame);
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [copiedCode, setCopiedCode] = useState(false);
  
  const { updateRoomCode, updateGameKey } = useRoom();
  const navigate = useNavigate();

  useEffect(() => {
    getGames().then(setGames).catch(console.error);
  }, []);

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

  const copyToClipboard = (text, type) => {
    navigator.clipboard.writeText(text);
    if (type === "code") {
      setCopiedCode(true);
      setTimeout(() => setCopiedCode(false), 2000);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] px-4 w-full">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-lg bg-gray-900 border border-gray-800 rounded-3xl p-8 md:p-10 shadow-2xl relative overflow-hidden"
      >
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-1/2 bg-blue-500/10 blur-[80px] pointer-events-none" />

        <div className="relative z-10">
          <div className="mb-8 text-center">
            <div className="mx-auto w-16 h-16 bg-blue-500/10 rounded-2xl flex items-center justify-center mb-6 border border-blue-500/20 shadow-inner">
              <Server className="w-8 h-8 text-blue-400" />
            </div>
            <h1 className="text-3xl font-black text-white mb-2">Initialize Arena</h1>
            <p className="text-gray-400">Deploy a dedicated multiplayer server</p>
          </div>

          <AnimatePresence mode="wait">
            {!result ? (
              <motion.form 
                key="form"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                className="space-y-6" 
                onSubmit={onCreate}
              >
                <div className="space-y-2">
                  <label className="text-sm font-bold text-gray-300 ml-1">Select Engine</label>
                  <select 
                    value={gameKey} 
                    onChange={(e) => setGameKey(e.target.value)}
                    className="w-full bg-gray-950 border border-gray-800 text-white rounded-xl px-4 py-4 appearance-none focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all font-mono"
                  >
                    {games.length > 0 ? (
                      games.map(g => (
                        <option key={g.key} value={g.key}>{g.title}</option>
                      ))
                    ) : (
                      <option value="tron">Tron</option>
                    )}
                  </select>
                </div>

                {error && (
                  <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl flex items-center gap-3 text-sm">
                    <AlertTriangle className="w-5 h-5 shrink-0" />
                    {error}
                  </div>
                )}

                <button 
                  disabled={loading} 
                  type="submit"
                  className="w-full flex items-center justify-center gap-3 bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 px-6 rounded-xl transition-all shadow-[0_0_20px_rgba(37,99,235,0.3)] hover:shadow-[0_0_30px_rgba(37,99,235,0.5)] disabled:opacity-50 disabled:pointer-events-none"
                >
                  {loading ? <><Loader2 className="animate-spin w-5 h-5" /> Deploying...</> : <>Generate Room <ArrowRight className="w-5 h-5" /></>}
                </button>
              </motion.form>
            ) : (
              <motion.div 
                key="success"
                initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                className="space-y-6"
              >
                <div className="bg-green-500/10 border border-green-500/20 rounded-2xl p-6 text-center">
                  <p className="text-green-400 font-bold mb-2 uppercase tracking-wider text-sm flex justify-center items-center gap-2">
                    <CheckCircle2 className="w-5 h-5" /> Server Active
                  </p>
                  <p className="text-gray-400 text-sm mb-4">Share this frequency code with entrants</p>
                  
                  <div 
                    onClick={() => copyToClipboard(result.room_code, 'code')}
                    className="group bg-gray-950 border border-gray-800 hover:border-gray-600 rounded-xl p-4 flex items-center justify-between cursor-pointer transition-all"
                  >
                    <span className="text-4xl font-black text-white tracking-[0.2em] font-mono mx-auto">
                      {result.room_code}
                    </span>
                    <button className="text-gray-500 group-hover:text-white transition-colors" type="button">
                      {copiedCode ? <CheckCircle2 className="text-green-500 w-6 h-6" /> : <Copy className="w-6 h-6" />}
                    </button>
                  </div>
                </div>

                <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-2xl p-5 flex flex-col items-center justify-center gap-2">
                  <Lock className="w-5 h-5 text-yellow-500 mb-1" />
                  <p className="text-xs text-yellow-200/50 uppercase tracking-widest font-bold">Admin Override PIN</p>
                  <code className="text-lg text-yellow-400 font-black">{result.admin_password}</code>
                </div>

                <button 
                  onClick={() => navigate("/workspace")}
                  className="w-full flex items-center justify-center gap-3 bg-white text-black hover:bg-gray-200 font-bold py-4 px-6 rounded-xl transition-all"
                >
                  Enter Workspace
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}
