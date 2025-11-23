import { useState } from "react";

export default function CreateBoardModal({ onCreate, onClose }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  function handleSubmit(e) {
    e.preventDefault();
    if (!name.trim()) return;
    onCreate(name.trim(), description.trim());
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center">
      <div className="bg-white w-full max-w-md rounded-xl shadow-lg p-6 space-y-4">
        <h2 className="text-xl font-semibold">Create a new board</h2>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <input
            className="w-full border p-2 rounded"
            placeholder="Board name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />

          <input
            className="w-full border p-2 rounded"
            placeholder="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-2 bg-gray-200 rounded-lg hover:bg-gray-300"
            >
              Cancel
            </button>

            <button
              type="submit"
              className="px-3 py-2 bg-gray-900 text-white rounded-lg"
            >
              Create
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
