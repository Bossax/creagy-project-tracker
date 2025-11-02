import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { api } from "./api.js";
import Layout from "./components/Layout.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import ProjectCreatePage from "./pages/ProjectCreatePage.jsx";
import ProjectDetailPage from "./pages/ProjectDetailPage.jsx";

const SessionContext = createContext({
  user: null,
  setUser: () => {},
  loading: true,
});

export function useSession() {
  return useContext(SessionContext);
}

function ProtectedRoute({ children }) {
  const { user, loading } = useSession();
  const location = useLocation();

  if (loading) {
    return (
      <div className="loader">
        <span className="spinner" /> Loading...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    api
      .getSession()
      .then((response) => {
        if (isMounted) {
          setUser(response.user ?? null);
        }
      })
      .finally(() => {
        if (isMounted) {
          setLoading(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const value = useMemo(() => ({ user, setUser, loading }), [user, loading]);

  return (
    <SessionContext.Provider value={value}>
      <Routes>
        <Route
          path="/login"
          element={
            <LoginPage
              onLogin={(nextUser) => {
                setUser(nextUser);
              }}
            />
          }
        />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="projects/new" element={<ProjectCreatePage />} />
          <Route path="projects/:projectId" element={<ProjectDetailPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </SessionContext.Provider>
  );
}
