import { useMemo, useState } from "react";
import Editor from "@monaco-editor/react";
import JSZip from "jszip";
import {
  getLeaderboard,
  getRecentMatches,
  queueMatch,
  submitBot,
  testBot,
  getMatchReplay,
  getMatchRawOutput,
  getTestJobStatus,
} from "../api";
import { useRoom } from "../state";
import ReplayViewer from "../components/replay/ReplayViewer";

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
    code: `#include <stdio.h>\n\nint main() {\n  char line[8192];\n  while (fgets(line, sizeof(line), stdin)) {\n    printf(\"{\\\"move\\\":\\\"UP\\\"}\\n\");\n    fflush(stdout);\n  }\n  return 0;\n}\n`,
    runSh: "gcc bot.c -O2 -o bot && ./bot\n",
    editorLanguage: "c",
  },
};

export default function WorkspacePage() {
  const { roomCode, displayName, gameKey } = useRoom();
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState(languageTemplates.python.code);
  const [password, setPassword] = useState("");
  const [tier, setTier] = useState("tier1");
  const [tab, setTab] = useState("replay");
  const [leaderboard, setLeaderboard] = useState([]);
  const [matches, setMatches] = useState([]);
  const [logs, setLogs] = useState("No logs yet.");
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
    <section className="workspace">
      <h1>Workspace: {roomCode}</h1>
      <div className="workspace-grid">
        <div className="editor-wrap">
          <div className="toolbar">
            <label>Tier
              <select value={tier} onChange={(e) => setTier(e.target.value)}>
                <option value="tier1">Tier 1</option>
                <option value="tier2">Tier 2</option>
                <option value="tier3">Tier 3</option>
              </select>
            </label>
            <label>Language
              <select value={language} onChange={(e) => onLanguageChange(e.target.value)}>
                <option value="python">Python</option>
                <option value="java">Java</option>
                <option value="c">C</option>
              </select>
            </label>
            <input
              type="password"
              placeholder="Submission password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <button className="btn secondary" onClick={onTest} disabled={isTesting || isSubmitting}>
              {isTesting ? "Testing..." : "Test"}
            </button>
            <button className="btn" onClick={onSubmit} disabled={isSubmitting || isTesting}>
              {isSubmitting ? "Submitting..." : "Submit"}
            </button>
            <button className="btn secondary" onClick={onQueue} disabled={isTesting || isSubmitting}>Queue Match</button>
            <button className="btn secondary" onClick={refresh} disabled={isTesting || isSubmitting}>Refresh</button>
          </div>
          <Editor
            height="62vh"
            defaultLanguage={languageTemplates[language].editorLanguage}
            language={languageTemplates[language].editorLanguage}
            value={code}
            onChange={(value) => setCode(value || "")}
            options={{ minimap: { enabled: false }, fontSize: 14 }}
          />
        </div>
        <div className="sidepanel">
          <div className="status-strip">
            <div className="status-item">
              <strong>Test:</strong> {testStatus}
              {isTesting && <span className="spinner" aria-hidden="true" />}
            </div>
            {submitStatus && (
              <div className="status-item">
                <strong>Submitted:</strong> {submitStatus.submittedAt}
              </div>
            )}
          </div>
          <div className="tabs">
            <button className={tab === "replay" ? "active" : ""} onClick={() => setTab("replay")}>Replay</button>
            <button className={tab === "logs" ? "active" : ""} onClick={() => setTab("logs")}>Logs</button>
            <button className={tab === "raw" ? "active" : ""} onClick={() => setTab("raw")}>Raw Output</button>
          </div>
          {tab === "replay" && (
            <ReplayViewer
              gameKey={(replayPayload && replayPayload.game_key) || gameKey || "tron"}
              replay={replayPayload && replayPayload.replay}
            />
          )}
          {tab === "logs" && <pre>{logs}</pre>}
          {tab === "raw" && <pre>{JSON.stringify(rawOutput || { message: "No raw output yet" }, null, 2)}</pre>}
          <h3>Recent Matches</h3>
          <ul>
            {matches.map((m) => (
              <li key={m.id}>
                <button className="btn secondary" onClick={() => loadMatchArtifacts(m.id)}>
                  Match {m.id}: {m.participant_a_name} vs {m.participant_b_name}
                </button>
              </li>
            ))}
          </ul>
          {selectedMatchId && <p>Selected match: {selectedMatchId}</p>}
          <h3>Leaderboard</h3>
          <ol>
            {leaderboard.map((row) => (
              <li key={row.rank}>{row.display_name} ({row.rating})</li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
