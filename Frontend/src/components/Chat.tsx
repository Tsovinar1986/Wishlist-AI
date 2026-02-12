"use client";

import { useState } from "react";

export default function Chat() {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState("");

  const sendMessage = async () => {
    const res = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message }),
    });

    const data = await res.json();
    setResponse(data.response);
  };

  return (
    <div className="bg-white p-6 rounded-xl shadow-md w-96">
      <h1 className="text-xl font-bold mb-4">AI Chat</h1>

      <input
        className="w-full border p-2 mb-4"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Type your message..."
      />

      <button
        onClick={sendMessage}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        Send
      </button>

      {response && (
        <div className="mt-4 p-3 bg-gray-100 rounded">
          {response}
        </div>
      )}
    </div>
  );
}
