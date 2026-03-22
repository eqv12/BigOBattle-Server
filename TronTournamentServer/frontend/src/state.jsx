import React, { createContext, useContext, useMemo, useState } from "react";

const RoomContext = createContext(null);

export function RoomProvider({ children }) {
  const [roomCode, setRoomCode] = useState(localStorage.getItem("room_code") || "");
  const [gameKey, setGameKey] = useState(localStorage.getItem("game_key") || "tron");
  const [displayName, setDisplayName] = useState(localStorage.getItem("display_name") || "");

  const updateRoomCode = (value) => {
    setRoomCode(value);
    localStorage.setItem("room_code", value);
  };

  const updateGameKey = (value) => {
    setGameKey(value);
    localStorage.setItem("game_key", value);
  };

  const updateDisplayName = (value) => {
    setDisplayName(value);
    localStorage.setItem("display_name", value);
  };

  const value = useMemo(
    () => ({
      roomCode,
      gameKey,
      displayName,
      updateRoomCode,
      updateGameKey,
      updateDisplayName,
    }),
    [roomCode, gameKey, displayName]
  );

  return <RoomContext.Provider value={value}>{children}</RoomContext.Provider>;
}

export function useRoom() {
  const context = useContext(RoomContext);
  if (!context) {
    throw new Error("useRoom must be used within RoomProvider");
  }
  return context;
}
