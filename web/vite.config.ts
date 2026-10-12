import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Where the detection proxy (api/detect.ts) lives:
//   VITE_API_URL set  -> that origin (used by the GitHub Pages build)
//   building on Vercel -> same origin as the page
//   otherwise          -> no proxy; the page asks for a Roboflow key instead
const apiBase = process.env.VITE_API_URL?.replace(/\/+$/, '') || (process.env.VERCEL ? '' : null);

export default defineConfig({
    // Relative asset paths, so the build works under any GitHub Pages path.
    base: './',
    plugins: [react()],
    define: { __API_BASE__: JSON.stringify(apiBase) },
});
