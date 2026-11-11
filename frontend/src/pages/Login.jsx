import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldCheck, LogIn, Lock } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import ErrorAlert from "../components/common/ErrorAlert";
import "./Login.css";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const { signIn, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  // Redirect if already authenticated
  React.useEffect(() => {
    if (isAuthenticated) {
      navigate("/", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setErrorMsg("Please enter both email address and password.");
      return;
    }

    setSubmitting(true);
    setErrorMsg(null);

    try {
      await signIn(email, password);
      navigate("/", { replace: true });
    } catch (err) {
      setErrorMsg(err.message || "Invalid credentials or authentication failure. Please check your email and password.");
    } finally {
      setSubmitting(false);
    }
  };

  const fillDemoAccount = (demoEmail) => {
    setEmail(demoEmail);
    setPassword("password123");
    setErrorMsg(null);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="login-icon-box">
            <ShieldCheck size={32} />
          </div>
          <h1 className="login-title">Institutional Decision Platform</h1>
          <p className="login-subtitle">Sign in to access platform analytics and decision tools</p>
        </div>

        {errorMsg && (
          <div style={{ marginBottom: "1.25rem" }}>
            <ErrorAlert message={errorMsg} />
          </div>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          <div className="login-field">
            <label htmlFor="email">Email Address</label>
            <input
              id="email"
              type="email"
              placeholder="e.g. admin@institution.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={submitting}
              required
            />
          </div>

          <div className="login-field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={submitting}
              required
            />
          </div>

          <button type="submit" className="login-btn" disabled={submitting}>
            {submitting ? (
              <>Authenticating...</>
            ) : (
              <>
                <LogIn size={18} /> Sign In
              </>
            )}
          </button>
        </form>

        <div className="login-demo-section">
          <div className="login-demo-title">Quick Demo Logins (Role Testing)</div>
          <div className="login-demo-grid">
            <button
              type="button"
              className="login-demo-btn"
              onClick={() => fillDemoAccount("admin@institution.edu")}
            >
              👑 Administrator<br />
              <span style={{ fontSize: "0.7rem", color: "#64748b" }}>All Access</span>
            </button>

            <button
              type="button"
              className="login-demo-btn"
              onClick={() => fillDemoAccount("hod.cse@institution.edu")}
            >
              🏫 CSE HOD<br />
              <span style={{ fontSize: "0.7rem", color: "#64748b" }}>Computer Science</span>
            </button>

            <button
              type="button"
              className="login-demo-btn"
              onClick={() => fillDemoAccount("hod.ece@institution.edu")}
            >
              🏫 ECE HOD<br />
              <span style={{ fontSize: "0.7rem", color: "#64748b" }}>Electronics Eng</span>
            </button>

            <button
              type="button"
              className="login-demo-btn"
              onClick={() => fillDemoAccount("hod.aiml@institution.edu")}
            >
              🏫 AIML HOD<br />
              <span style={{ fontSize: "0.7rem", color: "#64748b" }}>AI & Machine Learning</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
