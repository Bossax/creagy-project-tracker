import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { api } from "../api.js";
import { useSession } from "../App.jsx";

export default function Layout() {
  const { user, setUser } = useSession();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await api.logout();
    } finally {
      setUser(null);
      navigate("/login");
    }
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <NavLink to="/">Creagy Tracker</NavLink>
        </div>
        <nav className="nav-links">
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/projects/new">New Project</NavLink>
        </nav>
        <div className="user-actions">
          {user ? <span className="user-name">{user.name}</span> : null}
          <button type="button" onClick={handleLogout} className="btn-secondary">
            Logout
          </button>
        </div>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
