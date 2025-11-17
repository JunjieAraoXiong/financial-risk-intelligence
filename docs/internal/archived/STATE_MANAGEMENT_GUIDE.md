# State Management Guide

React Query + Zustand pattern for FE-EKG frontend.

---

## Architecture Overview

```
┌─────────────────┐
│  Server State   │ ← React Query (events, graph data)
│  (API Data)     │
└─────────────────┘

┌─────────────────┐
│   UI State      │ ← Zustand (selected node, zoom, filters)
│  (Ephemeral)    │
└─────────────────┘

┌─────────────────┐
│  Local Storage  │ ← Zustand persist (user preferences)
│  (Persistent)   │
└─────────────────┘
```

**Rule:** Server state in React Query, UI state in Zustand

---

## 1. Server State (React Query)

### Setup QueryClient

**File:** `src/app/providers.tsx`

```typescript
"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5 * 60 * 1000,
            gcTime: 10 * 60 * 1000,
            refetchOnWindowFocus: false,
            retry: 3,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

### Main Graph Data Hook

**File:** `src/hooks/useGraphData.ts`

```typescript
import { useQuery } from "@tanstack/react-query";
import { useFilterStore } from "@/stores/filterStore";
import { fetchTimeWindow, fetchPaginatedEvents } from "@/lib/api/events";

export function useGraphData() {
  const { startDate, endDate, offset, limit } = useFilterStore();

  return useQuery({
    queryKey: ["graph", startDate, endDate, offset, limit],
    queryFn: async () => {
      // Use time window if dates provided
      if (startDate && endDate) {
        const data = await fetchTimeWindow(startDate, endDate);
        return {
          nodes: processNodes(data.events),
          edges: processEdges(data.relationships),
          stats: data.stats,
        };
      }

      // Otherwise paginated
      const data = await fetchPaginatedEvents(offset, limit);
      return {
        nodes: processNodes(data.events),
        edges: processEdges(data.relationships),
        stats: data.stats,
      };
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// Helper functions
function processNodes(events: any[]) {
  return events.map((e) => ({
    id: e.eventId,
    label: e.label,
    type: e.type,
    group: e.group || "event",
  }));
}

function processEdges(relationships: any[]) {
  return relationships.map((r) => ({
    source: r.from,
    target: r.to,
    type: r.type,
    strength: r.score || 0.5,
  }));
}
```

### Event Details Hook

**File:** `src/hooks/useEventDetails.ts`

```typescript
import { useQuery } from "@tanstack/react-query";
import { fetchEventDetails } from "@/lib/api/events";

export function useEventDetails(eventId: string | null) {
  return useQuery({
    queryKey: ["event", eventId],
    queryFn: () => fetchEventDetails(eventId!),
    enabled: !!eventId, // Only fetch if eventId exists
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}
```

### Prefetch on Hover

```typescript
import { useQueryClient } from "@tanstack/react-query";

export function usePrefetch() {
  const queryClient = useQueryClient();

  const prefetchEvent = (eventId: string) => {
    queryClient.prefetchQuery({
      queryKey: ["event", eventId],
      queryFn: () => fetchEventDetails(eventId),
    });
  };

  return { prefetchEvent };
}
```

---

## 2. UI State (Zustand)

### Graph Store

**File:** `src/stores/graphStore.ts`

```typescript
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface GraphStore {
  // Selection
  selectedNode: string | null;
  hoveredNode: string | null;

  // Viewport
  zoomLevel: number;
  panPosition: { x: number; y: number };

  // Expansion
  expandedNodes: Set<string>;

  // Actions
  setSelectedNode: (nodeId: string | null) => void;
  setHoveredNode: (nodeId: string | null) => void;
  setZoom: (level: number) => void;
  setPan: (position: { x: number; y: number }) => void;
  toggleNodeExpand: (nodeId: string) => void;
  reset: () => void;
}

export const useGraphStore = create<GraphStore>()(
  persist(
    (set) => ({
      // Initial state
      selectedNode: null,
      hoveredNode: null,
      zoomLevel: 1,
      panPosition: { x: 0, y: 0 },
      expandedNodes: new Set(),

      // Actions
      setSelectedNode: (nodeId) => set({ selectedNode: nodeId }),
      setHoveredNode: (nodeId) => set({ hoveredNode: nodeId }),
      setZoom: (level) => set({ zoomLevel: level }),
      setPan: (position) => set({ panPosition: position }),

      toggleNodeExpand: (nodeId) =>
        set((state) => {
          const newExpanded = new Set(state.expandedNodes);
          if (newExpanded.has(nodeId)) {
            newExpanded.delete(nodeId);
          } else {
            newExpanded.add(nodeId);
          }
          return { expandedNodes: newExpanded };
        }),

      reset: () =>
        set({
          selectedNode: null,
          hoveredNode: null,
          zoomLevel: 1,
          panPosition: { x: 0, y: 0 },
          expandedNodes: new Set(),
        }),
    }),
    {
      name: "graph-store",
      partialize: (state) => ({
        // Only persist these fields
        zoomLevel: state.zoomLevel,
        expandedNodes: Array.from(state.expandedNodes),
      }),
    }
  )
);
```

### Filter Store

**File:** `src/stores/filterStore.ts`

```typescript
import { create } from "zustand";

interface FilterStore {
  startDate: string | null;
  endDate: string | null;
  eventTypes: string[];
  searchQuery: string;
  offset: number;
  limit: number;

  setDateRange: (start: string, end: string) => void;
  setEventTypes: (types: string[]) => void;
  setSearchQuery: (query: string) => void;
  setPage: (offset: number, limit: number) => void;
  reset: () => void;
}

export const useFilterStore = create<FilterStore>((set) => ({
  startDate: null,
  endDate: null,
  eventTypes: [],
  searchQuery: "",
  offset: 0,
  limit: 100,

  setDateRange: (start, end) => set({ startDate: start, endDate: end }),
  setEventTypes: (types) => set({ eventTypes: types }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setPage: (offset, limit) => set({ offset, limit }),

  reset: () =>
    set({
      startDate: null,
      endDate: null,
      eventTypes: [],
      searchQuery: "",
      offset: 0,
      limit: 100,
    }),
}));
```

### UI Store (Global UI State)

**File:** `src/stores/uiStore.ts`

```typescript
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UIStore {
  sidebarOpen: boolean;
  theme: "light" | "dark";
  layoutMode: "cose" | "circle" | "grid" | "breadthfirst";

  toggleSidebar: () => void;
  setTheme: (theme: "light" | "dark") => void;
  setLayoutMode: (mode: string) => void;
}

export const useUIStore = create<UIStore>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: "light",
      layoutMode: "cose",

      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setTheme: (theme) => set({ theme }),
      setLayoutMode: (mode: any) => set({ layoutMode: mode }),
    }),
    { name: "ui-store" }
  )
);
```

---

## 3. Component Usage Examples

### Using Graph Data

```typescript
// Component
export function GraphPage() {
  const { data, isLoading, error } = useGraphData();
  const { selectedNode, setSelectedNode } = useGraphStore();

  if (isLoading) return <GraphSkeleton />;
  if (error) return <Error error={error} />;

  return (
    <GraphView
      nodes={data.nodes}
      edges={data.edges}
      onNodeClick={setSelectedNode}
    />
  );
}
```

### Using Filters

```typescript
export function FilterPanel() {
  const { startDate, endDate, setDateRange } = useFilterStore();

  return (
    <DateRangeFilter
      startDate={startDate}
      endDate={endDate}
      onStartChange={(date) => setDateRange(date, endDate)}
      onEndChange={(date) => setDateRange(startDate, date)}
    />
  );
}
```

### Using Multiple Stores

```typescript
export function GraphControls() {
  const { zoomLevel, setZoom, reset } = useGraphStore();
  const { sidebarOpen, toggleSidebar } = useUIStore();

  return (
    <div>
      <button onClick={toggleSidebar}>Toggle Sidebar</button>
      <button onClick={reset}>Reset View</button>
      <div>Zoom: {zoomLevel.toFixed(2)}</div>
    </div>
  );
}
```

---

## 4. State Flow Diagram

```
User Action
    ↓
Component Event Handler
    ↓
Zustand Action (UI state)
    OR
React Query Mutation (Server state)
    ↓
State Update
    ↓
Component Re-render
    ↓
Cytoscape.js Update
```

**Example:**

```typescript
// 1. User clicks node
cy.on('tap', 'node', (evt) => {
  const nodeId = evt.target.id();

  // 2. Update Zustand
  setSelectedNode(nodeId);

  // 3. Component re-renders
  // EventCard now shows selectedNode

  // 4. Prefetch data
  prefetchEvent(nodeId);
});
```

---

## 5. Optimistic Updates

For mutations (expand node):

```typescript
const expandNode = useMutation({
  mutationFn: fetchNodeNeighborhood,

  // Optimistic update
  onMutate: async (nodeId) => {
    // Cancel any outgoing refetches
    await queryClient.cancelQueries({ queryKey: ["graph"] });

    // Snapshot previous value
    const previousGraph = queryClient.getQueryData(["graph"]);

    // Optimistically update to show loading state
    queryClient.setQueryData(["graph"], (old: any) => ({
      ...old,
      loadingNodes: [...old.loadingNodes, nodeId],
    }));

    return { previousGraph };
  },

  // On error, rollback
  onError: (err, nodeId, context) => {
    queryClient.setQueryData(["graph"], context.previousGraph);
  },

  // On success, refetch
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ["graph"] });
  },
});
```

---

## 6. Debugging

### React Query Devtools

```typescript
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

