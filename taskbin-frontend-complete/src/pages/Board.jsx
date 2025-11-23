import { Link, useParams, useNavigate } from "react-router-dom";   // 🔥 CHANGED
import { useEffect, useState } from "react";
import { useApi } from "../hooks/useApi";
import { useAuth } from "../hooks/useAuth";
import TaskCard from "../components/TaskCard";
import EditTaskModal from "../components/EditTaskModal";
import CreateBoardModal from "../components/CreateBoardModal";
import { toast } from "react-hot-toast";



export default function Board() {
  const {id} = useParams();
  const navigate = useNavigate();  // 🔥 ADDED
  const {user} = useAuth();
  const api = useApi(user?.email);

  const [board, setBoard] = useState(null);
  const [boards, setBoards] = useState([]);   // 🔥 ADDED for sidebar list
  const [tasks, setTasks] = useState([]);
  const [members, setMembers] = useState([]);
  const [owner, setOwner] = useState(null);
  const [showCreateBoardModal, setShowCreateBoardModal] = useState(false);
  const [boardDeletedMessage, setBoardDeletedMessage] = useState(null);


  const [newTaskTitle, setNewTaskTitle] = useState("");
  const [newTaskStatus, setNewTaskStatus] = useState("todo");
  const [newTaskAssignee, setNewTaskAssignee] = useState("");
  const [newTaskDue, setNewTaskDue] = useState("");

  const [editingTask, setEditingTask] = useState(null);
  const [socket, setSocket] = useState(null);

  function broadcast(action, payload = {}) {
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({action, ...payload}));
  }

  // -----------------------------------
  // Load ALL boards (for sidebar)
  // -----------------------------------
  useEffect(() => {
    if (!user?.email) return;
    api.listBoards().then((res) => {
      setBoards(res || []);
    });
  }, [user?.email]);   // 🔥 ADDED

  // -----------------------------------
  // Initial board load
  // -----------------------------------
  useEffect(() => {
    if (!user?.email) return;

    async function init() {
      try {
        const meta = await api.getBoard(id);
        setBoard(meta);
        setMembers(meta?.members || []);
        setOwner(meta?.owner_id || null);

        const ts = await api.listTasks(id);
        setTasks(ts.map((t) => ({...t, id: t.task_id})));
      } catch (err) {
        console.error("Failed loading board or tasks:", err);
      }
    }

    init();
  }, [id, user?.email]);

  // -----------------------------------
  // WebSocket setup + send memberJoined
  // -----------------------------------
  useEffect(() => {
    if (!user?.email || !id) return;

    const wsUrl =
        `${import.meta.env.VITE_WEBSOCKET_API_URL}?` +
        `user_id=${encodeURIComponent(user.email)}` +
        `&board_id=${encodeURIComponent(id)}`;

    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Debug
      // console.log("🔥 WS RECEIVED RAW:", event.data);

      // ⛔ Ignore messages until board + API are fully ready
      if (!api) return;

      if (data.action === "taskUpdated") {
        api.listTasks(id).then((ts) =>
            setTasks(ts.map((t) => ({...t, id: t.task_id})))
        );
      }
      if (data.action === "boardDeleted") {
        // Show popup instead of alert
        setBoardDeletedMessage("This board has been deleted. Press OK to return to dashboard.");
      }

      if (data.action === "memberJoined") {
        api.getBoard(id).then((meta) => {
          setMembers(meta?.members || []);
        });
      }
    };
    setSocket(ws);
    return () => ws.close();
  }, [user?.email, id]);


  async function handleGenerateCode() {
    try {
      const res = await api.generateCode(id);
      const code = res?.access_code;

      if (!code) {
        //alert("Failed to generate code — backend returned no access_code");
        toast("Failed to generate code — backend returned no access_code")
        return;
      }

      alert(`Access Code for this board: ${code}`);
      toast(`Access Code: ${code}`, {
        icon: "🔑",
      });

    } catch (err) {
      console.error("Error generating code:", err);
      // alert("Failed to generate access code.");
      toast("Failed to generate access code.");
    }
  }

  async function handleCreateTask(e) {
    e.preventDefault();
    if (!newTaskTitle.trim()) return;

    await api.createTask(id, {
      title: newTaskTitle.trim(),
      description: "",
      task_status: newTaskStatus,
      assigned_to: newTaskAssignee || null,
      finish_by: newTaskDue ? new Date(newTaskDue).toISOString() : null,
    });

    setNewTaskTitle("");
    setNewTaskStatus("todo");
    setNewTaskAssignee("");
    setNewTaskDue("");

    const refreshed = await api.listTasks(id);
    setTasks(refreshed.map((t) => ({...t, id: t.task_id})));

    broadcast("taskUpdated", {
      board_id: id,
      user_id: user.email,
      message: "created",
    });
    toast.success("Task created!");
  }

  async function handleDeleteTask(taskId) {
    await api.deleteTask(id, taskId);
    setTasks((prev) => prev.filter((t) => (t.id || t.task_id) !== taskId));

    broadcast("taskUpdated", {
      board_id: id,
      user_id: user.email,
      message: "deleted",
    });
    toast.success("Task deleted!");
  }

  async function handleEditTask(taskId, updates) {
    await api.editTask(taskId, updates);

    const refreshed = await api.listTasks(id);
    setTasks(refreshed.map((t) => ({...t, id: t.task_id})));

    setEditingTask(null);

    broadcast("taskUpdated", {
      board_id: id,
      user_id: user.email,
      message: "updated",
    });
    toast.success("Task updated!");
  }

  async function createBoard(name, description) {
    await api.createBoard({
      name,
      description,
    });
    const refreshed = await api.listBoards();
    setBoards(refreshed);
    setShowCreateBoardModal(false);
  }

  async function handleDeleteBoard() {
    if (!confirm("Are you sure you want to delete this board? This cannot be undone.")) {
      return;
    }

    try {
      await api.deleteBoard(id);

      // Refresh board list for sidebar
      const refreshed = await api.listBoards();
      setBoards(refreshed);

      // Navigate back to dashboard
      navigate("/");
      toast.success("Deleted board!")
    } catch (err) {
      console.error("Delete board failed:", err);
      alert("Failed to delete board. Only the owner can delete it.");
    }
  }


  // ------------------------------
  // GROUP TASKS FOR THE 3 COLUMNS
  // ------------------------------
  const grouped = {
    todo: tasks.filter((t) => t.task_status === "todo"),
    in_progress: tasks.filter((t) => t.task_status === "in_progress"),
    done: tasks.filter((t) => t.task_status === "done"),
  };


  return (
      <div className="flex h-screen">
        {/* -----------------------------
        LEFT SIDEBAR
    ----------------------------- */}
        <div className="w-64 bg-gray-900 text-white p-4 flex flex-col border-r border-gray-700">
          <h2 className="text-lg mb-4 font-semibold">Your Boards</h2>
          <div className="flex-1 space-y-2 overflow-y-auto">
            {boards.map((b) => (
                <div
                    key={b.id}
                    onClick={() => navigate(`/boards/${b.id}`)}
                    className={`p-2 rounded cursor-pointer ${
                        b.id === id ? "bg-gray-700" : "hover:bg-gray-800 transition"
                    }`}
                >
                  {b.name}
                </div>
            ))}
          </div>
          <button
              onClick={() => setShowCreateBoardModal(true)}
              className="mt-4 bg-purple-600 hover:bg-purple-700 text-center py-2 rounded-lg transition"
          >
            + Create Board
          </button>
        </div>

        {/* -----------------------------
        RIGHT CONTENT
    ----------------------------- */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <Link to="/" className="text-sm text-blue-600 hover:underline">
            ← Back
          </Link>

          <header className="space-y-1 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">{board?.name || "Board"}</h1>
              {board?.description && (
                  <p className="text-sm text-gray-500">{board.description}</p>
              )}
            </div>

            <button
                onClick={handleGenerateCode}
                className="bg-purple-600 text-white px-3 py-2 rounded-lg shadow hover:bg-purple-700 transition"
            >
              Generate Access Code
            </button>

            {owner === user?.email && (
                <button
                    onClick={handleDeleteBoard}
                    className="bg-red-600 text-white px-3 py-2 rounded-lg shadow hover:bg-red-700 transition"
                >
                  Delete Board
                </button>
            )}
          </header>

          {/* MEMBERS SECTION */}
          <section className="bg-white rounded-xl shadow p-4 space-y-3">
            <h2 className="text-lg font-semibold">Members</h2>
            <div>
              <p className="text-sm font-semibold mb-1">Owner</p>
              <div className="bg-purple-50 px-3 py-2 rounded-lg flex justify-between">
                <span>{owner}</span>
                <span className="px-2 py-1 text-xs bg-purple-200 text-purple-800 rounded-full">
              owner
            </span>
              </div>
            </div>

            <div>
              <p className="text-sm font-semibold mt-3 mb-1">Members</p>
              {members.filter((m) => m.user_id !== owner).length === 0 ? (
                  <p className="text-sm text-gray-500">No other members.</p>
              ) : (
                  <ul className="space-y-1 text-sm">
                    {members
                        .filter((m) => m.user_id !== owner)
                        .map((m) => (
                            <li
                                key={m.user_id}
                                className="flex justify-between bg-gray-50 px-3 py-2 rounded-lg"
                            >
                              <span>{m.user_id}</span>
                              <span className="px-2 py-1 text-xs bg-gray-200 text-gray-600 rounded-full">
                      member
                    </span>
                            </li>
                        ))}
                  </ul>
              )}
            </div>
          </section>

          {/* CREATE TASK SECTION */}
          <section className="bg-white rounded-xl shadow p-4 space-y-3">
            <h2 className="text-lg font-semibold">Create a new task</h2>
            <form
                onSubmit={handleCreateTask}
                className="grid grid-cols-1 md:grid-cols-5 gap-3 items-end"
            >
              <div className="flex flex-col">
                <label>Title</label>
                <input
                    className="border p-2 rounded"
                    value={newTaskTitle}
                    onChange={(e) => setNewTaskTitle(e.target.value)}
                />
              </div>

              <div className="flex flex-col">
                <label>Status</label>
                <select
                    className="border p-2 rounded"
                    value={newTaskStatus}
                    onChange={(e) => setNewTaskStatus(e.target.value)}
                >
                  <option value="todo">Todo</option>
                  <option value="in_progress">In Progress</option>
                  <option value="done">Done</option>
                </select>
              </div>

              <div className="flex flex-col">
                <label>Assignee</label>
                <input
                    className="border p-2 rounded"
                    value={newTaskAssignee}
                    onChange={(e) => setNewTaskAssignee(e.target.value)}
                />
              </div>

              <div className="flex flex-col">
                <label>Due date</label>
                <input
                    type="date"
                    className="border p-2 rounded"
                    value={newTaskDue}
                    onChange={(e) => setNewTaskDue(e.target.value)}
                />
              </div>

              <button className="bg-black text-white px-4 py-2 rounded-lg">
                Create Task
              </button>
            </form>
          </section>

          {/* TASKS COLUMNS */}
          <section className="grid gap-6 grid-cols-1 md:grid-cols-3">
            {["todo", "in_progress", "done"].map((status) => (
                <div
                    key={status}
                    className="bg-white shadow rounded-xl p-4 min-h-[200px] flex flex-col"
                >
                  <h3 className="font-semibold mb-3 text-gray-700">
                    {status === "todo"
                        ? "Todo"
                        : status === "in_progress"
                            ? "In Progress"
                            : "Done"}
                  </h3>
                  <div className="flex-1 space-y-3">
                    {grouped[status].length === 0 ? (
                        <p className="text-sm text-gray-400 italic">No tasks.</p>
                    ) : (
                        grouped[status].map((t) => (
                            <TaskCard
                                key={t.id}
                                task={{
                                  ...t,
                                  task_id: t.id,
                                  onDelete: () => handleDeleteTask(t.id),
                                  onEdit: () => setEditingTask(t),
                                }}
                            />
                        ))
                    )}
                  </div>
                </div>
            ))}
          </section>

          {/* EDIT TASK MODAL */}
          {editingTask && (
              <EditTaskModal
                  task={editingTask}
                  onSave={(updates) => handleEditTask(editingTask.id, updates)}
                  onClose={() => setEditingTask(null)}
              />
          )}

          {/* CREATE BOARD MODAL */}
          {showCreateBoardModal && (
              <CreateBoardModal
                  onCreate={createBoard}
                  onClose={() => setShowCreateBoardModal(false)}
              />
          )}

          {/* ---------------------------
          BOARD DELETED MODAL
      --------------------------- */}
          {boardDeletedMessage && (
              <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
                <div className="bg-white p-6 rounded shadow-lg max-w-sm text-center">
                  <p className="mb-4">{boardDeletedMessage}</p>
                  <button
                      onClick={() => {
                        setBoardDeletedMessage(null); // close modal
                        navigate("/"); // navigate to dashboard
                      }}
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                  >
                    OK
                  </button>
                </div>
              </div>
          )}
        </div>
      </div>
  );
}
