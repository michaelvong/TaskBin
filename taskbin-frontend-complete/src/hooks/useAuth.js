import { useState } from "react";

export function useAuth() {
  // Simple mock auth: always logged in as test user
  const [user, setUser] = useState({ username: "mockuser@example.com" });

  return {
    user,
    signIn: async () => {},         // no-op for now
    signUp: async () => {},         // no-op
    signOut: async () => setUser(null),
  };
}
