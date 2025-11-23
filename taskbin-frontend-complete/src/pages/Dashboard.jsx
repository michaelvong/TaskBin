import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import { useAuth } from "../hooks/useAuth";

export default function Dashboard() {
  //const api = useApi();
  const { user, loading, signOut } = useAuth();   // ⬅️ MUST expose `loading`
  const api = useApi(user?.email);  // Pass email directly
  const [boards, setBoards] = useState([]);
  const [newBoardName, setNewBoardName] = useState("");
  const [newBoardDescription, setNewBoardDescription] = useState("");

  // --------------------------
  // Load boards AFTER user loads
  // --------------------------
  useEffect(() => {
    // Cognito still loading user → do nothing
    if (loading) return;

    // No authenticated user → do nothing
    if (!user?.email) {
      return;
    }


    api.listBoards()
      .then(setBoards)
      .catch((err) => console.error("ListBoards failed:", err));
  }, [loading, user?.email]);  // ⬅️ KEY: wait for loading to finish

  async function handleCreateBoard(e) {
    e.preventDefault();
    if (!newBoardName.trim()) return;

    await api.createBoard({
      name: newBoardName.trim(),
      description: newBoardDescription.trim(),
    });

    setNewBoardName("");
    setNewBoardDescription("");

    const refreshed = await api.listBoards();
    setBoards(refreshed);
  }

  return (
    <div className="max-w-4xl mx-auto p-4 space-y-6">

      {/* HEADER */}
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Your Boards</h1>
          <p className="text-sm text-gray-500">Logged in as {user?.email}</p>
        </div>

        <button
          onClick={signOut}
          className="px-4 py-2 text-sm font-semibold bg-red-500 text-white rounded-lg shadow hover:bg-red-600"
        >
          Sign Out
        </button>
      </header>

      {/* CREATE BOARD */}
      <section className="bg-white p-4 rounded-xl shadow space-y-3">
        <h2 className="text-lg font-semibold">Create a new board</h2>

        <form
          onSubmit={handleCreateBoard}
          className="grid grid-cols-1 md:grid-cols-3 gap-3"
        >
          <input
            className="border p-2 rounded"
            placeholder="Board name"
            value={newBoardName}
            onChange={(e) => setNewBoardName(e.target.value)}
          />

          <input
            className="border p-2 rounded"
            placeholder="Description (optional)"
            value={newBoardDescription}
            onChange={(e) => setNewBoardDescription(e.target.value)}
          />

          <button
            type="submit"
            className="px-3 py-2 bg-gray-900 text-white rounded-lg"
          >
            Create
          </button>
        </form>
      </section>

      {/* BOARDS */}
      <section>
        {boards.length === 0 ? (
          <p className="text-sm text-gray-500">No boards yet.</p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            {boards.map((b) => (
              <Link
                key={b.id}
                to={`/boards/${b.id}`}
                className="block bg-white p-4 rounded-xl shadow hover:bg-gray-50"
              >
                <h3 className="font-semibold">{b.name}</h3>
                {b.description && (
                  <p className="text-xs text-gray-500 mt-1">{b.description}</p>
                )}
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
