import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./fonts/fonts.css";             // self-hosted Onest + JetBrains Mono (no third-party font host)
import "./styles/questcity.css";        // mocks link bundle.css first…
import "./styles/quest-screens.css";    // …then quest-mocks.css
import "./styles/app.css";

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);
