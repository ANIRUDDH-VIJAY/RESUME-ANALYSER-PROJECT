import { useEffect, useState } from "react";

function App() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch(`${import.meta.env.VITE_API_URL}/test`)
      .then((res) => res.json())
      .then((data) => setMessage(data))
      .catch((err) => console.error(err));
  }, []);

  return (
    <div>
      <h1>Resume Analyzer</h1>
      <p>Backend says: {message}</p>
    </div>
  );
}

export default App;
