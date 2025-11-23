// src/pages/Login.jsx
export default function Login() {
  const loginUrl = import.meta.env.VITE_COGNITO_LOGIN_URL;

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-50">
      <h1 className="text-2xl font-semibold mb-6">Welcome to TaskBin</h1>

      <button
        onClick={() => (window.location.href = loginUrl)}
        className="px-6 py-3 rounded-lg bg-indigo-600 text-white font-semibold shadow hover:bg-indigo-700"
      >
        Login with TaskBin
      </button>
    </div>
  );
}
