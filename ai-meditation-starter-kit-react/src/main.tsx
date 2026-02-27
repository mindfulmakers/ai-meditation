import { createRoot } from "react-dom/client";
import App from "./App.tsx";
import "./index.css";

const originalError = console.error;
console.error = (...args) => {
  // TODO: Pass error to Openbase
  originalError(...args); // Pass through all other errors
};

createRoot(document.getElementById("root")!).render(<App />);
