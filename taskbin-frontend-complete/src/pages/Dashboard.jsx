import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useApi } from "../hooks/useApi";

export default function Dashboard() {
  const api = useApi();

  const [boards, setBoards] = useState([]);
  const [loading, setLoading] = useState(true);

  const [newBoardName, setNewBoardName] = useState("");
  const [newBoardDescription, setNewBoardDescription] = useState("");

  // -----------------------------
  // Load boards (AWS or MOCK)
  // -----------------------------
  async function loadBoards() {
    try {
      const result = await api.listBoards();

      // Normalize shape: AWS returns { boards: [...] }
      const arr = Array.isArray(result)
        ? result
        : (result?.boards || []);

      setBoards(arr);
    } catch (err) {
      console.error("Failed to load boards:", err);
      setBoards([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadBoards();
  }, []);

  useEffect(() => {
    if (window.location.hash.includes("id_token")) {
      const params = new URLSearchParams(window.location.hash.substring(1));
      const idToken = params.get("id_token");

      console.log("🔥 Cognito Token:", idToken);

      localStorage.setItem("idToken", idToken);
      
      // Remove token fragment from URL
      window.location.hash = "";
    }
  }, []);


  // -----------------------------
  // Create Board
  // -----------------------------
  async function createBoard(e) {
    e.preventDefault();
    if (!newBoardName.trim()) return;

    try {
      console.log("DEBUG: Sending createBoard body:", {
        user_id: "testuser@example.com",
        name: newBoardName,
        description: newBoardDescription,
      });

      await api.createBoard({
        user_id: "testuser@example.com",  // hardcoded for now
        name: newBoardName,
        description: newBoardDescription,
      });


      await loadBoards();
      setNewBoardName("");
      setNewBoardDescription("");
    } catch (err) {
      console.error("Failed to create board:", err);
    }
  }

  return (
    <div className="max-w-5xl mx-auto p-4 space-y-6">
      <h1 className="text-2xl font-bold">Your Boards</h1>

      {/* Create Board */}
      <section className="bg-white shadow rounded-xl p-4 space-y-3">
        <h2 className="font-semibold text-lg">Create a Board</h2>

        <form onSubmit={createBoard} className="space-y-3">
          <input
            className="w-full border rounded-lg px-3 py-2 text-sm"
            placeholder="Board name"
            value={newBoardName}
            onChange={(e) => setNewBoardName(e.target.value)}
          />

          <textarea
            className="w-full border rounded-lg px-3 py-2 text-sm"
            placeholder="Description (optional)"
            value={newBoardDescription}
            onChange={(e) => setNewBoardDescription(e.target.value)}
          />

          <button className="px-4 py-2 bg-gray-900 text-white rounded-lg text-sm">
            Create
          </button>
        </form>
      </section>

      {/* Boards */}
      <section>
        {loading ? (
          <div className="text-sm text-gray-500">Loading…</div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {boards.map((b) => (
              <Link
                key={b.id}
                to={`/boards/${b.id}`}
                state={{ board: b }}
                className="block p-4 border rounded-xl bg-white shadow hover:shadow-md transition"
              >
                <div className="font-semibold text-sm">{b.name}</div>
                {b.description && (
                  <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                    {b.description}
                  </p>
                )}
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
