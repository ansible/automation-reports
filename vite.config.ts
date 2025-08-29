import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [react(), visualizer({ open: true, filename: 'bundle-analysis.html' })],
  base: './',
  server: {
    host: 'localhost',
    port: 9000,
  },
  build: {
    outDir: 'dist',
  },
  root: 'src/frontend',
  resolve: {
    alias: {
      '@app': path.resolve(__dirname, 'src/frontend/app'),
    },
  },
});
