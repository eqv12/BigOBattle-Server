const createRoomForm = document.getElementById("createRoomForm");
const joinRoomForm = document.getElementById("joinRoomForm");
const submitBotForm = document.getElementById("submitBotForm");
const queueMatchForm = document.getElementById("queueMatchForm");
const monitorForm = document.getElementById("monitorForm");

const createRoomResult = document.getElementById("createRoomResult");
const joinRoomResult = document.getElementById("joinRoomResult");
const submitBotResult = document.getElementById("submitBotResult");
const queueMatchResult = document.getElementById("queueMatchResult");
const monitorResult = document.getElementById("monitorResult");

const leaderboardBody = document.getElementById("leaderboardBody");
const matchesBody = document.getElementById("matchesBody");
const toggleAutoRefreshBtn = document.getElementById("toggleAutoRefresh");
const toast = document.getElementById("toast");

let autoRefreshTimer = null;

function showToast(message) {
	toast.textContent = message;
	toast.classList.add("show");
	setTimeout(() => toast.classList.remove("show"), 2200);
}

function setResult(el, text, ok = true) {
	el.textContent = text;
	el.classList.toggle("ok", ok);
	el.classList.toggle("err", !ok);
}

function rememberRoom(roomCode) {
	localStorage.setItem("emergent_room_code", roomCode);
}

function hydrateRememberedRoom() {
	const saved = localStorage.getItem("emergent_room_code");
	if (!saved) {
		return;
	}
	for (const form of [joinRoomForm, submitBotForm, queueMatchForm, monitorForm]) {
		const input = form.querySelector("input[name='room_code']");
		if (input) {
			input.value = saved;
		}
	}
}

async function parseResponse(res) {
	let data = null;
	try {
		data = await res.json();
	} catch (_) {
		data = null;
	}
	return data;
}

function renderLeaderboard(rows) {
	if (!rows || rows.length === 0) {
		leaderboardBody.innerHTML = "<tr><td colspan='5' class='muted'>No data yet.</td></tr>";
		return;
	}
	leaderboardBody.innerHTML = rows.map((row) => `
		<tr>
			<td>${row.rank}</td>
			<td>${row.display_name}</td>
			<td>${row.rating}</td>
			<td>${row.rd}</td>
			<td>${row.matches_played}</td>
		</tr>
	`).join("");
}

function renderMatches(rows) {
	if (!rows || rows.length === 0) {
		matchesBody.innerHTML = "<tr><td colspan='6' class='muted'>No matches yet.</td></tr>";
		return;
	}
	matchesBody.innerHTML = rows.map((row) => `
		<tr>
			<td>${row.id}</td>
			<td>${row.participant_a_name}</td>
			<td>${row.participant_b_name}</td>
			<td>${row.winner_name || "Draw"}</td>
			<td>${row.termination_reason || "-"}</td>
			<td>${row.played_at}</td>
		</tr>
	`).join("");
}

async function refreshMonitor(roomCode) {
	if (!roomCode) {
		setResult(monitorResult, "Room code is required.", false);
		return;
	}

	const [leaderboardRes, matchesRes] = await Promise.all([
		fetch(`/api/rooms/${encodeURIComponent(roomCode)}/leaderboard`),
		fetch(`/api/rooms/${encodeURIComponent(roomCode)}/matches/recent?limit=20`),
	]);

	const leaderboard = await parseResponse(leaderboardRes);
	const matches = await parseResponse(matchesRes);

	if (!leaderboardRes.ok) {
		setResult(monitorResult, (leaderboard && leaderboard.error) || "Failed loading leaderboard.", false);
		return;
	}
	if (!matchesRes.ok) {
		setResult(monitorResult, (matches && matches.error) || "Failed loading matches.", false);
		return;
	}

	renderLeaderboard(leaderboard);
	renderMatches(matches);
	setResult(monitorResult, `Updated ${new Date().toLocaleTimeString()}.`, true);
}

