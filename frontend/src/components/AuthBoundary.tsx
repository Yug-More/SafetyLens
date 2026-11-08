"use client";
import {
  createContext,
  useContext,
  FormEvent,
  ReactNode,
  useCallback,
  useEffect,
  useState,
} from "react";
import {
  apiGetItem,
  apiPostJson,
  getApiBaseUrl,
  setCsrfToken,
} from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type Session = {
  username: string;
  role: string;
  mode: string;
  csrf_token: string;
};

const SessionContext = createContext<Session | null>(null);
export function useSession() {
  return useContext(SessionContext);
}

function LiveConnection() {
  const [status, setStatus] = useState("Connecting to event stream");
  useEffect(() => {
    const events = new EventSource(`${getApiBaseUrl()}/api/events`, {
      withCredentials: true,
    });
    let lastId = 0;
    let timer: ReturnType<typeof setTimeout>;
    events.onopen = () => setStatus("Event stream connected");
    events.onerror = () => setStatus("Reconnecting · automatic recovery");
    events.addEventListener("resync_required", () =>
      window.dispatchEvent(new Event("platform-update")),
    );
    events.addEventListener("session_expired", () =>
      window.dispatchEvent(new Event("session-expired")),
    );
    events.addEventListener("update", (message) => {
      const event = message as MessageEvent;
      const id = Number(event.lastEventId);
      if (id <= lastId) return;
      lastId = id;
      clearTimeout(timer);
      timer = setTimeout(
        () => window.dispatchEvent(new Event("platform-update")),
        200,
      );
    });
    return () => {
      clearTimeout(timer);
      events.close();
    };
  }, []);
  return (
    <span role="status" className="text-xs text-muted-foreground">
      {status}
    </span>
  );
}

export function AuthBoundary({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const accept = useCallback((value: Session) => {
    setCsrfToken(value.csrf_token);
    setSession(value);
  }, []);
  useEffect(() => {
    let cancelled = false;
    apiGetItem<Session>("/api/auth/me")
      .then((value) => {
        if (!cancelled) accept(value);
      })
      .catch(() => undefined)
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    const expire = () => {
      setSession(null);
      setCsrfToken("");
    };
    window.addEventListener("session-expired", expire);
    return () => {
      cancelled = true;
      window.removeEventListener("session-expired", expire);
    };
  }, [accept]);
  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      accept(
        await apiPostJson<Session>("/api/auth/login", {
          username: form.get("username"),
          password: form.get("password"),
        }),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed");
    } finally {
      setBusy(false);
    }
  }
  async function logout() {
    try {
      await apiPostJson("/api/auth/logout");
      setSession(null);
      setCsrfToken("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Logout failed");
    }
  }
  if (loading)
    return (
      <main className="grid min-h-screen place-items-center" aria-busy="true">
        Checking your session…
      </main>
    );
  if (!session)
    return (
      <main className="grid min-h-screen place-items-center px-5">
        <section className="w-full max-w-md rounded-2xl border border-border bg-panel p-8 shadow-lg">
          <p className="text-xs uppercase tracking-[.2em] text-blue-400">
            SafetyLens / Operations
          </p>
          <h1 className="mt-4 text-3xl font-semibold">Welcome back.</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Sign in to review evidence and coordinate a supervised response.
          </p>
          <form onSubmit={login} className="mt-7 space-y-5">
            <label className="block text-sm">
              Username
              <Input
                className="mt-2"
                name="username"
                autoComplete="username"
                required
                maxLength={120}
              />
            </label>
            <label className="block text-sm">
              Password
              <Input
                className="mt-2"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                maxLength={1024}
              />
            </label>
            {error && (
              <p role="alert" className="text-sm text-red-300">
                {error}
              </p>
            )}
            <Button type="submit" className="w-full" disabled={busy}>
              {busy ? "Signing in…" : "Sign in"}
            </Button>
          </form>
          <p className="mt-6 text-xs text-muted-foreground">
            Access is managed by your installation administrator. SafetyLens
            supports decision-making and does not replace trained safety
            personnel.
          </p>
        </section>
      </main>
    );
  return (
    <SessionContext.Provider value={session}>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-panel px-5 py-2 text-xs">
        <div>
          <span className="font-medium">{session.username}</span>
          <span className="ml-2 text-muted-foreground">
            {session.role.replaceAll("_", " ")}
          </span>
          {session.mode === "demo" && (
            <span className="ml-3 text-amber-300">
              UNAUTHENTICATED LOCAL DEMO
            </span>
          )}
        </div>
        <LiveConnection />
        {session.mode !== "demo" && (
          <button
            onClick={() => void logout()}
            className="rounded px-3 py-1 hover:bg-secondary"
          >
            Sign out
          </button>
        )}
      </div>
      {error && <p role="alert">{error}</p>}
      {children}
    </SessionContext.Provider>
  );
}
