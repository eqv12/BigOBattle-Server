import { Link } from "react-router-dom";
import { Terminal, Swords, Zap, ChevronRight, Code } from "lucide-react";
import { motion } from "framer-motion";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-200 font-mono flex flex-col w-full">
      {/* Hero Section */}
      <section className="relative px-6 py-32 mx-auto max-w-7xl flex flex-col items-center text-center flex-grow">
        {/* Decorative background glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-green-500/10 blur-[120px] rounded-full pointer-events-none"></div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="relative z-10 mt-12"
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 mb-8 rounded-full border border-green-500/30 bg-green-500/10 text-green-400 text-sm">
            <Terminal size={14} />
            <span>v1.0 is live</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-black tracking-tight mb-6 bg-gradient-to-br from-green-400 to-blue-500 text-transparent bg-clip-text">
            CODE. COMPETE. CONQUER.
          </h1>
          
          <p className="max-w-2xl mx-auto text-lg md:text-xl text-gray-400 mb-10 leading-relaxed">
            Write autonomous bots in Python, Java, or C directly in your browser. 
            Spawn live rooms, invite your friends, and battle your code on the ultimate real-time LAN ladder.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link to="/games" className="group flex items-center gap-2 bg-green-600 hover:bg-green-500 text-gray-950 font-bold px-8 py-4 rounded-lg transition-all">
              <Swords size={20} />
              <span>Create Room</span>
              <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            
            <Link to="/join" className="flex items-center gap-2 px-8 py-4 rounded-lg border border-gray-700 hover:border-gray-500 hover:bg-gray-800 transition-all font-semibold text-gray-300">
              <Zap size={20} className="text-blue-400" />
              <span>Join a Room</span>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Features Grid */}
      <section className="py-24 px-6 relative z-10 bg-gray-900/50 border-t border-gray-800 w-full">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-100 mb-4">Built for Competetors</h2>
            <p className="text-gray-400">Everything you need to turn logic into victory.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <FeatureCard 
              icon={<Terminal className="text-green-400 w-8 h-8" />}
              title="Monaco Integration"
              desc="VS Code in your browser. Complete with syntax highlighting, autocomplete, and seamless file management."
            />
            <FeatureCard 
              icon={<Zap className="text-blue-400 w-8 h-8" />}
              title="Instant Sandbox Validation"
              desc="Run your code against varying tiers of benchmark bots to test your strategies before submission."
            />
            <FeatureCard 
              icon={<Swords className="text-red-400 w-8 h-8" />}
              title="Real-Time Visualizer"
              desc="Watch your bots face off with live game state playback right inside your editor workspace."
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-gray-800 text-center text-gray-500 w-full">
        <div className="flex justify-center items-center gap-2 mb-4">
          <Code size={20} />
          <span>Emergent Protocol</span>
        </div>
        <p className="text-sm">Built for the ultimate LAN coding tournament.</p>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, desc }) {
  return (
    <div className="bg-gray-900 border border-gray-800 p-8 rounded-xl hover:border-green-500/50 hover:bg-gray-800/80 transition-all duration-300">
      <div className="mb-4 bg-gray-950 w-14 h-14 flex items-center justify-center rounded-lg border border-gray-800">
        {icon}
      </div>
      <h3 className="text-xl font-bold text-gray-200 mb-3">{title}</h3>
      <p className="text-gray-400 leading-relaxed">{desc}</p>
    </div>
  );
}
