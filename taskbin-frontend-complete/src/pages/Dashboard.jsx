import { useApi } from "../hooks/useApi";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

export default function Dashboard() {
  const api = useApi();
  const [boards, setBoards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newBoardName, setNewBoardName] = useState("");

  useEffect(() => {
    api
      .listBoards()
      .then(setBoards)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  async function handleCreateBoard(e) {
    e.preventDefault();
    if (!newBoardName.trim()) return;
    try {
      const created = await api.createBoard(newBoardName.trim());
      setBoards((prev) => [...prev, created]);
      setNewBoardName("");
    } catch (err) {
      console.error("Failed to create board:", err);
    }
  }

  return (
    <div className="p-6">
      <h1 className="font-bold text-2xl mb-4">Your Boards</h1>

      <form className="flex gap-2 mb-4" onSubmit={handleCreateBoard}>
        <input
          className="border rounded px-3 py-2 flex-1"
          placeholder="New board name"
          value={newBoardName}
          onChange={(e) => setNewBoardName(e.target.value)}
        />
        <button className="bg-blue-600 text-white px-4 py-2 rounded">
          Create
        </button>
      </form>

      {loading ? (
        <p>Loading boards...</p>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          {boards.map((b) => (
            <Link
              key={b.id}
              to={`/board/${b.id}`}
              state={{ board: b }}
              className="p-4 bg-white rounded shadow hover:shadow-md transition"
            >
              <div className="font-semibold">{b.name}</div>
              {b.description && (
                <div className="text-xs text-gray-500 mt-1">
                  {b.description}
                </div>
              )}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
