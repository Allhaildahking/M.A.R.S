"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

type Mode = "standard" | "dev";
type Message = { role: "user" | "assistant"; content: string };

const suggestions = [
  "Help me understand something",
  "Research an idea",
  "Help me build an app",
  "Think through a decision",
];

export default function HomePage() {
  const [mode, setMode] = useState<Mode>("standard");
  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [sending, setSending] = useState(false);
  const [apiStatus, setApiStatus] = useState<"checking" | "connected" | "disconnected">("checking");
  const [conversationId, setConversationId] = useState(() => `mars-${Date.now()}`);
  const composerRef = useRef<HTMLTextAreaElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let active = true;
    fetch("/api/health", { cache: "no-store" })
      .then((response) => {
        if (!response.ok) throw new Error("API unavailable");
        return response.json();
      })
      .then((payload) => {
        if (active) setApiStatus(payload.status === "ok" ? "connected" : "disconnected");
      })
      .catch(() => {
        if (active) setApiStatus("disconnected");
      });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, sending]);

  function newChat() {
    setMessages([]);
    setPrompt("");
    setConversationId(`mars-${Date.now()}`);
    composerRef.current?.focus();
  }

  async function sendPrompt(event?: FormEvent<HTMLFormElement>, suggested?: string) {
    event?.preventDefault();
    const value = (suggested ?? prompt).trim();
    if (!value || sending) return;

    setPrompt("");
    setMessages((current) => [...current, { role: "user", content: value }]);
    setSending(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: value, conversation_id: conversationId, mode }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(typeof payload.error === "string" ? payload.error : "M.A.R.S. could not complete the request.");
      }
      if (typeof payload.answer !== "string") throw new Error("The backend returned an unexpected response.");
      setMessages((current) => [...current, { role: "assistant", content: payload.answer }]);
      setApiStatus("connected");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not reach M.A.R.S.";
      setMessages((current) => [...current, { role: "assistant", content: message }]);
      setApiStatus("disconnected");
    } finally {
      setSending(false);
    }
  }

  return (
    <main className="mars-app">
      <aside className="sidebar">
        <button className="brand" onClick={newChat} aria-label="M.A.R.S. new chat">
          <span className="brand-mark">M</span><span>M.A.R.S.</span>
        </button>
        <button className="new-chat" onClick={newChat}><span>＋</span> New chat</button>
        <div className="sidebar-label">YOUR SPACE</div>
        <p className="sidebar-empty">Your recent chats will appear here.</p>
        <div className="sidebar-bottom">
          <div className="region-note"><span className="region-dot" /> Nigeria-first, globally aware</div>
          <div className="connection"><span className={`connection-dot ${apiStatus}`} />{apiStatus === "checking" ? "Connecting…" : apiStatus === "connected" ? "Connected" : "Offline"}</div>
        </div>
      </aside>

      <section className="chat-area">
        <header className="topbar">
          <div className="mobile-brand"><span className="brand-mark">M</span> M.A.R.S.</div>
          <div className="mode-picker" aria-label="Choose mode">
            <button className={mode === "standard" ? "mode-option selected" : "mode-option"} onClick={() => setMode("standard")}>Standard</button>
            <button className={mode === "dev" ? "mode-option selected" : "mode-option"} onClick={() => setMode("dev")}>Dev</button>
          </div>
        </header>

        <div className={messages.length ? "conversation has-messages" : "conversation"}>
          {messages.length === 0 ? (
            <div className="welcome">
              <div className="welcome-mark">M</div>
              <h1>What are we working on?</h1>
              <p>Ask anything. Start with a question, an idea, or a problem you want to solve.</p>
              <div className="suggestions">
                {suggestions.map((item) => <button key={item} onClick={() => sendPrompt(undefined, item)}>{item}<span>↗</span></button>)}
              </div>
            </div>
          ) : (
            <div className="message-list">
              {messages.map((message, index) => (
                <article className={`message ${message.role}`} key={`${message.role}-${index}`}>
                  {message.role === "assistant" && <div className="assistant-mark">M</div>}
                  <div className="message-content">
                    {message.role === "user" && <span className="message-label">You</span>}
                    <p>{message.content}</p>
                  </div>
                </article>
              ))}
              {sending && <article className="message assistant"><div className="assistant-mark">M</div><div className="message-content"><p className="thinking">Thinking<span>.</span><span>.</span><span>.</span></p></div></article>}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <div className="composer-wrap">
          <form className="composer" onSubmit={sendPrompt}>
            <label className="sr-only" htmlFor="mars-composer">Message M.A.R.S.</label>
            <textarea
              ref={composerRef}
              id="mars-composer"
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="Message M.A.R.S."
              rows={1}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  event.currentTarget.form?.requestSubmit();
                }
              }}
            />
            <div className="composer-footer">
              <span className="composer-hint">{mode === "standard" ? "Standard mode" : "Dev mode"}</span>
              <button className="send-button" type="submit" aria-label="Send message" disabled={!prompt.trim() || sending}>{sending ? "…" : "↑"}</button>
            </div>
          </form>
          <p className="disclaimer">M.A.R.S. can make mistakes. Check important information.</p>
        </div>
      </section>
    </main>
  );
}
