import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    build: {
        outDir: '../rhombus/preview/dist',
        emptyOutDir: true,
    },
    server: {
        proxy: {
            // Leitet alle Anfragen, die mit /data beginnen, an dein Backend weiter
            '/data': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
            },
        },
    },
});
