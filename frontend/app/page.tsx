"use client";

import { FormEvent, useState } from "react";

type Section = "Home" | "Workspace" | "Projects" | "Research" | "System Lab";
const sections: { name: Section; mark: string }[] = [
  { name: "Home", mark: "⌂" }, { name: "Workspace", mark: "▤" }, { name: "Projects", mark: "▦" },
  { name: "Research", mark: "⌕" }, { name: "System Lab", mark: "⌘" },
];
const starters = [
  { mark: "↗", title: "Research a topic", detail: "Compare sources and surface useful findings." },
  { mark: "</>", title: "Build something", detail: "Plan a feature, review code, or solve a bug." },
  { mark: "◷", title: "Think it through", detail: "Turn a rough idea into a clear next step." },
];

export default function HomePage() {
  const [section, setSection] = useState<Section>("Home");
  const [prompt, setPrompt] = useState("");
  const [drafts, setDrafts] = useState<string[]>([]);
  const [notice, setNotice] = useState("Development preview · backend not connected");

  function sendPrompt(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = prompt.trim();
    if (!value) return;
    setDrafts((current) => [...current, value]);
    setPrompt("");
    setNotice("Saved in this page only. Connect the M.A.R.S. API for real responses.");
    setSection("Workspace");
  }

  function startWith(title: string) {
    const prefixes: Record<string, string> = {
      "Research a topic": "Help me research: ",
      "Build something": "Help me plan and build: ",
      "Think it through": "Help me think through this idea: ",
    };
    setPrompt(prefixes[title] || "");
    document.getElementById("mars-composer")?.focus();
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <button className="brand" onClick={() => setSection("Home")} aria-label="M.A.R.S. home">
          <span className="brand-mark"><i /></span><span className="brand-copy"><strong>M.A.R.S.</strong><small>PERSONAL SYSTEM</small></span>
        </button>
        <button className="new-session" onClick={() => { setDrafts([]); setSection("Home"); setNotice("New local session · backend not connected"); }}><b>＋</b> New session <kbd>⌘ K</kbd></button>
        <p className="nav-label">WORKSPACE</p>
        <nav className="main-nav" aria-label="Main navigation">
          {sections.map((item) => <button key={item.name} className={section === item.name ? "nav-item active" : "nav-item"} onClick={() => setSection(item.name)}><span className="nav-mark">{item.mark}</span><span>{item.name}</span>{item.name === "System Lab" && <i className="nav-dot" />}</button>)}
        </nav>
        <div className="sidebar-bottom">
          <div className="side-status"><i className="status-led" /><div><strong>Local preview</strong><small>API disconnected</small></div><span className="more-mark">···</span></div>
          <button className="nav-item" onClick={() => setNotice("Settings will be added when preferences and session storage are defined.")}><span className="nav-mark">⚙</span> Settings</button>
          <div className="profile-row"><div className="avatar">DG</div><div className="profile-copy"><strong>Workspace owner</strong><small>Personal environment</small></div><span className="more-mark">···</span></div>
        </div>
      </aside>

      <section className="main-panel">
        <header className="topbar"><div className="breadcrumb"><span>Studio</span><b>/</b><strong>{section}</strong></div><div className="topbar-right"><span className="environment"><i className="status-led amber" /> LOCAL ENVIRONMENT</span><button className="icon-button" aria-label="Help" onClick={() => setNotice("Choose a workspace section or start with a prompt.")}>?</button></div></header>
        {section === "Home" ? (
          <div className="home-content">
            <div className="eyebrow"><i /> YOUR PRIVATE BUILDER&apos;S STUDIO</div>
            <div className="hero-title"><h1>Make room<br />for <em>better thinking.</em></h1><p>A workspace for ideas, research, and the things you&apos;re here to build.</p></div>
            <form className="composer" onSubmit={sendPrompt}>
              <label className="sr-only" htmlFor="mars-composer">Message M.A.R.S.</label>
              <textarea id="mars-composer" value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="What are we working on?" rows={2} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); } }} />
              <div className="composer-footer"><span className="composer-hint"><b>✳</b> Be curious. Be specific.</span><div className="composer-actions"><span className="key-hint">↵ to send · shift + ↵ for new line</span><button className="send-button" type="submit" aria-label="Send message" disabled={!prompt.trim()}>↑</button></div></div>
            </form>
            <div className="section-heading"><div><span className="section-kicker">START SOMEWHERE</span><h2>What do you need today?</h2></div><span className="heading-index">01 / 03</span></div>
            <div className="starter-grid">{starters.map((item) => <button className="starter-card" key={item.title} onClick={() => startWith(item.title)}><span className="starter-icon">{item.mark}</span><span className="starter-title">{item.title}<b>↗</b></span><span className="starter-detail">{item.detail}</span></button>)}</div>
            <div className="lower-grid">
              <section className="lower-card"><div className="card-topline"><span className="section-kicker">PICK UP WHERE YOU LEFT OFF</span><span className="subtle-index">02</span></div><h3>Recent work</h3><div className="empty-state"><span>↳</span><div><strong>No saved sessions yet</strong><p>Your conversations will show up here once session storage is connected.</p></div></div></section>
              <section className="lower-card"><div className="card-topline"><span className="section-kicker">SYSTEM STATUS</span><span className="subtle-index">03</span></div><h3>Under the hood</h3><div className="system-row"><span>Interface</span><strong><i className="status-led" /> Running locally</strong></div><div className="system-row"><span>Backend API</span><strong className="muted-value">Not connected</strong></div><div className="system-row"><span>Tool permissions</span><strong className="muted-value">Not queried</strong></div></section>
            </div>
          </div>
        ) : (
          <div className="section-placeholder"><div className="placeholder-mark">{sections.find((item) => item.name === section)?.mark}</div><span className="section-kicker">WORKSPACE MODULE</span><h1>{section}</h1><p>{section === "System Lab" ? "A clear view of capability health, tool permissions, and test results. This panel will show real system data once the backend exposes it." : section === "Projects" ? "A home for the work you care about. Project storage is not connected yet." : section === "Research" ? "Source-backed research belongs here. Search tools will be connected through the backend, not simulated in the browser." : "Your working conversation will live here. This preview stores drafts locally in page state, but does not call an AI model."}</p>
          {section === "Workspace" && drafts.length > 0 && <div className="local-messages"><span className="section-kicker">LOCAL DRAFTS · NOT SENT</span>{drafts.map((draft, index) => <div className="local-message" key={index}>{draft}</div>)}</div>}<button className="back-home" onClick={() => setSection("Home")}>← Back to home</button></div>
        )}
        <footer className="footer-bar"><span><b className="mini-mark">M</b> M.A.R.S. <i>/</i> FOUNDATION 0.1</span><span className="footer-note">{notice}</span><span className="footer-build">BUILT FOR THE WORK <b>✳</b></span></footer>
      </section>
    </main>
  );
}
