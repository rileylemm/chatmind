# 🧠 3D Graph Interface Plan

A roadmap for integrating a 3D visualization mode into ChatMind using `react-force-graph-3d`. This feature will provide an immersive and interactive way to explore knowledge graphs built from ChatGPT data.

---

## 🎯 Objective

Create a fully interactive 3D graph view that visualizes:

- **Chats → Messages → Chunks → Tags**
- Semantic clusters and topic gravity centers
- Layer toggles between raw data and semantic overlays

---

## ⚙️ Tech Stack

| Component                  | Choice                        | Notes |
|---------------------------|-------------------------------|-------|
| **Renderer**              | `react-force-graph-3d`        | Based on Three.js, React-friendly |
| **Framework**             | React 19 + Vite               | Already in use |
| **Graph Data**            | `/api/graph` endpoint         | Neo4j-derived |
| **3D Engine (under hood)**| Three.js                      | Powered by `react-force-graph-3d` |
| **State/Control**         | Zustand / React Query         | Already in project |

---

## 🧱 MVP Milestone (v1)

### Features

- [ ] Render 3D force-directed graph
- [ ] Map data from `/api/graph` to nodes and links
- [ ] Use node types (chat, message, chunk, tag) for:
  - Shape (sphere, box, etc.)
  - Color coding
  - Sizing
- [ ] Zoom, rotate, drag interaction
- [ ] Node labels on hover
- [ ] Click node to display metadata

### File: `frontend/src/components/Graph3D.tsx`

```tsx
import ForceGraph3D from 'react-force-graph-3d';
``` 