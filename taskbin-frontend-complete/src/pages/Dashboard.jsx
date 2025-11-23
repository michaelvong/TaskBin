import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useApi } from "../hooks/useApi";
import { useAuth } from "../hooks/useAuth";

export default function Dashboard() {
  const { user, loading, signOut } = useAuth();   
  const api = useApi(user?.email);

  const [boards, setBoards] = useState([]);
  const [newBoardName, setNewBoardName] = useState("");
  const [newBoardDescription, setNewBoardDescription] = useState("");

  // Join board modal state
  const [showJoinModal, setShowJoinModal] = useState(false);
  const [joinCode, setJoinCode] = useState("");

  // --------------------------
  // Load boards AFTER user loads
  // --------------------------
  useEffect(() => {
    if (loading) return;
    if (!user?.email) return;

    api.listBoards()
      .then(setBoards)
      .catch((err) => console.error("ListBoards failed:", err));
  }, [loading, user?.email]);

  // --------------------------
  // CREATE BOARD
  // --------------------------
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
    toast.success("Board created!");
  }

  // --------------------------
  // JOIN BOARD VIA CODE
  // --------------------------
  async function handleJoinBoard() {
    const code = joinCode.trim();

    if (!code) {
      // alert("Enter an access code.");
      toast("Enter an access code.")
      return;
    }

    try {
      // 🔥 Use your real API wrapper
      const res = await api.joinBoard(code);

      const boardId = res?.board_id || res?.board?.board_id;
      if (!boardId) {
        //alert("Invalid access code.");
        toast("Invalid access code.")
        return;
      }

      // close modal + reset field
      setShowJoinModal(false);
      setJoinCode("");

      // refresh boards on dashboard
      const refreshed = await api.listBoards();
      setBoards(refreshed);


    } catch (err) {
      console.error("Join board failed:", err);
      //alert("Failed to join board. Check your access code.");
      toast("Failed to join board. Check your access code.")
    }
  }


  return (
    <div className="max-w-4xl mx-auto p-4 space-y-6">

      {/* HEADER */}
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Your Boards</h1>
          <p className="text-sm text-gray-500">Logged in as {user?.email}</p>
        </div>

        <div className="flex gap-3">
          {/* JOIN BOARD BUTTON */}
          <button
            onClick={() => setShowJoinModal(true)}
            className="px-4 py-2 text-sm font-semibold bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700"
          >
            Join Board
          </button>

          <button
            onClick={signOut}
            className="px-4 py-2 text-sm font-semibold bg-red-500 text-white rounded-lg shadow hover:bg-red-600"
          >
            Sign Out
          </button>
        </div>
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

      {/* JOIN BOARD MODAL */}
      {showJoinModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center">
          <div className="bg-white p-6 rounded-lg shadow-xl w-80">
            <h2 className="text-xl font-bold mb-4">Join a Board</h2>

            <input
              className="border w-full p-2 rounded mb-4"
              placeholder="Enter access code"
              value={joinCode}
              onChange={(e) => setJoinCode(e.target.value)}
            />

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowJoinModal(false)}
                className="px-3 py-1 bg-gray-300 rounded"
              >
                Cancel
              </button>
              <button
                onClick={handleJoinBoard}
                className="px-3 py-1 bg-blue-600 text-white rounded"
              >
                Join
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
