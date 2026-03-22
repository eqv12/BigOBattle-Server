export async function jsonRequest(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error((data && data.error) || `Request failed: ${res.status}`);
  }
  return data;
}

export async function createRoom(gameKey) {
  return jsonRequest("/api/rooms", {
    method: "POST",
    body: JSON.stringify({ game_key: gameKey }),
  });
}

export async function getGames() {
  return jsonRequest("/api/games");
}

export async function getGameDetails(gameKey) {
  return jsonRequest(`/api/games/${encodeURIComponent(gameKey)}`);
}

export async function joinRoom(roomCode, displayName) {
  return jsonRequest(`/api/rooms/${encodeURIComponent(roomCode)}/join`, {
    method: "POST",
    body: JSON.stringify({ display_name: displayName }),
  });
}

export async function submitBot(roomCode, formData) {
  const res = await fetch(`/api/rooms/${encodeURIComponent(roomCode)}/submit`, {
    method: "POST",
    body: formData,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error((data && data.error) || `Submit failed: ${res.status}`);
  }
  return data;
}

export async function queueMatch(roomCode) {
  return jsonRequest(`/api/rooms/${encodeURIComponent(roomCode)}/queue-match`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function getLeaderboard(roomCode) {
  return jsonRequest(`/api/rooms/${encodeURIComponent(roomCode)}/leaderboard`);
}

export async function getRecentMatches(roomCode) {
  return jsonRequest(`/api/rooms/${encodeURIComponent(roomCode)}/matches/recent?limit=20`);
}

export async function getMatchReplay(roomCode, matchId) {
  return jsonRequest(`/api/rooms/${encodeURIComponent(roomCode)}/matches/${matchId}/replay`);
}

export async function getMatchRawOutput(roomCode, matchId) {
  return jsonRequest(`/api/rooms/${encodeURIComponent(roomCode)}/matches/${matchId}/raw-output`);
}

export async function testBot(roomCode, tier, formData) {
  const res = await fetch(`/api/rooms/${encodeURIComponent(roomCode)}/test`, {
    method: "POST",
    body: formData,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error((data && data.error) || `Test failed: ${res.status}`);
  }
  return data;
}
