import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Button, Card, Input } from "../components/ui";
import { DisclaimerBanner } from "../components/layout";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { errorMessage } from "../lib/format";

export default function LoginPage() {
  const { user, login } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function onSubmit(e) {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email.trim(), password);
      navigate("/", { replace: true });
    } catch (err) {
      toast.error(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-[linear-gradient(160deg,#0f2744,#143a5c_45%,#115e59)]">
      <DisclaimerBanner />
      <div className="mx-auto grid min-h-[calc(100vh-2.25rem)] max-w-6xl items-center gap-10 px-4 py-10 lg:grid-cols-2">
        <div className="text-white">
          <p className="text-xs uppercase tracking-[0.25em] text-teal-200">Government of India · SIH 26016</p>
          <h1 className="mt-3 font-serif text-4xl leading-tight md:text-5xl">National Land Acquisition Command Center</h1>
          <p className="mt-4 max-w-lg text-sm text-slate-200">
            A demonstration workspace for proposal approval, acquisition workflow, compensation, R&amp;R, and field
            verification. Operational data in this prototype is synthetic.
          </p>
        </div>
        <Card className="mx-auto w-full max-w-md">
          <h2 className="font-serif text-2xl text-ink">Sign in</h2>
          <p className="mt-1 text-sm text-slate-600">Use a demo directory account. Credentials are not stored in the app.</p>
          <form className="mt-5 space-y-3" onSubmit={onSubmit}>
            <Input label="Official email" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required />
            <Input label="Password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            <Button type="submit" className="w-full" loading={loading}>
              Continue
            </Button>
          </form>
          <div className="mt-5 rounded-xl bg-sand p-3 text-xs text-slate-600">
            <p className="font-semibold text-ink">Demo directory (password not shown)</p>
            <ul className="mt-1 space-y-0.5">
              <li>admin@demo.local — ADMIN</li>
              <li>officer@demo.local — ACQUISITION OFFICER (Telangana)</li>
              <li>approver@demo.local — APPROVING AUTHORITY</li>
              <li>field@demo.local — FIELD OFFICER</li>
            </ul>
          </div>
        </Card>
      </div>
    </div>
  );
}
