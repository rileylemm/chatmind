# ChatMind Frontend

React-based frontend for visualizing the ChatGPT knowledge graph using Cytoscape.js.

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start development server:**
   ```bash
   npm start
   ```

3. **Build for production:**
   ```bash
   npm run build
   ```

## Features

- **Interactive Graph Visualization**: Explore topics, chats, and messages in a network graph
- **Topic Clusters**: View semantically clustered topics with summaries
- **Chat Navigation**: Browse individual chats and their messages
- **Search**: Search through messages by content
- **Responsive Design**: Works on desktop and mobile devices

## Architecture

- **React 18**: Modern React with hooks
- **TypeScript**: Type-safe development
- **Material-UI**: Beautiful, accessible components
- **Cytoscape.js**: Powerful graph visualization library
- **Axios**: HTTP client for API communication

## API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000` and expects the following endpoints:

- `GET /graph` - Get graph data for visualization
- `GET /topics` - Get all topic clusters
- `GET /chats` - Get all chats
- `GET /chats/{id}/messages` - Get messages for a chat
- `GET /topics/{id}/messages` - Get messages for a topic
- `GET /search?query=...` - Search messages

## Development

The main component is `App.tsx` which handles:
- Loading graph data from the API
- Rendering the Cytoscape.js visualization
- Managing the sidebar with topics and chats
- Displaying message details in the side panel

## Styling

The graph uses different colors and sizes for different node types:
- **Topics** (red): Large nodes representing semantic clusters
- **Chats** (teal): Medium nodes representing conversations
- **Messages** (blue): Small nodes representing individual messages 