<ReactQueryDevtools initialIsOpen={false} position="bottom-right" />
```

### Zustand Devtools

```typescript
import { devtools } from "zustand/middleware";

export const useGraphStore = create<GraphStore>()(
  devtools(
    persist(
      (set) => ({
        // ... store
      }),
      { name: "graph-store" }
    ),
    { name: "GraphStore" }
  )
);
```

### Log State Changes

```typescript
// Add to store
set: (fn) => {
  const newState = fn(get());
  console.log("State changed:", newState);
  return set(newState);
};
```

---

## 7. Best Practices

### ✅ DO

- Keep server state in React Query
- Keep UI state in Zustand
- Use query keys that include all dependencies
- Memoize expensive selectors
- Persist user preferences
- Use optimistic updates for instant UX

### ❌ DON'T

- Store API responses in Zustand
- Duplicate state between React Query and Zustand
- Use query keys without dependencies
- Over-persist (don't persist everything)
- Update state on every render

---

## 8. Testing

### Test React Query Hooks

```typescript
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useGraphData } from "./useGraphData";

test("fetches graph data", async () => {
  const queryClient = new QueryClient();
  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  const { result } = renderHook(() => useGraphData(), { wrapper });

  await waitFor(() => expect(result.current.isSuccess).toBe(true));
  expect(result.current.data.nodes).toBeDefined();
});
```

### Test Zustand Stores

```typescript
import { renderHook, act } from "@testing-library/react";
import { useGraphStore } from "./graphStore";

test("updates selected node", () => {
  const { result } = renderHook(() => useGraphStore());

  act(() => {
    result.current.setSelectedNode("node1");
  });

  expect(result.current.selectedNode).toBe("node1");
});
```

---

**Status:** State management documented ✅
**Ready to build!** All 7 docs complete.
