import { useApi } from "../hooks/useApi";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

export default function Dashboard() {
  const api = useApi();

  const [boards, setBoards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const [newBoardName, setNewBoardName] = useState("");
  const [newBoardDescription, setNewBoardDescription] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function loadBoards() {
      try {
        const data = await api.listBoards();
        if (!cancelled) {
          setBoards(data);
        }
      } catch (err) {
        console.error("Failed to load boards:", err);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    loadBoards();

    return () => {
      cancelled = true;
    };
  }, [api]);

  async function handleCreateBoard(e) {
    e.preventDefault();
    const name = newBoardName.trim();
    if (!name) return;

    setCreating(true);
    try {
      const board = await api.createBoard(name, newBoardDescription.trim());
      // Optimistically add new board to top of list
      setBoards((prev) => [board, ...prev]);
      setNewBoardName("");
      setNewBoardDescription("");
    } catch (err) {
      console.error("Failed to create board:", err);
      // Optional: show toast / inline error
    } finally {
      setCreating(false);
    }
  }

  function formatJoinedAt(joinedAt) {
    if (!joinedAt) return null;
    const d = new Date(joinedAt);
    if (Number.isNaN(d.getTime())) return null;
    return d.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  return (
    <div className="max-w-5xl mx-auto p-4 space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Your boards</h1>
      </header>

      {/* Create board form */}
      <section className="bg-white rounded-xl shadow p-4 space-y-3">
        <h2 className="text-lg font-semibold">Create a new board</h2>
        <form
          onSubmit={handleCreateBoard}
          className="space-y-3"
        >
          <div>
            <label className="block text-sm font-medium mb-1">
              Board name
            </label>
            <input
              type="text"
              className="w-full border rounded-lg px-3 py-2 text-sm"
              placeholder="e.g. TaskBin roadmap"
              value={newBoardName}
              onChange={(e) => setNewBoardName(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">
              Description <span className="text-gray-400">(optional)</span>
            </label>
            <textarea
              className="w-full border rounded-lg px-3 py-2 text-sm min-h-[60px]"
              placeholder="Short description of what this board is for"
              value={newBoardDescription}
              onChange={(e) => setNewBoardDescription(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={creating || !newBoardName.trim()}
            className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-semibold border bg-gray-900 text-white disabled:opacity-60"
          >
            {creating ? "Creating…" : "Create board"}
          </button>
        </form>
      </section>

      {/* Boards list */}
      <section>
        {loading ? (
          <div className="text-sm text-gray-500">Loading boards…</div>
        ) : boards.length === 0 ? (
          <div className="text-sm text-gray-500">
            You don&apos;t have any boards yet. Create one above to get
            started.
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {boards.map((b) => {
              const joined = formatJoinedAt(b.joinedAt);
              return (
                <Link
                  key={b.id}
                  to={`/boards/${b.id}`}
                  state={{ board: b }}
                  className="block rounded-xl border bg-white p-4 hover:shadow-sm transition-shadow"
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="font-semibold text-sm line-clamp-1">
                      {b.name}
                    </div>
                    {b.role && (
                      <span className="text-[11px] px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
                        {b.role === "owner" ? "Owner" : "Member"}
                      </span>
                    )}
                  </div>

                  {b.description && (
                    <p className="text-xs text-gray-600 line-clamp-2 mb-2">
                      {b.description}
                    </p>
                  )}

                  {joined && (
                    <div className="text-[11px] text-gray-400">
                      Joined · {joined}
                    </div>
                  )}
                </Link>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