createRoomForm.addEventListener("submit", async (e) => {
	e.preventDefault();
	const gameKey = new FormData(createRoomForm).get("game_key");

	const res = await fetch("/api/rooms", {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ game_key: gameKey }),
	});

	const data = await parseResponse(res);
	if (!res.ok) {
		setResult(createRoomResult, (data && data.error) || "Room creation failed.", false);
		return;
	}

	rememberRoom(data.room_code);
	hydrateRememberedRoom();
	setResult(createRoomResult, `Room ${data.room_code} created. Admin password: ${data.admin_password}`, true);
	showToast(`Room ${data.room_code} created`);
});

joinRoomForm.addEventListener("submit", async (e) => {
	e.preventDefault();
	const fd = new FormData(joinRoomForm);
	const roomCode = String(fd.get("room_code") || "").trim();
	const displayName = String(fd.get("display_name") || "").trim();

	const res = await fetch(`/api/rooms/${encodeURIComponent(roomCode)}/join`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ display_name: displayName }),
	});

	const data = await parseResponse(res);
	if (!res.ok) {
		setResult(joinRoomResult, (data && data.error) || "Join failed.", false);
		return;
	}

	rememberRoom(roomCode);
	hydrateRememberedRoom();
	setResult(joinRoomResult, `${displayName} joined room ${roomCode}. participant_id=${data.participant_id}`, true);
	showToast(`${displayName} joined room ${roomCode}`);
});

submitBotForm.addEventListener("submit", async (e) => {
	e.preventDefault();
	const fd = new FormData(submitBotForm);
	const roomCode = String(fd.get("room_code") || "").trim();
	const res = await fetch(`/api/rooms/${encodeURIComponent(roomCode)}/submit`, {
		method: "POST",
		body: fd,
	});

	const data = await parseResponse(res);
	if (!res.ok) {
		setResult(submitBotResult, (data && data.error) || "Upload failed.", false);
		return;
	}

	rememberRoom(roomCode);
	hydrateRememberedRoom();
	setResult(submitBotResult, `${data.message}. Password initialized: ${data.password_initialized}`, true);
	showToast(`Bot uploaded for ${data.display_name}`);
});

queueMatchForm.addEventListener("submit", async (e) => {
	e.preventDefault();
	const roomCode = String(new FormData(queueMatchForm).get("room_code") || "").trim();
	const res = await fetch(`/api/rooms/${encodeURIComponent(roomCode)}/queue-match`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({}),
	});

	const data = await parseResponse(res);
	if (!res.ok) {
		setResult(queueMatchResult, (data && data.error) || "Queue failed.", false);
		return;
	}

	setResult(queueMatchResult, `Queued ${data.participant_a_id} vs ${data.participant_b_id}`, true);
	showToast(`Match queued in ${roomCode}`);
	await refreshMonitor(roomCode);
});

monitorForm.addEventListener("submit", async (e) => {
	e.preventDefault();
	const roomCode = String(new FormData(monitorForm).get("room_code") || "").trim();
	rememberRoom(roomCode);
	hydrateRememberedRoom();
	await refreshMonitor(roomCode);
});

toggleAutoRefreshBtn.addEventListener("click", async () => {
	if (autoRefreshTimer) {
		clearInterval(autoRefreshTimer);
		autoRefreshTimer = null;
		toggleAutoRefreshBtn.textContent = "Start Auto Refresh";
		setResult(monitorResult, "Auto refresh stopped.", true);
		return;
	}

	const roomCode = String(new FormData(monitorForm).get("room_code") || "").trim();
	if (!roomCode) {
		setResult(monitorResult, "Set room code first.", false);
		return;
	}

	await refreshMonitor(roomCode);
	autoRefreshTimer = setInterval(() => refreshMonitor(roomCode), 4000);
	toggleAutoRefreshBtn.textContent = "Stop Auto Refresh";
	setResult(monitorResult, "Auto refresh every 4s.", true);
});

hydrateRememberedRoom();
