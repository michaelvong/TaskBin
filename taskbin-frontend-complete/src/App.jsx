// src/App.jsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useAuth } from "./hooks/useAuth";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Board from "./pages/Board";
import NotFound from "./pages/NotFound";

export default function App() {
  const { user } = useAuth();

  // -------------------------------
  // If NOT logged in → show Login page
  // -------------------------------
  if (!user) {
    return <Login />;
  }

  // -------------------------------
  // Logged in → show full app
  // -------------------------------
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/boards/:id" element={<Board />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
