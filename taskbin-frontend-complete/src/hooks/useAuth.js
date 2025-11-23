import { useEffect, useState } from "react";
import { jwtDecode } from "jwt-decode";

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);  // Add this

  useEffect(() => {
    // Parse Cognito redirect URL
    const hash = window.location.hash;

    if (hash.includes("id_token")) {
      const params = new URLSearchParams(hash.substring(1));
      const idToken = params.get("id_token");

      if (idToken) {
        localStorage.setItem("id_token", idToken);
        window.location.hash = "";
      }
    }

    // Load token from storage
    const token = localStorage.getItem("id_token");

    if (!token) {
      setUser(null);
      setLoading(false);  // Done loading, no user
      return;
    }

    // Decode JWT
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

    setLoading(false);  // Done loading
  }, []);

  return {
    user,
    loading,  // Expose it
    signIn: () => {},
    signUp: () => {},
    signOut: () => {
      localStorage.removeItem("id_token");
      setUser(null);
      window.location.href = "/";
    },
  };
}