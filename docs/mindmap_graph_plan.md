
# 🧠 Mindmap Graph System Design — Best Practices for Chat Memory

## 🎯 Goal

Create an **interactive, intuitive graph view** of your chat history that:
- Uses **semantic relationships** for layout and navigation
- Makes **exploration of topics and ideas** natural
- Handles large-scale data (thousands of messages)
- Feels like a **visual memory palace** for long-term knowledge

---

## 1. 🧩 Graph Layout Strategy

### ✅ Best Practice:
**Hybrid Semantic-Force Layout**

**What it means:**
- Use a **UMAP** or **t-SNE** projection on message/topic embeddings to reduce to 2D — captures true semantic space.
- Then apply a **force-directed layout** *with constraints* to:
  - Prevent overlap
  - Preserve local clustering
  - Simulate slight pull/push between related items

**Why:**
- UMAP/t-SNE gives global structure based on embeddings
- Force simulation ensures clean spacing and user flow

**Implementation Tip:**
- Use UMAP to generate fixed `(x, y)` positions (with a seed for reproducibility)
- Input these as initial positions into `react-force-graph-2d` or `d3-force`
- Tune the `charge` and `linkDistance` dynamically by cluster density

---

## 2. 🕸️ Edge Visualization

### ✅ Best Practice:
**Contextual Edge Visibility**

| View Mode           | Show Edges? | Type of Edges              |
|---------------------|-------------|-----------------------------|
| Topic View          | Yes         | Topic-to-topic similarity   |
| Topic Expanded View | Yes         | Chat-to-chat (same topic)   |
| Zoomed Message View | Optional    | Message references/citations |

**Why:**
- Too many edges = visual noise
- Edges only matter when they help interpret relationships

**Design Enhancements:**
- Use curved edges with **opacity scaling by weight**
- Animate or highlight on hover

---

## 3. 🔢 Node Sizing (Visual Weight)

### ✅ Best Practice:
**Size Nodes by Combined Importance**

Formula:

```ts
nodeSize = log10(totalMessages + 1) * recencyBoost * importanceBoost
```

Where:
- `totalMessages` = count in that chat/topic
- `recencyBoost` = scale recent chats up slightly (e.g. last 30d = ×1.2)
- `importanceBoost` = based on pin/star/mentions/etc.

**Why:**
- Balances scale (size from volume) with human salience

---

## 4. 🪄 Hover + Click Behavior

### ✅ Best Practice:
**Multilayered Popup Content**

#### Hover Tooltip
- Title / summary
- Tag count
- Recent timestamp
- Semantic category

#### Click Panel or Modal
- Chat preview (first 2-3 messages)
- Similar topics (with scores)
- Link to open full thread
- Actions: Pin, Annotate, Copy

---

## 5. 🧭 Navigation Flow

### ✅ Best Practice:
**Breadcrumb + Zoom Controls**

| Action                  | UI Element              |
|-------------------------|-------------------------|
| Zoom in to topic        | Click or scroll on node |
| Zoom out                | “Back to Topics” button |
| Navigate up hierarchy   | Breadcrumb trail        |
| Snap to home view       | Compass/reset button    |

---

## 6. 🗃️ Data Preprocessing

Before rendering, process your tagged chat data into:

```ts
interface GraphNode {
  id: string;
  type: 'Topic' | 'Chat' | 'Message';
  name: string;
  embedding: number[];
  clusterId?: string;
  timestamp?: string;
  importance?: number;
  x?: number;
  y?: number;
}
```

Use UMAP to set `(x, y)` coordinates. Group chats into clusters (`clusterId`), calculate importance and freshness for sizing and color.

---

## 7. 🧪 UMAP Projection Code

```python
import json
import numpy as np
import umap
from pathlib import Path

# Load your node data
with open("data/processed/nodes_with_embeddings.json") as f:
    nodes = json.load(f)

# Extract embeddings
embeddings = np.array([node["embedding"] for node in nodes])

# Run UMAP
reducer = umap.UMAP(random_state=42)
embedding_2d = reducer.fit_transform(embeddings)

# Update nodes with x/y
for i, node in enumerate(nodes):
    node["x"] = float(embedding_2d[i][0])
    node["y"] = float(embedding_2d[i][1])

# Save output
with open("data/processed/nodes_with_xy.json", "w") as f:
    json.dump(nodes, f, indent=2)
```

---

## 🧪 Final Steps

1. ✅ Finalize `tags_master_list.json` + `tag_aliases.json`
2. ✅ Normalize tags in your processed chunks
3. ✅ Run UMAP on node embeddings
4. ✅ Load updated coordinates into GraphView
5. ✅ Design UI layers and interactivity
6. 🚢 Ship your visual mind browser MVP
