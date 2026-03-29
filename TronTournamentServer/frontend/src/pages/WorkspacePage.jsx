import React, { useMemo, useState, useEffect } from "react";
import { Navigate } from "react-router-dom";
import Editor from "@monaco-editor/react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Code2,
  Terminal,
  PlaySquare,
  Activity,
  ScrollText,
  UploadCloud,
  FlaskConical,
  RefreshCw,
  Trophy,
} from "lucide-react";
import JSZip from "jszip";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  getLeaderboard,
  getRecentMatches,
  queueMatch,
  submitBot,
  testBot,
  getMatchReplay,
  getMatchRawOutput,
  getTestJobStatus,
  getGameDetails,
} from "../api";
import { useRoom } from "../state";
import ReplayViewer from "../components/replay/ReplayViewer";
import TurnLogsAccordion from "../components/TurnLogsAccordion";

const languageTemplates = {
  python: {
    filename: "bot.py",
    code: `import sys\nimport json\n\nfor line in sys.stdin:\n    if not line:\n        break\n    state = json.loads(line)\n    print(json.dumps({\"move\": \"UP\"}))\n    sys.stdout.flush()\n`,
    runSh: "python3 bot.py\n",
    editorLanguage: "python",
  },
  java: {
    filename: "Main.java",
    code: `import java.io.*;\nimport org.json.*;\n\npublic class Main {\n  public static void main(String[] args) throws Exception {\n    BufferedReader br = new BufferedReader(new InputStreamReader(System.in));\n    String line;\n    while ((line = br.readLine()) != null) {\n      JSONObject out = new JSONObject();\n      out.put(\"move\", \"UP\");\n      System.out.println(out.toString());\n      System.out.flush();\n    }\n  }\n}\n`,
    runSh: "javac -cp /usr/share/java/json.jar Main.java && java -cp .:/usr/share/java/json.jar Main\n",
    editorLanguage: "java",
  },
  c: {
    filename: "bot.c",
    code: `#include <stdio.h>\n\nint main() {\n  char line[8192];\n  while (fgets(line, sizeof(line), stdin)) {\n    printf("{\\"move\\":\\"UP\\"}\\n");\n    fflush(stdout);\n  }\n  return 0;\n}\n`,
    runSh: "gcc bot.c -O2 -o bot && ./bot\n",
    editorLanguage: "c",
  },
  cpp: {
    filename: "bot.cpp",
    code: `#include <iostream>\n#include <string>\n\nusing namespace std;\n\nint main() {\n  string line;\n  while (getline(cin, line)) {\n    cout << "{\\"move\\":\\"UP\\"}" << endl;\n  }\n  return 0;\n}\n`,
    runSh: "g++ bot.cpp -O2 -o bot && ./bot\n",
    editorLanguage: "cpp",
  },
  javascript: {
    filename: "bot.js",
    code: `const readline = require('readline');\n\nconst rl = readline.createInterface({\n  input: process.stdin,\n  output: process.stdout,\n  terminal: false\n});\n\nrl.on('line', (line) => {\n  console.log(JSON.stringify({ move: "UP" }));\n});\n`,
    runSh: "node bot.js\n",
    editorLanguage: "javascript",
  },
};

