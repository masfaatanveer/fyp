import { useEffect, useRef, useState, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import {
  MessageCircle,
  Phone,
  PhoneOff,
  Send,
  Sparkles,
  X,
  ChevronDown,
} from "lucide-react";

// ── Types ─────────────────────────────────────────────────────────────────────

type ChatRole = "user" | "assistant";

interface Message {
  id: string;
  role: ChatRole;
  content: string;
  ts: Date;
}

interface ChatWidgetProps {
  rollNo?: string;
  agentName?: string;
  description?: string;
  apiBase?: string;
  vapiPublicKey?: string;
  vapiAssistantId?: string;
}

interface StudentInfo {
  roll_no: string;
  name: string;
  program: string;
  section: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const QUICK_PROMPTS = [
  "Meri attendance kitni hai?",
  "Mera transcript dikhao",
  "Current courses kaun se hain?",
  "KFUEIT attendance policy kya hai?",
];

function makeId() {
  return typeof crypto !== "undefined" ? crypto.randomUUID() : `id_${Date.now()}_${Math.random()}`;
}

function formatTime(d: Date) {
  return d.toLocaleTimeString("en-PK", { hour: "2-digit", minute: "2-digit" });
}

// ── Typing indicator ──────────────────────────────────────────────────────────

function TypingDots() {
  return (
    <div className="cw-typing">
      <span /><span /><span />
    </div>
  );
}

// ── Message bubble ────────────────────────────────────────────────────────────

function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  return (
    <div className={`cw-row cw-row--${msg.role}`}>
      {!isUser && (
        <div className="cw-avatar">
          <Sparkles size={13} />
        </div>
      )}
      <div className={`cw-bubble cw-bubble--${msg.role}`}>
        {isUser ? (
          <p className="cw-bubble-text">{msg.content}</p>
        ) : (
          <div className="cw-bubble-text cw-markdown">
            <ReactMarkdown>{msg.content}</ReactMarkdown>
          </div>
        )}
        <span className="cw-ts">{formatTime(msg.ts)}</span>
      </div>
    </div>
  );
}

// ── Main widget ───────────────────────────────────────────────────────────────

export function ChatWidget({
  rollNo: rollNoProp,
  agentName = "KFUEIT Agent",
  description = "AI University Assistant",
  apiBase = "http://127.0.0.1:8000/api/agent",
  vapiPublicKey,
  vapiAssistantId,
}: ChatWidgetProps) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [callActive, setCallActive] = useState(false);
  const [showQuick, setShowQuick] = useState(true);
  const [sessionId] = useState(makeId);

  // Roll number login state
  const [student, setStudent] = useState<StudentInfo | null>(
    rollNoProp ? { roll_no: rollNoProp, name: "", program: "", section: "" } : null
  );
  const [rollInput, setRollInput] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState("");
  const rollInputRef = useRef<HTMLInputElement>(null);

  const rollNo = student?.roll_no ?? "";

  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "**Assalam o Alaikum!** Main KFUEIT Agent Assist hun.\n\nAapki attendance, transcript, courses, ya university policies ke bare mein pooch saktay hain.",
      ts: new Date(),
    },
  ]);

  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const hasInteracted = messages.length > 1;

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (!open) return;
    setTimeout(() => {
      if (!student) rollInputRef.current?.focus();
      else inputRef.current?.focus();
    }, 120);
  }, [open, student]);

  // Initialize Vapi SDK instance once public key is available
  useEffect(() => {
    if (!vapiPublicKey) return;
    // @ts-ignore
    if (window.__vapi) return;
    const init = () => {
      // @ts-ignore
      if (window.Vapi) {
        // @ts-ignore
        window.__vapi = new window.Vapi(vapiPublicKey);
      }
    };
    // @ts-ignore
    if (window.Vapi) init();
    else {
      const script = document.querySelector('script[src*="vapi.ai"]');
      if (script) script.addEventListener("load", init);
    }
  }, [vapiPublicKey]);

  const sendMessage = useCallback(
    async (text?: string) => {
      const query = (text ?? input).trim();
      if (!query || loading) return;

      setShowQuick(false);
      setInput("");
      setMessages((prev) => [
        ...prev,
        { id: makeId(), role: "user", content: query, ts: new Date() },
      ]);
      setLoading(true);

      try {
        const res = await fetch(`${apiBase}/query/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query, roll_no: rollNo, session_id: sessionId }),
        });
        const data = await res.json();
        setMessages((prev) => [
          ...prev,
          {
            id: makeId(),
            role: "assistant",
            content: data.response || data.error || "Sorry, valid response nahi mila.",
            ts: new Date(),
          },
        ]);
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            id: makeId(),
            role: "assistant",
            content: "Backend se connection nahi ho saka. Django server check karein.",
            ts: new Date(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [input, loading, apiBase, rollNo, sessionId]
  );

  async function handleLogin() {
    const rn = rollInput.trim().toUpperCase();
    if (!rn) return;
    setLoginLoading(true);
    setLoginError("");
    try {
      const res = await fetch(`${apiBase}/student/${rn}/`);
      const data = await res.json();
      if (!res.ok) {
        setLoginError(data.error || "Student not found.");
      } else {
        setStudent(data as StudentInfo);
      }
    } catch {
      setLoginError("Backend se connection nahi ho saka.");
    } finally {
      setLoginLoading(false);
    }
  }

  async function toggleCall() {
    if (!vapiPublicKey || !vapiAssistantId) {
      setMessages((prev) => [
        ...prev,
        {
          id: makeId(),
          role: "assistant",
          content:
            "Voice call ke liye Vapi configure nahi hai. `.env` mein `VITE_VAPI_PUBLIC_KEY` aur `VITE_VAPI_ASSISTANT_ID` set karein.",
          ts: new Date(),
        },
      ]);
      return;
    }
    if (callActive) {
      // @ts-ignore
      window.__vapi?.stop();
      setCallActive(false);
    } else {
      // @ts-ignore
      const vapi = window.__vapi;
      if (!vapi) {
        setMessages((prev) => [
          ...prev,
          { id: makeId(), role: "assistant", content: "Vapi SDK load nahi hua. Page reload karein.", ts: new Date() },
        ]);
        return;
      }
      vapi.start(vapiAssistantId, { metadata: { roll_no: rollNo } });
      setCallActive(true);
    }
  }

  return (
    <>
      {/* FAB */}
      <button className="cw-fab" onClick={() => setOpen((v) => !v)} aria-label="Toggle chat">
        {!open && <span className="cw-fab-pulse" />}
        {open ? <X size={22} /> : <MessageCircle size={22} />}
      </button>

      {/* Panel */}
      <div className={`cw-panel${open ? " cw-panel--open" : ""}`} aria-hidden={!open}>
        {/* Header */}
        <header className="cw-header">
          <div className="cw-header-identity">
            <div className="cw-header-avatar">
              <Sparkles size={16} />
            </div>
            <div>
              <p className="cw-header-name">{agentName}</p>
              <p className="cw-header-sub">
                <span className="cw-online-dot" />
                {student ? `${student.name} · ${student.roll_no}` : description}
              </p>
            </div>
          </div>
          <div className="cw-header-actions">
            {student && (
              <button
                className={`cw-icon-btn${callActive ? " cw-icon-btn--danger" : ""}`}
                onClick={toggleCall}
                title={callActive ? "End call" : "Start voice call"}
              >
                {callActive ? <PhoneOff size={15} /> : <Phone size={15} />}
              </button>
            )}
            {student && (
              <button
                className="cw-icon-btn"
                onClick={() => { setStudent(null); setRollInput(""); }}
                title="Switch student"
              >
                <X size={15} />
              </button>
            )}
            <button className="cw-icon-btn" onClick={() => setOpen(false)} title="Minimize">
              <ChevronDown size={15} />
            </button>
          </div>
        </header>

        {/* Login screen */}
        {!student ? (
          <div className="cw-login">
            <div className="cw-login-icon"><Sparkles size={28} /></div>
            <p className="cw-login-title">KFUEIT Student Portal</p>
            <p className="cw-login-sub">Apna roll number enter karein</p>
            <div className="cw-input-wrap" style={{ margin: "0 0 8px" }}>
              <input
                ref={rollInputRef}
                className="cw-input"
                value={rollInput}
                onChange={(e) => setRollInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleLogin()}
                placeholder="e.g. COSC221103029"
                disabled={loginLoading}
                style={{ textTransform: "uppercase" }}
              />
              <button
                className="cw-send"
                onClick={handleLogin}
                disabled={loginLoading || !rollInput.trim()}
                aria-label="Login"
              >
                <Send size={16} />
              </button>
            </div>
            {loginLoading && <p className="cw-login-sub">Verifying...</p>}
            {loginError && <p className="cw-login-error">{loginError}</p>}
          </div>
        ) : (
          <>
            {/* Messages */}
            <div className="cw-messages">
              {messages.map((msg) => (
                <MessageBubble key={msg.id} msg={msg} />
              ))}
              {loading && (
                <div className="cw-row cw-row--assistant">
                  <div className="cw-avatar"><Sparkles size={13} /></div>
                  <div className="cw-bubble cw-bubble--assistant"><TypingDots /></div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Quick prompts */}
            {showQuick && !hasInteracted && (
              <div className="cw-quick">
                {QUICK_PROMPTS.map((p) => (
                  <button key={p} className="cw-quick-btn" onClick={() => sendMessage(p)} disabled={loading}>
                    {p}
                  </button>
                ))}
              </div>
            )}
          </>
        )}

        {/* Input — only shown when logged in */}
        {student && (
          <footer className="cw-footer">
            <div className="cw-input-wrap">
              <input
                ref={inputRef}
                className="cw-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
                placeholder="Apna sawal likhein..."
                disabled={loading}
              />
              <button
                className="cw-send"
                onClick={() => sendMessage()}
                disabled={loading || !input.trim()}
                aria-label="Send"
              >
                <Send size={16} />
              </button>
            </div>
            <p className="cw-powered">
              <Sparkles size={11} className="cw-powered-icon" />
              Powered by AI · Responses are for guidance only
            </p>
          </footer>
        )}
      </div>
    </>
  );
}
