import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // allow Cloudflare quick-tunnel hostnames (*.trycloudflare.com) to reach this dev server
    allowedHosts: true,
    // relay API calls to the backend over localhost so only the frontend needs a public tunnel
    proxy: {
      "/query": "http://localhost:8000",
      "/health": "http://localhost:8000",
      "/status": "http://localhost:8000",
      "/collections": "http://localhost:8000",
      "/eval": "http://localhost:8000",
    },
  },
});