export default function WorkspacePage() {
  const { roomCode, displayName, gameKey } = useRoom();

  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState(languageTemplates.python.code);
  const [password, setPassword] = useState("");
  const [tier, setTier] = useState("tier1");
  const [tab, setTab] = useState("specs");
  
  const [leaderboard, setLeaderboard] = useState([]);
  const [matches, setMatches] = useState([]);
  const [logs, setLogs] = useState("No logs yet.");
  const [gameSpecs, setGameSpecs] = useState(null);

  const specsMarkdown = gameSpecs ? `
# ${gameSpecs.title}

${gameSpecs.description || gameSpecs.summary || ""}

### Rules

${(gameSpecs.rules || []).map(r => "- " + r).join("\n")}

### I/O Interfacing

Each turn, your bot will receive a JSON payload on \`stdin\` representing the current game state. You have **1.0s** for the first turn and **0.25s** for every turn thereafter to respond.

To make a move, you must print a valid JSON string containing your move to \`stdout\`.

#### Standard Input (stdin)
\`\`\`json
${gameSpecs.bot_io?.input || ""}
\`\`\`

#### Standard Output (stdout)
\`\`\`json
${gameSpecs.bot_io?.output || ""}
\`\`\`
` : "";

  if (!roomCode || !displayName) {
    return <Navigate to="/join" replace />;
  }
  
  useEffect(() => {
    async function loadSpecs() {
      try {
        const details = await getGameDetails(gameKey || "tron");
        setGameSpecs(details);
      } catch (err) {
        console.error("Failed to load game specs", err);
      }
    }
    loadSpecs();
  }, [gameKey]);
  const [replayPayload, setReplayPayload] = useState(null);
  const [rawOutput, setRawOutput] = useState(null);
  const [selectedMatchId, setSelectedMatchId] = useState(null);
  const [isTesting, setIsTesting] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [testStatus, setTestStatus] = useState("Idle");
  const [submitStatus, setSubmitStatus] = useState(null);

  const roomReady = useMemo(() => roomCode && displayName, [roomCode, displayName]);

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const formatNow = () => new Date().toLocaleString();

  const onLanguageChange = (nextLanguage) => {
    setLanguage(nextLanguage);
    setCode(languageTemplates[nextLanguage].code);
  };

  const loadMatchArtifacts = async (matchId) => {
    if (!roomCode || !matchId) return;
    try {
      const [replayData, rawData] = await Promise.all([
        getMatchReplay(roomCode, matchId),
        getMatchRawOutput(roomCode, matchId),
      ]);
      setReplayPayload(replayData);
      setRawOutput(rawData);
      setSelectedMatchId(matchId);
    } catch (err) {
      setLogs(err.message);
    }
  };

  const refresh = async () => {
    if (!roomCode) return;
    const [lb, rm] = await Promise.all([getLeaderboard(roomCode), getRecentMatches(roomCode)]);
    setLeaderboard(lb);
    setMatches(rm);
    if (rm.length > 0) {
      await loadMatchArtifacts(rm[0].id);
    }
  };

  const buildSubmissionZip = async () => {
    const template = languageTemplates[language];
    const zipBuilder = new JSZip();
    zipBuilder.file(template.filename, code);
    zipBuilder.file("run.sh", template.runSh);
    return zipBuilder.generateAsync({ type: "blob" });
  };

  const onSubmit = async () => {
    if (!roomReady) return;
    if (!password) {
      setLogs("Please enter your submission password before submitting.");
      setTab("logs");
      return;
    }
    const zip = await buildSubmissionZip();
    const form = new FormData();
    form.set("display_name", displayName);
    form.set("password", password);
    form.set("bot_zip_file", zip, "bot.zip");
    try {
      setIsSubmitting(true);
      const data = await submitBot(roomCode, form);
      const submittedAt = formatNow();
      setSubmitStatus({
        submittedAt,
        message: data.message || "Submission accepted.",
      });
      setLogs(`Submission accepted at ${submittedAt}.`);
      setTab("logs");
    } catch (err) {
      setLogs(err.message);
      setTab("logs");
    } finally {
      setIsSubmitting(false);
    }
  };

  const onTest = async () => {
    if (!roomReady) return;
    if (isTesting) return;

    const zip = await buildSubmissionZip();
    const form = new FormData();
    form.set("tier", tier);
    form.set("bot_zip_file", zip, "bot.zip");

    setIsTesting(true);
    setTestStatus(`Queued (${tier})`);
    setLogs("Test queued.");
    setTab("replay");

    try {
      const data = await testBot(roomCode, tier, form);

      const jobId = data.job_id;
      if (!jobId) {
        throw new Error("Test response missing job_id.");
      }

      setTestStatus(`Running (${jobId})`);
      let finalPayload = null;

      for (let i = 0; i < 120; i += 1) {
        await sleep(1000);
        const status = await getTestJobStatus(roomCode, jobId);
        setTestStatus(`${status.status || "unknown"} (${jobId})`);

        if (status.status === "success") {
          finalPayload = status;
          break;
        }
        if (status.status === "failed") {
          throw new Error(status.error || "Test job failed.");
        }
      }

      if (!finalPayload) {
        throw new Error("Timed out waiting for test result.");
      }

      setReplayPayload({
        game_key: finalPayload.game_key || gameKey || "tron",
        replay: finalPayload.replay,
        p0_name: displayName,
        p1_name: `Benchmark ${tier.toUpperCase()}`
      });
      setRawOutput({
        bot_raw_outputs: finalPayload.raw_output || {},
        turn_events: finalPayload.replay?.result?.turn_events || [],
      });
      setLogs(
        `Test complete. Winner: ${finalPayload.winner}, termination: ${finalPayload.termination}`
      );
      setTestStatus(`Completed (${jobId})`);
    } catch (err) {
      setLogs(err.message);
      setTestStatus("Failed");
      setTab("logs");
    } finally {
      setIsTesting(false);
    }
  };

  const onQueue = async () => {
    if (!roomCode) return;
    try {
      await queueMatch(roomCode);
      await refresh();
      setLogs("Match queued.");
    } catch (err) {
      setLogs(err.message);
    }
  };

  if (!roomReady) {
    return <p>Join a room first.</p>;
  }

  return (
    <div className="flex h-screen w-full bg-slate-950 text-slate-200 overflow-hidden font-sans">
      
      {/* LEFT PANE: IDE & Controls */}
      <div className="flex flex-col w-[55%] border-r border-slate-800 bg-[#0f172a] relative z-10 shadow-2xl">
        
        {/* Header Strip */}
        <div className="flex items-center justify-between px-6 py-4 bg-slate-900 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-500/10 border border-emerald-500/20 rounded-lg">
              <Terminal className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-100 tracking-tight">Arena Workspace</h1>
              <p className="text-xs text-slate-400 font-mono">ROOM_ID // <span className="text-emerald-400">{roomCode}</span></p>
            </div>
          </div>
          <div className="px-3 py-1.5 bg-slate-950 rounded-md border border-slate-800 text-xs font-mono text-slate-400">
            AGENT: <span className="text-indigo-400 ml-1">{displayName}</span>
          </div>
        </div>

        {/* Toolbar */}
        <div className="flex flex-wrap items-center gap-3 px-4 py-3 bg-slate-900/50 border-b border-slate-800 text-sm">
          
          <div className="flex items-center gap-2 bg-slate-950 px-2 py-1.5 rounded-md border border-slate-700/50 hover:border-slate-600 transition-colors">
            <span className="text-slate-500 font-mono text-xs">TIER</span>
            <select 
              value={tier} 
              onChange={(e) => setTier(e.target.value)}
              className="bg-transparent text-slate-200 outline-none cursor-pointer text-sm"
            >
              <option value="tier1">Tier 1 (Easy)</option>
              <option value="tier2">Tier 2 (Med)</option>
              <option value="tier3">Tier 3 (Hard)</option>
            </select>
          </div>

          <div className="flex items-center gap-2 bg-slate-950 px-2 py-1.5 rounded-md border border-slate-700/50 hover:border-slate-600 transition-colors">
            <span className="text-slate-500 font-mono text-xs">LANG</span>
            <select 
              value={language} 
              onChange={(e) => onLanguageChange(e.target.value)}
              className="bg-transparent text-slate-200 outline-none cursor-pointer text-sm"
            >
              <option value="python">Python</option>
              <option value="java">Java</option>
              <option value="c">C</option>
              <option value="cpp">C++</option>
              <option value="javascript">Node.js</option>
            </select>
          </div>
          
          <div className="flex-grow"></div>

          <input
            type="password"
            placeholder="Room Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-36 bg-slate-950 border border-slate-700/50 rounded-md px-3 py-1.5 text-slate-200 text-sm placeholder-slate-600 focus:outline-none focus:border-emerald-500/50 transition-colors"
          />

          <button 
            onClick={onTest} 
            disabled={isTesting || isSubmitting}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-100 px-4 py-1.5 rounded-md transition-colors disabled:opacity-50 border border-slate-700 font-medium"
          >
            {isTesting ? <RefreshCw className="w-4 h-4 text-emerald-400 animate-spin" /> : <FlaskConical className="w-4 h-4 text-indigo-400" />}
            Test
          </button>
          
          <button 
            onClick={onSubmit} 
            disabled={isSubmitting || isTesting}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-1.5 rounded-md transition-colors disabled:opacity-50 shadow-lg shadow-emerald-900/20 font-medium"
          >
            {isSubmitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <UploadCloud className="w-4 h-4" />}
            Submit
          </button>

        </div>

        {/* Editor Area */}
        <div className="flex-grow relative">
           <Editor
              height="100%"
              theme="vs-dark"
              defaultLanguage={languageTemplates[language].editorLanguage}
              language={languageTemplates[language].editorLanguage}
              value={code}
              onChange={(value) => setCode(value || "")}
              options={{ 
                minimap: { enabled: false }, 
                fontSize: 14,
                fontFamily: "JetBrains Mono, 'Courier New', monospace",
                padding: { top: 16 }
              }}
            />
        </div>
      </div>

      {/* RIGHT PANE: Intelligence & Data */}
      <div className="flex flex-col w-[45%] bg-[#020617]">
        
        {/* Right Pane Tab Navigation */}
        <div className="flex items-center gap-1 px-2 pt-2 border-b border-slate-800 bg-slate-900">
          {[
            { id: 'specs', label: 'Registry Specs', icon: ScrollText },
            { id: 'raw', label: 'I/O Inspector', icon: Activity },
            { id: 'logs', label: 'Console Logs', icon: Code2 },
            { id: 'replay', label: 'Visualizer', icon: PlaySquare },
            { id: 'arena', label: 'Arena Live', icon: Trophy }
          ].map((t) => {
            const Icon = t.icon;
            const isActive = tab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`relative flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors outline-none rounded-t-lg
                  ${isActive ? 'text-emerald-400 bg-slate-800/50' : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/30'}`}
              >
                <Icon className="w-4 h-4" />
                {t.label}
                {isActive && (
                  <motion.div
                    layoutId="activeTabIndicator"
                    className="absolute bottom-[-1px] left-0 right-0 h-0.5 bg-emerald-400"
                    initial={false}
                  />
                )}
              </button>
            )
          })}
        </div>

        {/* Right Pane Content Area */}
        <div className="flex-grow w-full relative overflow-y-auto p-6 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
          <AnimatePresence mode="wait">
            
            {tab === "specs" && (
              <motion.div 
                key="specs"
                initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }}
                className="prose prose-invert prose-emerald max-w-none text-slate-300"
              >
                {gameSpecs ? (
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={{
                      h1: ({node, ...props}) => <h1 className="text-3xl font-black text-emerald-400 mb-6 tracking-tight" {...props} />,
                      h3: ({node, ...props}) => <h3 className="text-xl font-bold text-slate-200 mt-8 mb-4 flex items-center gap-2 border-b border-slate-800 pb-2" {...props} />,
                      h4: ({node, ...props}) => <h4 className="text-sm font-bold text-slate-500 mt-6 mb-2 uppercase tracking-widest font-mono" {...props} />,
                      p: ({node, ...props}) => <p className="text-slate-300 leading-relaxed mb-4 text-sm" {...props} />,
                      ul: ({node, ...props}) => <ul className="list-none space-y-2 mb-6" {...props} />,
                      li: ({node, ...props}) => (
                        <li className="text-slate-300 text-sm flex gap-3 items-start" {...props}>
                          <span className="text-emerald-500 font-bold mt-0.5">›</span>
                          <span>{props.children}</span>
                        </li>
                      ),
                      code: ({inline, node, ...props}) => (
                        <code className="bg-slate-900 text-indigo-300 px-1.5 py-0.5 rounded font-mono text-xs border border-slate-800" {...props} />
                      ),
                      blockquote: ({node, ...props}) => (
                        <blockquote className="border-l-2 border-emerald-500/50 pl-4 py-2 bg-gradient-to-r from-emerald-500/10 to-transparent rounded-r-lg my-3 font-mono text-sm text-slate-300" {...props} />
                      )
                    }}
                  >
                    {specsMarkdown}
                  </ReactMarkdown>
                ) : (
                  <div className="flex items-center gap-3 text-slate-500">
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    <p>Loading registry specifications...</p>
                  </div>
                )}
              </motion.div>
            )}

            {tab === "raw" && (
              <motion.div key="raw" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <h3 className="text-slate-300 font-mono mb-4 flex justify-between items-center border-b border-slate-800 pb-2">
                  <span className="flex items-center gap-2"><Activity className="w-4 h-4 text-indigo-400"/> RAW I/O TELEMETRY</span>
                  <span className="text-xs text-slate-500 bg-slate-900 px-2 py-1 rounded">MATCH/ID: {selectedMatchId || 'N/A'}</span>
                </h3>
                <TurnLogsAccordion rawOutput={rawOutput} />
              </motion.div>
            )}

            {tab === "logs" && (
              <motion.div key="logs" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full">
                <div className="bg-[#0a0f1d] border border-slate-800 rounded-lg overflow-hidden flex flex-col min-h-[400px]">
                  <div className="bg-slate-900 px-4 py-2 border-b border-slate-800 flex justify-between items-center">
                    <span className="text-xs font-mono text-slate-400 flex items-center gap-2"><Code2 className="w-4 h-4"/> process.stdout</span>
                    <div className="flex items-center gap-2">
                       {testStatus !== "Idle" && <span className="text-xs text-emerald-400 font-mono bg-emerald-400/10 px-2 py-0.5 rounded border border-emerald-400/20">{testStatus}</span>}
                    </div>
                  </div>
                  <div className="p-4 overflow-y-auto font-mono text-sm text-slate-300 whitespace-pre-wrap">
                    {logs}
                  </div>
                </div>
              </motion.div>
            )}

            {tab === "replay" && (
              <motion.div key="replay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="h-full flex flex-col absolute inset-0 p-6 pb-8">
                 <ReplayViewer
                    gameKey={(replayPayload && replayPayload.game_key) || gameKey || "tron"}
                    replay={replayPayload && replayPayload.replay}
                    p0Name={replayPayload?.p0_name || replayPayload?.participant_a_name}
                    p1Name={replayPayload?.p1_name || replayPayload?.participant_b_name}
                  />
              </motion.div>
            )}

            {tab === "arena" && (
              <motion.div key="arena" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
                
                {/* Match Control */}
                <div className="p-6 bg-slate-900 border border-slate-800 rounded-xl relative overflow-hidden">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-3xl"></div>
                  <h3 className="text-lg font-bold text-slate-200 mb-2 relative z-10 flex items-center gap-2"><Trophy className="w-5 h-5 text-yellow-400"/> Arena Commands</h3>
                  <p className="text-sm text-slate-400 mb-6 relative z-10">Queue your bot to play a rated match against an opponent on the server.</p>
                  <div className="flex gap-4 relative z-10">
                    <button onClick={onQueue} disabled={isTesting || isSubmitting} className="bg-emerald-600 hover:bg-emerald-500 text-white px-6 py-2.5 rounded-md font-medium transition-colors shadow-lg shadow-emerald-900/20 flex items-center gap-2">
                      <PlaySquare className="w-4 h-4" /> Submit
                    </button>
                    <button onClick={refresh} disabled={isTesting || isSubmitting} className="bg-slate-800 hover:bg-slate-700 text-slate-200 px-6 py-2.5 rounded-md font-medium transition-colors flex items-center gap-2 border border-slate-700">
                      <RefreshCw className="w-4 h-4" /> Refresh Leaderboard
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  {/* Leaderboard */}
                  <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col max-h-96">
                    <div className="bg-slate-950 px-4 py-3 border-b border-slate-800">
                      <h3 className="font-bold text-slate-300 text-sm flex items-center gap-2">
                         Room ELO Rankings
                      </h3>
                    </div>
                    <ul className="divide-y divide-slate-800/50 overflow-y-auto">
                      {leaderboard.filter(r => r.matches_played > 0).length === 0 && (
                        <li className="p-4 text-sm text-slate-500 text-center">No ranked players yet</li>
                      )}
                      {leaderboard.filter(row => row.matches_played > 0).map((row, idx) => (
                        <li key={row.rank} className="p-3 flex justify-between items-center text-sm hover:bg-slate-800/30 transition-colors">
                          <div className="flex items-center gap-3">
                            <span className="text-slate-600 font-mono w-4 font-bold">{idx + 1}.</span>
                            <span className="text-slate-200 font-medium">{row.display_name}</span>
                          </div>
                          <span className="text-emerald-400 font-mono bg-emerald-400/10 px-2 py-0.5 rounded text-xs">{row.rating}</span>
                        </li>
                      ))}
                      {leaderboard.filter(r => r.matches_played === 0).length > 0 && (
                        <li className="p-3 text-xs text-slate-500 text-center border-t border-slate-800/50 flex align-center justify-center italic">
                          {leaderboard.filter(r => r.matches_played === 0).length} unranked players hidden
                        </li>
                      )}
                    </ul>
                  </div>

                  {/* Matches */}
                  <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col max-h-96">
                    <div className="bg-slate-950 px-4 py-3 border-b border-slate-800">
                      <h3 className="font-bold text-slate-300 text-sm">Recent Matches</h3>
                    </div>
                    <ul className="divide-y divide-slate-800/50 overflow-y-auto">
                      {matches.length === 0 && <li className="p-4 text-sm text-slate-500 text-center">No matches found</li>}
                      {matches.map((m) => (
                        <li key={m.id} className="p-0">
                          <button 
                            onClick={() => { loadMatchArtifacts(m.id); setTab("replay"); }}
                            className="w-full text-left p-3 hover:bg-slate-800/50 transition-colors flex flex-col gap-1 group"
                          >
                            <span className="text-xs font-mono text-slate-500 group-hover:text-indigo-400 transition-colors">ID: {m.id}</span>
                            <span className="text-sm text-slate-300">
                              {m.participant_a_name} <span className="text-slate-600 px-1 text-xs">vs</span> {m.participant_b_name}
                            </span>
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

              </motion.div>
            )}

          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
