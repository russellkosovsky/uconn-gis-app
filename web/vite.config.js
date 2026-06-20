import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The React dev server runs on 5173 and proxies API calls to FastAPI on 8000,
// so the browser sees one origin and the client code never hardcodes a host.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
      "/tiles": "http://localhost:8000",
    },
  },
});
