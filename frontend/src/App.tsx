import { ChatWidget } from "./components/ChatWidget/ChatWidget";
import { AdminDashboard } from "./components/AdminDashboard/AdminDashboard";
import { GraduationCap } from "lucide-react";

const isAdmin = window.location.hash === "#admin";

const NAV_LINKS = ["About", "Programs", "Admissions", "Research", "Campus Life"];

const STATS = [
  { value: "12K+", label: "Students" },
  { value: "60+",  label: "Programs" },
  { value: "450+", label: "Faculty" },
  { value: "98%",  label: "Satisfaction" },
];

export default function App() {
  if (isAdmin) {
    return <AdminDashboard apiBase="http://127.0.0.1:8000/api/agent" />;
  }

  return (
    <div className="page-root">
      {/* ── Decorative background blobs ── */}
      <div className="bg-blob bg-blob--tl" />
      <div className="bg-blob bg-blob--br" />
      <div className="bg-noise" />

      {/* ── Navigation ── */}
      <nav className="nav">
        <div className="nav-inner">
          <a href="/" className="nav-logo">
            <div className="nav-logo-icon">
              <GraduationCap size={20} strokeWidth={2} />
            </div>
            <div>
              <div className="nav-logo-name">KFUEIT</div>
              <div className="nav-logo-sub">KHWAJA FAREED UNIVERSITY</div>
            </div>
          </a>

          <ul className="nav-links">
            {NAV_LINKS.map((l) => (
              <li key={l}>
                <a href="#" className="nav-link">{l}</a>
              </li>
            ))}
          </ul>

          <a href="#" className="nav-cta">
            Apply now <span className="nav-cta-arrow">→</span>
          </a>
        </div>
      </nav>

      {/* ── Hero ── */}
      <main className="hero">
        <div className="hero-inner">
          <div className="hero-badge">
            <span className="hero-badge-dot">✦</span>
            Now with AI-powered student support
          </div>

          <h1 className="hero-headline">
            A legacy of{" "}
            <em className="hero-headline-gold">excellence</em>,<br />
            built for tomorrow.
          </h1>

          <p className="hero-subline">
            From engineering to the arts, Khwaja Fareed University empowers
            the next generation of changemakers with world-class faculty,
            modern facilities, and a vibrant campus community.
          </p>

          <div className="hero-actions">
            <a href="#" className="btn-primary">
              Explore Programs <span>→</span>
            </a>
            <a href="#" className="btn-ghost">Take a virtual tour</a>
          </div>
        </div>

        {/* ── Stats row ── */}
        <div className="stats-row">
          {STATS.map((s) => (
            <div className="stat-tile" key={s.label}>
              <span className="stat-value">{s.value}</span>
              <span className="stat-label">{s.label}</span>
            </div>
          ))}
        </div>
      </main>

      {/* ── Chat widget ── */}
      <ChatWidget
        agentName="KFUEIT Assistant"
        description="Online · usually replies instantly"
        apiBase="http://127.0.0.1:8000/api/agent"
        vapiPublicKey={import.meta.env.VITE_VAPI_PUBLIC_KEY}
        vapiAssistantId={import.meta.env.VITE_VAPI_ASSISTANT_ID}
      />
    </div>
  );
}
