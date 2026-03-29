import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { joinRoom } from "../api";
import { useRoom } from "../state";
import { Zap, AlertTriangle, ArrowRight, Loader2, Gamepad2, Users, Keyboard } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function JoinRoomPage() {
  const [roomCodeInput, setRoomCodeInput] = useState("");
  const [nameInput, setNameInput] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [joined, setJoined] = useState(null);
  const { updateRoomCode, updateGameKey, updateDisplayName } = useRoom();
  const navigate = useNavigate();

  const onJoin = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await joinRoom(roomCodeInput, nameInput);
      setJoined(data);
      updateRoomCode(data.room_code);
      updateGameKey(data.game_key);
      updateDisplayName(data.display_name);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] px-4 w-full">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-lg bg-gray-900 border border-gray-800 rounded-3xl p-8 md:p-10 shadow-2xl relative overflow-hidden"
      >
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-1/2 bg-yellow-500/10 blur-[80px] pointer-events-none" />

        <div className="relative z-10">
          <AnimatePresence mode="wait">
            {!joined ? (
              <motion.div key="join-form" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div className="mb-8 text-center">
                  <div className="mx-auto w-16 h-16 bg-yellow-500/10 rounded-2xl flex items-center justify-center mb-6 border border-yellow-500/20 shadow-inner">
                    <Zap className="w-8 h-8 text-yellow-400" />
                  </div>
                  <h1 className="text-3xl font-black text-white mb-2">Connect to Arena</h1>
                  <p className="text-gray-400">Enter frequency code to drop in</p>
                </div>

                <form className="space-y-6" onSubmit={onJoin}>
                  <div className="space-y-2">
                    <label className="text-sm font-bold text-gray-300 ml-1">Room Code</label>
                    <input 
                      value={roomCodeInput} 
                      onChange={(e) => setRoomCodeInput(e.target.value.toUpperCase())} 
                      placeholder="e.g. AB12CD"
                      className="w-full bg-gray-950 border border-gray-800 text-white rounded-xl px-4 py-4 focus:outline-none focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500 transition-all font-mono tracking-widest text-center text-xl uppercase placeholder:text-gray-700"
                      required 
                      maxLength={6}
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-bold text-gray-300 ml-1">Display Name</label>
                    <input 
                      value={nameInput} 
                      onChange={(e) => setNameInput(e.target.value)} 
                      placeholder="GhostProtocol"
                      className="w-full bg-gray-950 border border-gray-800 text-white rounded-xl px-4 py-4 focus:outline-none focus:border-yellow-500 focus:ring-1 focus:ring-yellow-500 transition-all font-mono"
                      required 
                    />
                  </div>

                  {error && (
                    <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl flex items-center gap-3 text-sm">
                      <AlertTriangle className="w-5 h-5 shrink-0" />
                      {error}
                    </div>
                  )}

                  <button 
                    disabled={loading || !roomCodeInput || !nameInput} 
                    type="submit"
                    className="w-full flex items-center justify-center gap-3 bg-yellow-500 hover:bg-yellow-400 text-black font-black py-4 px-6 rounded-xl transition-all shadow-[0_0_20px_rgba(234,179,8,0.2)] hover:shadow-[0_0_30px_rgba(234,179,8,0.4)] disabled:opacity-50 disabled:pointer-events-none"
                  >
                    {loading ? <><Loader2 className="animate-spin w-5 h-5" /> Connecting...</> : <>Establish Link <ArrowRight className="w-5 h-5" /></>}
                  </button>
                </form>
              </motion.div>
            ) : (
              <motion.div 
                key="lobby" 
                initial={{ opacity: 0, scale: 0.95 }} 
                animate={{ opacity: 1, scale: 1 }}
                className="space-y-8"
              >
                <div className="text-center">
                  <div className="inline-flex items-center justify-center bg-green-500/10 text-green-400 border border-green-500/20 px-4 py-1.5 rounded-full text-sm font-bold tracking-widest uppercase mb-6">
                    Connection Established
                  </div>
                  <h2 className="text-4xl font-black text-white uppercase tracking-tight">{joined.game_key}</h2>
                  <p className="text-gray-400 font-mono mt-2">Room: {joined.room_code}</p>
                </div>

                <div className="bg-gray-950 border border-gray-800 rounded-2xl p-6 grid grid-cols-2 gap-4">
                  <div className="flex flex-col items-center justify-center p-4 bg-gray-900 rounded-xl border border-gray-800">
                    <Users className="text-blue-400 mb-2 w-6 h-6" />
                    <span className="text-xs text-gray-400 font-bold uppercase">Identity</span>
                    <span className="text-white font-mono mt-1">{joined.display_name}</span>
                  </div>
                  <div className="flex flex-col items-center justify-center p-4 bg-gray-900 rounded-xl border border-gray-800">
                    <Gamepad2 className="text-pink-400 mb-2 w-6 h-6" />
                    <span className="text-xs text-gray-400 font-bold uppercase">Engine</span>
                    <span className="text-white font-mono mt-1 uppercase">{joined.game_key}</span>
                  </div>
                </div>

                <div className="bg-blue-500/10 border border-blue-500/20 rounded-2xl p-6 text-center">
                  <p className="text-blue-200/80 text-sm">
                    Read the rules from the arena registry carefully before initializing your algorithms.
                  </p>
                </div>

                <div className="space-y-3">
                  <button 
                    onClick={() => navigate("/workspace")}
                    className="w-full flex items-center justify-center gap-3 bg-white hover:bg-gray-200 text-black font-bold py-4 px-6 rounded-xl transition-all shadow-lg"
                  >
                    <Keyboard className="w-5 h-5" /> Access Developer Workspace
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}
