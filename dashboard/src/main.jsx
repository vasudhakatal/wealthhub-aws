import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  LayoutDashboard,
  Users,
  ArrowUpRight,
  ArrowDownToLine,
  Wallet,
  ShieldCheck,
  LogOut,
  Activity,
  Layers,
  ChevronRight,
} from "lucide-react";
import "./style.css";
const money = (v) =>
  new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
    maximumFractionDigits: 0,
  }).format(v);
const colors = ["#178f7c", "#88bcb0", "#dcb878"];
function App() {
  const [token, setToken] = useState(""),
    [page, setPage] = useState("overview"),
    [portfolio, setPortfolio] = useState(null),
    [performance, setPerformance] = useState([]),
    [jobs, setJobs] = useState([]),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [notice, setNotice] = useState("");
  async function api(path, options = {}) {
    const r = await fetch("/api" + path, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: "Bearer " + token } : {}),
        ...options.headers,
      },
    });
    if (!r.ok) {
      if (r.status === 401) setToken("");
      let body = await r.json().catch(() => ({}));
      throw Error(
        typeof body.detail === "string"
          ? body.detail
          : "Please check the form and try again.",
      );
    }
    return r;
  }
  async function refresh() {
    try {
      const [p, h, j] = await Promise.all([
        api("/portfolio").then((r) => r.json()),
        api("/performance").then((r) => r.json()),
        api("/jobs").then((r) => r.json()),
      ]);
      setPortfolio(p);
      setPerformance(h.series);
      setJobs(j);
    } catch (e) {
      setError(e.message);
    }
  }
  useEffect(() => {
    if (token) {
      refresh();
      const timer = setInterval(() => {
        api("/jobs")
          .then((r) => r.json())
          .then(setJobs)
          .catch((e) => setError(e.message));
      }, 4000);
      return () => clearInterval(timer);
    }
  }, [token]);
  async function login(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = new FormData(e.target);
      const r = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(data)),
      });
      setToken((await r.json()).access_token);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function onboard(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    const form = e.target;
    try {
      await api("/onboard", {
        method: "POST",
        body: JSON.stringify(Object.fromEntries(new FormData(form))),
      });
      form.reset();
      setNotice(
        "Client queued. The worker will prepare the welcome PDF shortly.",
      );
      setJobs(await api("/jobs").then((r) => r.json()));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function download(id) {
    try {
      const r = await api(`/jobs/${id}/pdf`);
      const url = URL.createObjectURL(await r.blob());
      const a = document.createElement("a");
      a.href = url;
      a.download = "wealthhub-welcome.pdf";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      setError(e.message);
    }
  }
  if (!token)
    return (
      <div className="login">
        <div className="login-story">
          <div className="brand">
            <span className="brand-icon">
              <Layers size={23} />
            </span>{" "}
            WealthHub
          </div>
          <div>
            <span className="eyebrow">A CLEARER PICTURE OF WEALTH</span>
            <h1>
              One workspace.
              <br />
              Every possibility.
            </h1>
            <p>
              Bring banking, investments and super together.
              <br />
              Make your next decision with the whole picture.
            </p>
            <div className="login-chart">
              <span>Sample portfolio</span>
              <h2>
                $244,000 <small>AUD</small>
              </h2>
              <svg viewBox="0 0 500 120">
                <path
                  d="M0 108 L40 95 L80 99 L120 72 L160 78 L200 53 L240 62 L280 35 L320 43 L360 18 L400 24 L450 7 L500 0"
                  fill="none"
                  stroke="#9fdac8"
                  strokeWidth="3"
                />
              </svg>
            </div>
          </div>
          <small>Built by Vasudha Katal · Portfolio engineering project</small>
        </div>
        <div className="login-form">
          <span className="tag">LOCAL DEMONSTRATION</span>
          <h2>Welcome to your workspace</h2>
          <p>Sign in to explore the mock wealth platform.</p>
          <form onSubmit={login}>
            <label>
              Username
              <input
                name="username"
                defaultValue="demo"
                required
                autoComplete="username"
              />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                defaultValue="local-demo-only"
                required
                autoComplete="current-password"
              />
            </label>
            {error && (
              <div role="alert" className="error">
                {error}
              </div>
            )}
            <button disabled={busy}>
              {busy ? "Signing in…" : "Enter demo workspace"}{" "}
              <ArrowUpRight size={17} />
            </button>
          </form>
          <div className="disclaimer">
            <ShieldCheck size={20} />
            <p>
              Synthetic data only. No bank connections, real client records or
              financial transactions.
            </p>
          </div>
        </div>
      </div>
    );
  const allocation = portfolio
    ? ["Cash", "Shares", "Super"].map((name) => ({
        name,
        value: portfolio.holdings
          .filter((h) => h.category === name)
          .reduce((a, h) => a + h.value, 0),
      }))
    : [];
  return (
    <div className="shell">
      <aside>
        <div className="brand">
          <span className="brand-icon">
            <Layers size={23} />
          </span>{" "}
          WealthHub
        </div>
        <span className="nav-label">WORKSPACE</span>
        <nav>
          <button
            className={page === "overview" ? "active" : ""}
            onClick={() => {
              setPage("overview");
              setError("");
            }}
          >
            <LayoutDashboard size={19} />
            Overview
          </button>
          <button
            className={page === "clients" ? "active" : ""}
            onClick={() => {
              setPage("clients");
              setError("");
            }}
          >
            <Users size={19} />
            Client onboarding
          </button>
          <a href="/api/docs" target="_blank" rel="noreferrer">
            <Activity size={19} />
            API explorer <ArrowUpRight size={14} />
          </a>
        </nav>
        <div className="sidebar-bottom">
          <div className="safe">
            <ShieldCheck size={22} />
            <strong>Your local sandbox</strong>
            <p>
              Mock data. Real engineering.
              <br />
              No cloud resources running.
            </p>
          </div>
          <button
            className="logout"
            onClick={() => {
              setToken("");
              setPortfolio(null);
              setJobs([]);
              setError("");
            }}
          >
            <LogOut size={17} />
            Sign out
          </button>
        </div>
      </aside>
      <div className="workspace">
        <header>
          <span>
            Workspace <ChevronRight size={14} />{" "}
            {page === "overview" ? "Overview" : "Client onboarding"}
          </span>
          <div>
            <span className="local-dot" /> Local demo{" "}
            <span className="avatar">VK</span>
          </div>
        </header>
        <main>
          <div className="heading">
            <div>
              <span className="eyebrow">YOUR WEALTH, IN PERSPECTIVE</span>
              <h1>
                {page === "overview"
                  ? "Portfolio overview"
                  : "A better first impression"}
              </h1>
              <p>
                {page === "overview"
                  ? "A consolidated view across your connected mock accounts."
                  : "From a client profile to a welcome pack, in one simple flow."}
              </p>
            </div>
            {page === "overview" && (
              <button className="secondary" onClick={refresh}>
                Refresh portfolio <Activity size={16} />
              </button>
            )}
          </div>
          {error && (
            <div className="error" role="alert">
              {error}
            </div>
          )}
          {notice && (
            <div className="notice" role="status">
              {notice}
            </div>
          )}
          {page === "overview" ? (
            <>
              <div className="stats">
                <article className="stat primary">
                  <div>
                    Total portfolio value <Wallet size={20} />
                  </div>
                  <h2>
                    {portfolio ? money(portfolio.total) : "Loading…"}
                    <small>AUD</small>
                  </h2>
                  <span className="pill">Synthetic portfolio</span>
                  <p>Across bank, shares and super</p>
                </article>
                <article className="stat">
                  <div>
                    Sample six-month change
                    <ArrowUpRight size={20} />
                  </div>
                  <h2>
                    +13.49<small>%</small>
                  </h2>
                  <span className="positive">+$29,000</span>
                  <p>Illustrative history · not a forecast</p>
                </article>
                <article className="stat">
                  <div>
                    Connected sources
                    <Layers size={20} />
                  </div>
                  <h2>
                    {portfolio
                      ? Object.values(portfolio.sources).filter(
                          (s) => s === "connected",
                        ).length
                      : "–"}
                    <small>/ 3</small>
                  </h2>
                  <span className="positive">
                    {portfolio &&
                    Object.values(portfolio.sources).every(
                      (s) => s === "connected",
                    )
                      ? "All sources available"
                      : "Checking sources"}
                  </span>
                  <p>Independent timeout and retry handling</p>
                </article>
              </div>
              <div className="charts">
                <section className="card">
                  <div className="card-heading">
                    <div>
                      <h3>Portfolio performance</h3>
                      <p>An illustrative six-month journey</p>
                    </div>
                    <span className="tag">6 MONTHS</span>
                  </div>
                  <div className="chart">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart
                        data={performance}
                        margin={{ top: 20, right: 12, left: 0, bottom: 0 }}
                      >
                        <defs>
                          <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
                            <stop
                              offset="0%"
                              stopColor="#178f7c"
                              stopOpacity={0.22}
                            />
                            <stop
                              offset="100%"
                              stopColor="#178f7c"
                              stopOpacity={0}
                            />
                          </linearGradient>
                        </defs>
                        <XAxis
                          dataKey="month"
                          axisLine={false}
                          tickLine={false}
                          tick={{ fill: "#81918d", fontSize: 12 }}
                        />
                        <YAxis
                          domain={[200000, 250000]}
                          tickFormatter={(v) => `${v / 1000}k`}
                          axisLine={false}
                          tickLine={false}
                          width={45}
                          tick={{ fill: "#81918d", fontSize: 11 }}
                        />
                        <Tooltip formatter={(v) => money(v)} />
                        <Area
                          type="monotone"
                          dataKey="value"
                          stroke="#178f7c"
                          strokeWidth={3}
                          fill="url(#fill)"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </section>
                <section className="card">
                  <div className="card-heading">
                    <div>
                      <h3>Asset allocation</h3>
                      <p>Where your sample wealth sits</p>
                    </div>
                  </div>
                  <div className="donut">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={allocation}
                          dataKey="value"
                          innerRadius={65}
                          outerRadius={88}
                          paddingAngle={4}
                          stroke="none"
                        >
                          {allocation.map((a, i) => (
                            <Cell key={a.name} fill={colors[i]} />
                          ))}
                        </Pie>
                        <Tooltip formatter={(v) => money(v)} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="legend">
                    {allocation.map((a, i) => (
                      <div key={a.name}>
                        <span>
                          <i style={{ background: colors[i] }} />
                          {a.name}
                        </span>
                        <strong>
                          {portfolio.total
                            ? Math.round((a.value / portfolio.total) * 100)
                            : 0}
                          %
                        </strong>
                      </div>
                    ))}
                  </div>
                </section>
              </div>
              <section className="card">
                <div className="card-heading">
                  <div>
                    <h3>Your holdings</h3>
                    <p>Three synthetic sources, one consistent view</p>
                  </div>
                  <span className="tag">MOCK DATA</span>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Asset / account</th>
                        <th>Source</th>
                        <th>Asset class</th>
                        <th className="number">Value (AUD)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {portfolio?.holdings.map((h, i) => (
                        <tr key={h.name}>
                          <td>
                            <span
                              className="asset-icon"
                              style={{
                                background: ["#e4f2ed", "#f6efdf", "#e9edf7"][
                                  i % 3
                                ],
                              }}
                            >
                              <Wallet size={16} />
                            </span>
                            {h.name}
                          </td>
                          <td className="muted">Mock {h.source}</td>
                          <td>
                            <span className="category">{h.category}</span>
                          </td>
                          <td className="number">
                            <strong>{money(h.value)}</strong>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
              <div className="sources">
                {portfolio &&
                  Object.entries(portfolio.sources).map(([name, status]) => (
                    <span key={name}>
                      <i
                        className={
                          status === "connected" ? "online" : "offline"
                        }
                      />
                      Mock {name} · {status}
                    </span>
                  ))}
              </div>
            </>
          ) : (
            <>
              <div className="onboarding-grid">
                <section className="card">
                  <h3>Create a mock client</h3>
                  <p className="muted">
                    Use invented details, such as Taylor Demo and
                    taylor@example.com.
                  </p>
                  <form onSubmit={onboard}>
                    <label>
                      Client name
                      <input
                        name="name"
                        placeholder="Taylor Demo"
                        minLength={2}
                        maxLength={100}
                        required
                      />
                    </label>
                    <label>
                      Email address
                      <input
                        name="email"
                        type="email"
                        placeholder="taylor@example.com"
                        maxLength={254}
                        required
                      />
                    </label>
                    <RiskPicker />
                    <button disabled={busy}>
                      {busy ? "Creating…" : "Create client & welcome PDF"}
                      <ArrowUpRight size={17} />
                    </button>
                  </form>
                </section>
                <section className="flow-card">
                  <span className="tag">HOW IT WORKS</span>
                  <h2>
                    One request.
                    <br />A complete welcome.
                  </h2>
                  {[
                    [
                      "01",
                      "Capture the profile",
                      "The API validates the form and saves the client.",
                    ],
                    [
                      "02",
                      "Queue the work",
                      "PostgreSQL stores the onboarding job reliably.",
                    ],
                    [
                      "03",
                      "Prepare the welcome",
                      "The worker creates a PDF for authenticated download.",
                    ],
                  ].map(([n, t, d]) => (
                    <div className="step" key={n}>
                      <b>{n}</b>
                      <div>
                        <h4>{t}</h4>
                        <p>{d}</p>
                      </div>
                    </div>
                  ))}
                </section>
              </div>
              <section className="card">
                <div className="card-heading">
                  <div>
                    <h3>Recent onboarding jobs</h3>
                    <p>Updates automatically every four seconds</p>
                  </div>
                  <span className="tag">{jobs.length} JOBS</span>
                </div>
                {!jobs.length ? (
                  <div className="empty">
                    <Users size={30} />
                    <h3>Your first client starts here</h3>
                    <p>
                      Create a mock profile above to see the worker in action.
                    </p>
                  </div>
                ) : (
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Client</th>
                          <th>Risk profile</th>
                          <th>Status</th>
                          <th>Welcome pack</th>
                        </tr>
                      </thead>
                      <tbody>
                        {jobs.map((j) => (
                          <tr key={j.id}>
                            <td>{j.client}</td>
                            <td>{j.risk}</td>
                            <td>
                              <span className={"status " + j.status}>
                                {j.status}
                              </span>
                              {j.error && <small>{j.error}</small>}
                            </td>
                            <td>
                              {j.status === "completed" ? (
                                <button
                                  className="text-button"
                                  onClick={() => download(j.id)}
                                >
                                  <ArrowDownToLine size={16} />
                                  Download PDF
                                </button>
                              ) : (
                                "—"
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </>
          )}
          <footer>
            <span>WealthHub · Built by Vasudha Katal</span>
            <span>Demonstration only · No financial advice</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
function RiskPicker() {
  const [h, setH] = useState("2"),
    [t, setT] = useState("2");
  const score = Number(h) + Number(t);
  const risk = score <= 2 ? "Conservative" : score >= 6 ? "Growth" : "Balanced";
  return (
    <fieldset>
      <legend>Short risk questionnaire</legend>
      <label>
        Investment horizon
        <select value={h} onChange={(e) => setH(e.target.value)}>
          <option value="0">Under 3 years</option>
          <option value="2">3–7 years</option>
          <option value="4">Over 7 years</option>
        </select>
      </label>
      <label>
        How would a 10% fall feel?
        <select value={t} onChange={(e) => setT(e.target.value)}>
          <option value="0">I would prefer to reduce risk</option>
          <option value="2">I would hold my position</option>
          <option value="4">I could accept it for long-term growth</option>
        </select>
      </label>
      <input type="hidden" name="risk" value={risk} />
      <div className="risk-result">
        Illustrative profile <strong>{risk}</strong>
      </div>
      <small>
        This simplified questionnaire is a software demonstration, not a
        suitability assessment.
      </small>
    </fieldset>
  );
}
createRoot(document.getElementById("root")).render(<App />);
