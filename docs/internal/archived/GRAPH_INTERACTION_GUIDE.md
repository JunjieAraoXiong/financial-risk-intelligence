# Graph Interaction Guide

User interaction patterns for the Cytoscape.js knowledge graph.

---

## 1. Pan & Zoom

### Built-in Cytoscape.js Controls

```typescript
// Already enabled by default in GraphView
cy.userZoomingEnabled(true);
cy.userPanningEnabled(true);

// Configure sensitivity
cy.wheelSensitivity(0.2); // Reduce zoom speed
cy.minZoom(0.3);
cy.maxZoom(3);
```

### Programmatic Control

```typescript
// Zoom to fit all nodes
cy.fit(undefined, 50); // 50px padding

// Zoom to specific node
const node = cy.getElementById(nodeId);
cy.animate({
  fit: { eles: node, padding: 100 },
  duration: 500,
});

// Reset view
cy.zoom(1);
cy.pan({ x: 0, y: 0 });
```

### User Controls Component

```typescript
// src/components/GraphView/GraphControls.tsx
export function GraphControls({ cy }: { cy: Core | null }) {
  return (
    <div className="absolute top-4 right-4 flex flex-col gap-2">
      <button
        onClick={() => cy?.fit(undefined, 50)}
        className="p-2 bg-white rounded-lg shadow hover:bg-gray-100"
        title="Fit to view"
      >
        <ExpandIcon className="w-5 h-5" />
      </button>

      <button
        onClick={() => cy?.zoom(cy.zoom() * 1.2)}
        className="p-2 bg-white rounded-lg shadow hover:bg-gray-100"
        title="Zoom in"
      >
        <PlusIcon className="w-5 h-5" />
      </button>

      <button
        onClick={() => cy?.zoom(cy.zoom() * 0.8)}
        className="p-2 bg-white rounded-lg shadow hover:bg-gray-100"
        title="Zoom out"
      >
        <MinusIcon className="w-5 h-5" />
      </button>

      <button
        onClick={() => {
          cy?.zoom(1);
          cy?.pan({ x: 0, y: 0 });
        }}
        className="p-2 bg-white rounded-lg shadow hover:bg-gray-100"
        title="Reset"
      >
        <RefreshIcon className="w-5 h-5" />
      </button>
    </div>
  );
}
```

---

## 2. Node Selection

### Click to Select

```typescript
// In GraphView component
cy.on('tap', 'node', (evt) => {
  const node = evt.target;
  const nodeId = node.id();

  // Update store
  setSelectedNode(nodeId);

  // Visual feedback
  cy.nodes().removeClass('selected');
  node.addClass('selected');

  // Callback
  onNodeClick?.(nodeId);
});

// Deselect on background click
cy.on('tap', (evt) => {
  if (evt.target === cy) {
    setSelectedNode(null);
    cy.nodes().removeClass('selected');
  }
});
```

### Multi-Select (Shift+Click)

```typescript
const selectedNodes = new Set<string>();

cy.on('tap', 'node', (evt) => {
  if (evt.originalEvent.shiftKey) {
    // Multi-select mode
    const nodeId = evt.target.id();
    if (selectedNodes.has(nodeId)) {
      selectedNodes.delete(nodeId);
      evt.target.removeClass('selected');
    } else {
      selectedNodes.add(nodeId);
      evt.target.addClass('selected');
    }
  } else {
    // Single select (clear others)
    cy.nodes().removeClass('selected');
    selectedNodes.clear();
    selectedNodes.add(evt.target.id());
    evt.target.addClass('selected');
  }
});
```

---

## 3. Node Hover Tooltips

### Basic Tooltip

```typescript
// In GraphView component
cy.on('mouseover', 'node', (evt) => {
  const node = evt.target;
  const data = node.data();

  onNodeHover?.({
    id: node.id(),
    label: data.label,
    type: data.type,
    position: node.renderedPosition(),
  });
});

cy.on('mouseout', 'node', () => {
  onNodeHover?.(null);
});
```

### Tooltip Component

```typescript
// src/components/GraphView/NodeTooltip.tsx
interface NodeTooltipProps {
  node: {
    label: string;
    type: string;
    position: { x: number; y: number };
  } | null;
}

export function NodeTooltip({ node }: NodeTooltipProps) {
  if (!node) return null;

  return (
    <div
      className="absolute z-50 bg-white rounded-lg shadow-xl p-3 pointer-events-none"
      style={{
        left: node.position.x + 20,
        top: node.position.y - 40,
      }}
    >
      <div className="font-semibold text-gray-900">{node.label}</div>
      <div className="text-sm text-gray-600">{node.type}</div>
    </div>
  );
}
```

---

## 4. Expand/Collapse Nodes

### Expand Node (Load Neighborhood)

```typescript
// src/hooks/useNodeExpansion.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchNodeNeighborhood } from '@/lib/api/graph';

export function useNodeExpansion(cy: Core | null) {
  const queryClient = useQueryClient();

  const expandNode = useMutation({
    mutationFn: async (nodeId: string) => {
      // Fetch neighbors from API
      const { neighbors, edges } = await fetchNodeNeighborhood(nodeId);

      // Add to graph
      neighbors.forEach((n: any) => {
        if (!cy?.getElementById(n.id).length) {
          cy?.add({
            data: { id: n.id, label: n.label, type: n.type, group: n.group },
          });
        }
      });

      edges.forEach((e: any) => {
        if (!cy?.getElementById(`${e.source}-${e.target}`).length) {
          cy?.add({
            data: {
              id: `${e.source}-${e.target}`,
              source: e.source,
              target: e.target,
              type: e.type,
            },
          });
        }
      });

      // Re-layout
      cy?.layout({ name: 'cose', animate: true }).run();

      return nodeId;
    },
  });

  return expandNode;
}
```

