import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";

const API_BASE = "http://127.0.0.1:8000/api";
const WS_BASE = "ws://127.0.0.1:8000/ws/updates/";

type Role = "USER" | "BUNK";
type Fuel = "PETROL" | "DIESEL";

type AuthPayload = {
  token: string;
  user: {
    id: number;
    username: string;
    email: string;
    profile: {
      role: Role;
      phone: string;
      bunk_name: string;
      is_available: boolean;
    };
  };
};

type FuelRequest = {
  id: number;
  customer_name: string;
  bunk_name: string | null;
  fuel_type: Fuel;
  quantity_liters: string;
  latitude: number;
  longitude: number;
  location_note: string;
  status: "PENDING" | "ACCEPTED" | "COMPLETED" | "CANCELLED";
  service_fee: string;
  payment_status: "UNPAID" | "PAID";
  payment_reference: string;
  distance_km?: number;
  created_at: string;
};

async function callApi<T>(path: string, method = "GET", body?: object, token?: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Token ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Request failed." }));
    throw new Error(JSON.stringify(payload));
  }
  return (await response.json()) as T;
}

export default function App() {
  const [auth, setAuth] = useState<AuthPayload | null>(null);
  const [isRegister, setIsRegister] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [requests, setRequests] = useState<FuelRequest[]>([]);

  const [authForm, setAuthForm] = useState({
    username: "",
    password: "",
    email: "",
    phone: "",
    bunk_name: "",
    role: "USER" as Role,
    latitude: "",
    longitude: "",
  });

  const [fuelForm, setFuelForm] = useState({
    fuel_type: "PETROL" as Fuel,
    quantity_liters: "2",
    latitude: "",
    longitude: "",
    location_note: "",
  });

  const role = auth?.user.profile.role;

  useEffect(() => {
    const token = localStorage.getItem("fuelassist_token");
    if (!token) {
      return;
    }
    callApi<AuthPayload["user"]>("/auth/me/", "GET", undefined, token)
      .then((user) => setAuth({ token, user }))
      .catch(() => localStorage.removeItem("fuelassist_token"));
  }, []);

  useEffect(() => {
    if (!auth) {
      return;
    }
    const load = () => callApi<FuelRequest[]>("/requests/", "GET", undefined, auth.token).then(setRequests).catch(() => null);
    load();
    const socket = new WebSocket(WS_BASE);
    socket.onmessage = () => {
      load();
    };
    const timer = setInterval(load, 15000);
    return () => {
      clearInterval(timer);
      socket.close();
    };
  }, [auth]);

  const pendingCount = useMemo(() => requests.filter((r) => r.status === "PENDING").length, [requests]);

  const submitAuth = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const payload = await callApi<AuthPayload>(
        isRegister ? "/auth/register/" : "/auth/login/",
        "POST",
        authForm
      );
      localStorage.setItem("fuelassist_token", payload.token);
      setAuth(payload);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  const useMyLocation = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition((position) => {
      setFuelForm((prev) => ({
        ...prev,
        latitude: String(position.coords.latitude),
        longitude: String(position.coords.longitude),
      }));
    });
  };

  const createRequest = async (e: FormEvent) => {
    e.preventDefault();
    if (!auth) return;
    setLoading(true);
    setError("");
    try {
      await callApi("/requests/", "POST", fuelForm, auth.token);
      const fresh = await callApi<FuelRequest[]>("/requests/", "GET", undefined, auth.token);
      setRequests(fresh);
      setFuelForm({
        fuel_type: "PETROL",
        quantity_liters: "2",
        latitude: "",
        longitude: "",
        location_note: "",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create request.");
    } finally {
      setLoading(false);
    }
  };

  const updateRequest = async (id: number, action: "accept" | "complete") => {
    if (!auth) return;
    setLoading(true);
    setError("");
    try {
      await callApi(`/requests/${id}/${action}/`, "POST", action === "complete" ? { service_fee: "40.00" } : {}, auth.token);
      const fresh = await callApi<FuelRequest[]>("/requests/", "GET", undefined, auth.token);
      setRequests(fresh);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed.");
    } finally {
      setLoading(false);
    }
  };

  const payRequest = async (id: number) => {
    if (!auth) return;
    setLoading(true);
    setError("");
    try {
      await callApi(`/requests/${id}/pay/`, "POST", {}, auth.token);
      const fresh = await callApi<FuelRequest[]>("/requests/", "GET", undefined, auth.token);
      setRequests(fresh);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Payment failed.");
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("fuelassist_token");
    setAuth(null);
    setRequests([]);
  };

  return (
    <div className="page">
      <header className="hero">
        <h1>FuelAssist</h1>
        <p>Emergency on-road fuel delivery for bike and car travelers.</p>
      </header>

      {!auth ? (
        <section className="card auth-card">
          <h2>{isRegister ? "Create account" : "Welcome back"}</h2>
          <form onSubmit={submitAuth} className="grid">
            <input placeholder="Username" value={authForm.username} onChange={(e) => setAuthForm({ ...authForm, username: e.target.value })} required />
            <input placeholder="Password" type="password" value={authForm.password} onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })} required />
            {isRegister && (
              <>
                <input placeholder="Email (optional)" value={authForm.email} onChange={(e) => setAuthForm({ ...authForm, email: e.target.value })} />
                <input placeholder="Phone number" value={authForm.phone} onChange={(e) => setAuthForm({ ...authForm, phone: e.target.value })} />
                <select value={authForm.role} onChange={(e) => setAuthForm({ ...authForm, role: e.target.value as Role })}>
                  <option value="USER">Traveler</option>
                  <option value="BUNK">Petrol Bunk</option>
                </select>
                {authForm.role === "BUNK" && (
                  <>
                    <input placeholder="Petrol bunk name" value={authForm.bunk_name} onChange={(e) => setAuthForm({ ...authForm, bunk_name: e.target.value })} required />
                    <div className="split">
                      <input placeholder="Bunk latitude" value={authForm.latitude} onChange={(e) => setAuthForm({ ...authForm, latitude: e.target.value })} />
                      <input placeholder="Bunk longitude" value={authForm.longitude} onChange={(e) => setAuthForm({ ...authForm, longitude: e.target.value })} />
                    </div>
                  </>
                )}
              </>
            )}
            <button type="submit" disabled={loading}>{loading ? "Please wait..." : isRegister ? "Register" : "Login"}</button>
          </form>
          <button className="link-btn" onClick={() => setIsRegister((v) => !v)}>
            {isRegister ? "Already have an account? Login" : "New here? Register"}
          </button>
        </section>
      ) : (
        <main className="layout">
          <section className="card">
            <div className="card-head">
              <h2>Hi, {auth.user.username}</h2>
              <span className="badge">{role === "USER" ? "Traveler" : "Petrol Bunk"}</span>
            </div>
            <p>
              {role === "USER"
                ? "Share your live coordinates and request fuel instantly."
                : "Monitor nearby emergency requests and dispatch fuel quickly."}
            </p>
            <button onClick={logout} className="secondary">Logout</button>
          </section>

          {role === "USER" && (
            <section className="card">
              <h3>Create Fuel Request</h3>
              <form onSubmit={createRequest} className="grid">
                <select value={fuelForm.fuel_type} onChange={(e) => setFuelForm({ ...fuelForm, fuel_type: e.target.value as Fuel })}>
                  <option value="PETROL">Petrol</option>
                  <option value="DIESEL">Diesel</option>
                </select>
                <input type="number" min="1" step="0.5" value={fuelForm.quantity_liters} onChange={(e) => setFuelForm({ ...fuelForm, quantity_liters: e.target.value })} required />
                <div className="split">
                  <input placeholder="Latitude" value={fuelForm.latitude} onChange={(e) => setFuelForm({ ...fuelForm, latitude: e.target.value })} required />
                  <input placeholder="Longitude" value={fuelForm.longitude} onChange={(e) => setFuelForm({ ...fuelForm, longitude: e.target.value })} required />
                </div>
                <button type="button" onClick={useMyLocation} className="secondary">Use My Location</button>
                <input placeholder="Landmark / road details" value={fuelForm.location_note} onChange={(e) => setFuelForm({ ...fuelForm, location_note: e.target.value })} />
                <button type="submit" disabled={loading}>{loading ? "Requesting..." : "Request Fuel Delivery"}</button>
              </form>
            </section>
          )}

          <section className="card">
            <div className="card-head">
              <h3>{role === "USER" ? "My Requests" : "Incoming Requests"}</h3>
              {role === "BUNK" && <span className="badge alert">{pendingCount} pending</span>}
            </div>
            <div className="request-list">
              {requests.length === 0 && <p>No requests yet.</p>}
              {requests.map((item) => (
                <article key={item.id} className="request-item">
                  <div>
                    <strong>{item.fuel_type}</strong> - {item.quantity_liters}L
                    <p>{item.location_note || "No landmark provided."}</p>
                    <small>
                      Location: {item.latitude}, {item.longitude}
                    </small>
                    <div>
                      <a
                        href={`https://www.openstreetmap.org/?mlat=${item.latitude}&mlon=${item.longitude}#map=15/${item.latitude}/${item.longitude}`}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Open in Map
                      </a>
                    </div>
                  </div>
                  <div className="actions">
                    <span className={`status ${item.status.toLowerCase()}`}>{item.status}</span>
                    {typeof item.distance_km === "number" && <small>{item.distance_km} km away</small>}
                    {role === "BUNK" && item.status === "PENDING" && (
                      <button onClick={() => updateRequest(item.id, "accept")}>Accept</button>
                    )}
                    {role === "BUNK" && item.status === "ACCEPTED" && (
                      <button onClick={() => updateRequest(item.id, "complete")}>Mark Completed</button>
                    )}
                    {role === "USER" && item.status === "COMPLETED" && item.payment_status !== "PAID" && (
                      <button onClick={() => payRequest(item.id)}>Pay Now</button>
                    )}
                    {item.payment_status === "PAID" && <small>Paid ({item.payment_reference})</small>}
                    {item.bunk_name && <small>Handled by: {item.bunk_name}</small>}
                  </div>
                </article>
              ))}
            </div>
          </section>
        </main>
      )}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
