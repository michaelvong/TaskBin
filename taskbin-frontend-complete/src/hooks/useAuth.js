import { useEffect, useState } from "react";
import { jwtDecode } from "jwt-decode";

export function useAuth() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    // -------------------------------
    // 1. Parse Cognito redirect URL
    // -------------------------------
    const hash = window.location.hash;

    if (hash.includes("id_token")) {
      const params = new URLSearchParams(hash.substring(1));
      const idToken = params.get("id_token");

      if (idToken) {
        localStorage.setItem("id_token", idToken);
        window.location.hash = ""; // cleanup the URL
      }
    }

    // -------------------------------
    // 2. Load token from storage
    // -------------------------------
    const token = localStorage.getItem("id_token");

    if (!token) {
      setUser(null);
      return;
    }

    // -------------------------------
    // 3. Decode JWT → user info
    // -------------------------------
    try {
      const decoded = jwtDecode(token);

      setUser({
        email: decoded.email,
        name: decoded.name || decoded.email,
        token,
      });
    } catch (err) {
      console.error("JWT decode failed:", err);
      localStorage.removeItem("id_token");
      setUser(null);
    }
  }, []);

  // -------------------------------
  // 4. Auth API exposed to components
  // -------------------------------
  return {
    user,
    signIn: () => {
      // Not used — Login.jsx handles redirect
    },
    signUp: () => {},
    signOut: () => {
      localStorage.removeItem("id_token");
      setUser(null);
      window.location.href = "/"; // go back to login
    },
  };
}