### Collapse Node (Hide Neighborhood)

```typescript
function collapseNode(nodeId: string) {
  const node = cy.getElementById(nodeId);

  // Get connected nodes
  const neighbors = node.neighborhood('node');

  // Check if neighbors are only connected to this node
  neighbors.forEach((neighbor) => {
    const connectedTo = neighbor.connectedEdges().connectedNodes();
    if (connectedTo.length === 1) {
      // Only connected to this node, safe to remove
      neighbor.remove();
    }
  });

  // Remove orphaned edges
  cy.edges().filter((edge) => {
    return !edge.source().length || !edge.target().length;
  }).remove();
}
```

### UI Button

```typescript
<button
  onClick={() => {
    if (isExpanded) {
      collapseNode(nodeId);
    } else {
      expandNode.mutate(nodeId);
    }
  }}
  className="p-2 bg-indigo-600 text-white rounded-md"
>
  {isExpanded ? 'Collapse' : 'Expand'}
</button>
```

---

## 5. Search & Highlight

### Search Implementation

```typescript
// src/hooks/useGraphSearch.ts
export function useGraphSearch(cy: Core | null) {
  const [query, setQuery] = useState('');

  useEffect(() => {
    if (!cy || !query) {
      cy?.nodes().removeClass('highlighted');
      return;
    }

    const lowerQuery = query.toLowerCase();

    cy.nodes().forEach((node) => {
      const label = node.data('label')?.toLowerCase() || '';

      if (label.includes(lowerQuery)) {
        node.addClass('highlighted');
      } else {
        node.removeClass('highlighted');
      }
    });

    // Zoom to highlighted nodes
    const highlighted = cy.nodes('.highlighted');
    if (highlighted.length > 0) {
      cy.fit(highlighted, 50);
    }
  }, [query, cy]);

  return { query, setQuery };
}
```

### Search UI

```typescript
// src/components/FilterPanel/SearchFilter.tsx
export function SearchFilter({ cy }: { cy: Core | null }) {
  const { query, setQuery } = useGraphSearch(cy);

  return (
    <div className="relative">
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search nodes..."
        className="w-full px-3 py-2 pl-10 border border-gray-300 rounded-md"
      />
      <SearchIcon className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
    </div>
  );
}
```

### Highlighted Style

```typescript
// Add to Cytoscape styles
{
  selector: 'node.highlighted',
  style: {
    'background-color': '#fbbf24',
    'border-width': 3,
    'border-color': '#f59e0b',
    'box-shadow': '0 0 20px rgba(245, 158, 11, 0.8)',
  },
}
```

---

## 6. Context Menu (Right-Click)

```typescript
cy.on('cxttap', 'node', (evt) => {
  const node = evt.target;
  const position = evt.renderedPosition;

  showContextMenu({
    x: position.x,
    y: position.y,
    options: [
      {
        label: 'View Details',
        onClick: () => setSelectedNode(node.id()),
      },
      {
        label: 'Expand Neighbors',
        onClick: () => expandNode.mutate(node.id()),
      },
      {
        label: 'Hide Node',
        onClick: () => node.style('display', 'none'),
      },
      {
        label: 'Focus on Node',
        onClick: () => cy.fit(node, 100),
      },
    ],
  });
});
```

---

## 7. Keyboard Shortcuts

```typescript
// src/hooks/useKeyboardShortcuts.ts
export function useKeyboardShortcuts(cy: Core | null) {
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Zoom in: + or =
      if (e.key === '+' || e.key === '=') {
        cy?.zoom(cy.zoom() * 1.2);
      }

      // Zoom out: -
      if (e.key === '-') {
        cy?.zoom(cy.zoom() * 0.8);
      }

      // Fit: F
      if (e.key === 'f') {
        cy?.fit(undefined, 50);
      }

      // Reset: R
      if (e.key === 'r') {
        cy?.zoom(1);
        cy?.pan({ x: 0, y: 0 });
      }

      // Escape: Deselect
      if (e.key === 'Escape') {
        cy?.nodes().removeClass('selected');
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [cy]);
}
```

---

## 8. Filter by Relationship Type

```typescript
function filterByRelationshipType(type: string, show: boolean) {
  const edges = cy.edges(`[type = "${type}"]`);

  if (show) {
    edges.style('display', 'element');
  } else {
    edges.style('display', 'none');
  }
}

// UI checkboxes
<Checkbox
  checked={showEvolvesTo}
  onChange={(checked) => {
    setShowEvolvesTo(checked);
    filterByRelationshipType('evolvesTo', checked);
  }}
>
  Show evolvesTo relationships
</Checkbox>
```

---

## 9. Layout Switching

```typescript
const layouts = ['cose', 'circle', 'grid', 'breadthfirst'];

function changeLayout(layoutName: string) {
  cy.layout({
    name: layoutName,
    animate: true,
    animationDuration: 500,
  }).run();
}

// UI dropdown
<select onChange={(e) => changeLayout(e.target.value)}>
  <option value="cose">Force-Directed</option>
  <option value="circle">Circle</option>
  <option value="grid">Grid</option>
  <option value="breadthfirst">Hierarchical</option>
</select>
```

---

**Status:** Interaction patterns documented ✅
**Next:** See PERFORMANCE_OPTIMIZATION.md for scaling strategies
