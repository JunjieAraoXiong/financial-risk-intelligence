# FE-EKG Frontend Architecture

**Framework:** Next.js 14 (App Router)
**Graph Library:** Cytoscape.js
**State Management:** React Query + Zustand
**Styling:** Tailwind CSS
**Language:** TypeScript

---

## Project Structure

```
feekg-frontend/
├── src/
│   ├── app/                           # Next.js 14 App Router
│   │   ├── layout.tsx                 # Root layout with providers
│   │   ├── page.tsx                   # Home page → redirects to /graph
│   │   ├── graph/
│   │   │   ├── page.tsx               # Main graph visualization page
│   │   │   └── loading.tsx            # Loading skeleton
│   │   ├── timeline/
│   │   │   └── page.tsx               # Timeline-focused view
│   │   ├── stats/
│   │   │   └── page.tsx               # Statistics dashboard
│   │   └── api/                       # Next.js API routes (proxy to Flask)
│   │       ├── events/
│   │       │   └── route.ts           # Proxy /api/events/*
│   │       ├── graph/
│   │       │   └── route.ts           # Proxy /api/graph/*
│   │       └── health/
│   │           └── route.ts           # Health check
│   │
│   ├── components/                    # React components
│   │   ├── GraphView/                 # Main graph visualization
│   │   │   ├── index.tsx              # Cytoscape.js container
│   │   │   ├── GraphControls.tsx      # Zoom, pan, reset controls
│   │   │   ├── GraphLegend.tsx        # Color legend
│   │   │   ├── NodeTooltip.tsx        # Hover tooltip
│   │   │   └── useGraphLayout.ts      # Custom hook for layouts
│   │   │
│   │   ├── FilterPanel/               # Filtering UI
│   │   │   ├── index.tsx              # Main filter container
│   │   │   ├── DateRangeFilter.tsx    # Time range picker
│   │   │   ├── EventTypeFilter.tsx    # Event type checkboxes
│   │   │   ├── SearchFilter.tsx       # Search input
│   │   │   └── ImpactFilter.tsx       # Min degree slider
│   │   │
│   │   ├── EventCard/                 # Event detail display
│   │   │   ├── index.tsx              # Card container
│   │   │   ├── EventHeader.tsx        # Title, date, type badge
│   │   │   ├── EventMeta.tsx          # CSV provenance metadata
│   │   │   ├── RelatedEvents.tsx      # Connected events list
│   │   │   └── EvolutionLinks.tsx     # Evolution chain display
│   │   │
│   │   ├── Timeline/                  # Timeline scrubber
│   │   │   ├── index.tsx              # Timeline component
│   │   │   ├── TimeAxis.tsx           # D3.js time axis
│   │   │   ├── EventMarkers.tsx       # Event dots on timeline
│   │   │   └── RangeBrush.tsx         # D3.js brush for selection
│   │   │
│   │   ├── StatsPanel/                # Statistics display
│   │   │   ├── index.tsx              # Stats container
│   │   │   ├── StatCard.tsx           # Individual stat card
│   │   │   └── EntityList.tsx         # Top entities list
│   │   │
│   │   ├── Layout/                    # Layout components
│   │   │   ├── Header.tsx             # Top navigation
│   │   │   ├── Sidebar.tsx            # Collapsible sidebar
│   │   │   └── Footer.tsx             # Footer with metadata
│   │   │
│   │   └── ui/                        # Reusable UI components
│   │       ├── Button.tsx             # Button variants
│   │       ├── Card.tsx               # Card container
│   │       ├── Input.tsx              # Input field
│   │       ├── Select.tsx             # Select dropdown
│   │       ├── Checkbox.tsx           # Checkbox
│   │       ├── Badge.tsx              # Badge/tag
│   │       ├── Skeleton.tsx           # Loading skeleton
│   │       ├── Toast.tsx              # Toast notifications
│   │       └── Modal.tsx              # Modal dialog
│   │
│   ├── hooks/                         # Custom React hooks
│   │   ├── useGraphData.ts            # React Query hook for graph data
│   │   ├── useEventDetails.ts         # Fetch event details
│   │   ├── useFilters.ts              # Filter state management
│   │   ├── useGraphLayout.ts          # Layout algorithms
│   │   ├── useDebounce.ts             # Debounce utility
│   │   ├── useLocalStorage.ts         # Persist state to localStorage
│   │   └── useKeyboardShortcuts.ts    # Keyboard shortcuts
│   │
│   ├── stores/                        # Zustand stores
│   │   ├── graphStore.ts              # Graph UI state
│   │   ├── filterStore.ts             # Filter state
│   │   └── uiStore.ts                 # Global UI state (theme, sidebar)
│   │
│   ├── lib/                           # Utilities and libraries
│   │   ├── api/                       # API client
│   │   │   ├── client.ts              # Fetch wrapper
│   │   │   ├── events.ts              # Event API functions
│   │   │   ├── graph.ts               # Graph API functions
│   │   │   └── types.ts               # API response types
│   │   ├── constants.ts               # Constants and config
│   │   ├── utils.ts                   # Utility functions
│   │   ├── formatters.ts              # Date, number formatters
│   │   └── cytoscape/                 # Cytoscape.js utilities
│   │       ├── styles.ts              # Graph styles
│   │       ├── layouts.ts             # Layout configs
│   │       └── extensions.ts          # Custom extensions
│   │
│   └── types/                         # TypeScript types
│       ├── index.ts                   # Main type exports
│       ├── graph.ts                   # Graph-related types
│       ├── event.ts                   # Event types
│       └── api.ts                     # API types
│
├── public/                            # Static assets
│   ├── icons/                         # Icon assets
│   └── images/                        # Images
│
├── .env.local                         # Environment variables
├── .env.example                       # Example env vars
├── next.config.js                     # Next.js config
├── tailwind.config.ts                 # Tailwind config
├── tsconfig.json                      # TypeScript config
├── package.json                       # Dependencies
└── README.md                          # Frontend documentation
```

---

## Architecture Patterns

### 1. Data Flow

```
┌─────────────┐
│   Flask API │ (http://localhost:5000)
│  (Backend)  │
└──────┬──────┘
       │ HTTP/JSON
       ↓
┌─────────────┐
│  Next.js    │ (http://localhost:3000)
│  API Routes │ (Proxy layer)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ React Query │ (Server state caching)
│  + Zustand  │ (UI state management)
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  React      │
│  Components │
└──────┬──────┘
       │
       ↓
┌─────────────┐
│ Cytoscape.js│ (Graph rendering)
└─────────────┘
```

### 2. State Management Strategy

**Server State (React Query):**
- Graph data (events, nodes, edges)
- Event details
- Statistics
- Search results

**UI State (Zustand):**
- Selected node
- Zoom level
- Pan position
- Active filters
- Sidebar open/closed
- Theme preference

**Why this split:**
- React Query handles caching, background refetch, optimistic updates
- Zustand handles ephemeral UI state that doesn't need caching
- Clear separation of concerns

### 3. Component Composition

```tsx
// Page level (app/graph/page.tsx)
<GraphPage>
  <Sidebar>
    <FilterPanel />
    <StatsPanel />
  </Sidebar>

  <MainContent>
    <GraphView />
    <Timeline />
  </MainContent>

  {selectedNode && <EventCard />}
</GraphPage>
```

### 4. API Proxy Pattern

Why proxy through Next.js API routes instead of direct fetch to Flask:

**Benefits:**
1. **CORS handling** - No CORS issues
2. **Request transformation** - Clean up responses
3. **Error handling** - Consistent error format
4. **Caching** - Can add edge caching later
5. **Authentication** - Add auth layer if needed

**Example:**
```tsx
// src/app/api/events/route.ts
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const offset = searchParams.get('offset') || '0'
  const limit = searchParams.get('limit') || '100'

  const response = await fetch(
    `${process.env.FLASK_API_URL}/api/events/paginated?offset=${offset}&limit=${limit}`
  )

  const data = await response.json()
  return Response.json(data)
}
```

---

## Key Files Explained

### `src/app/layout.tsx` - Root Layout

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
    },
  },
})

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <QueryClientProvider client={queryClient}>
          <Header />
          {children}
          <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
      </body>
    </html>
  )
}
```

### `src/hooks/useGraphData.ts` - Main Data Hook

```tsx
import { useQuery } from '@tanstack/react-query'
import { useFilterStore } from '@/stores/filterStore'
import { fetchTimeWindow, fetchPaginatedEvents } from '@/lib/api/events'

export function useGraphData() {
  const { startDate, endDate, offset, limit } = useFilterStore()

  return useQuery({
    queryKey: ['graph', startDate, endDate, offset, limit],
    queryFn: async () => {
      if (startDate && endDate) {
        return fetchTimeWindow(startDate, endDate)
      }
      return fetchPaginatedEvents(offset, limit)
    },
    enabled: true, // Always enabled
    refetchInterval: 60000, // Refetch every minute
  })
}
```

### `src/stores/graphStore.ts` - Zustand Store

```tsx
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface GraphStore {
  selectedNode: string | null
  hoveredNode: string | null
  zoomLevel: number
  panPosition: { x: number; y: number }
  expandedNodes: Set<string>

  setSelectedNode: (nodeId: string | null) => void
  setHoveredNode: (nodeId: string | null) => void
  setZoom: (level: number) => void
  setPan: (position: { x: number; y: number }) => void
  toggleNodeExpand: (nodeId: string) => void
  reset: () => void
}

export const useGraphStore = create<GraphStore>()(
  persist(
    (set) => ({
      selectedNode: null,
      hoveredNode: null,
      zoomLevel: 1,
      panPosition: { x: 0, y: 0 },
      expandedNodes: new Set(),

      setSelectedNode: (nodeId) => set({ selectedNode: nodeId }),
      setHoveredNode: (nodeId) => set({ hoveredNode: nodeId }),
      setZoom: (level) => set({ zoomLevel: level }),
      setPan: (position) => set({ panPosition: position }),
      toggleNodeExpand: (nodeId) => set((state) => {
        const newExpanded = new Set(state.expandedNodes)
        if (newExpanded.has(nodeId)) {
          newExpanded.delete(nodeId)
        } else {
          newExpanded.add(nodeId)
        }
        return { expandedNodes: newExpanded }
      }),
      reset: () => set({
        selectedNode: null,
        hoveredNode: null,
        zoomLevel: 1,
        panPosition: { x: 0, y: 0 },
        expandedNodes: new Set()
      })
    }),
    {
      name: 'graph-store', // localStorage key
      partialize: (state) => ({ // Only persist these fields
        zoomLevel: state.zoomLevel,
        expandedNodes: Array.from(state.expandedNodes) // Convert Set to Array
      }),
    }
  )
)
```

### `src/lib/constants.ts` - Configuration

```tsx
export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000',
  TIMEOUT: 30000, // 30 seconds
  RETRY_COUNT: 3,
}

export const GRAPH_CONFIG = {
  DEFAULT_PAGE_SIZE: 100,
  MAX_NODES: 1000,
  MAX_EDGES: 5000,
  ANIMATION_DURATION: 300,
}

export const COLORS = {
  // Relationship types
  hasActor: '#10b981',    // emerald
  hasTarget: '#ef4444',   // red
  involves: '#3b82f6',    // blue
  relatedTo: '#a855f7',   // purple
  evolvesTo: '#f59e0b',   // orange

  // Entity types
  bank: '#3b82f6',               // blue
  regulator: '#8b5cf6',          // purple
  investment_bank: '#ec4899',    // pink

  // Event types
  legal_issue: '#ef4444',
  merger_acquisition: '#8b5cf6',
  credit_downgrade: '#f59e0b',
  bankruptcy: '#dc2626',
  // ... all event types
}

export const LAYOUTS = {
  cose: {
    name: 'cose',
    animate: true,
    animationDuration: 500,
    idealEdgeLength: 100,
    nodeOverlap: 20,
    refresh: 20,
    fit: true,
    padding: 30,
    randomize: false,
    componentSpacing: 100,
    nodeRepulsion: 400000,
    edgeElasticity: 100,
    nestingFactor: 5,
    gravity: 80,
    numIter: 1000,
    initialTemp: 200,
    coolingFactor: 0.95,
    minTemp: 1.0
  },
  // Add more layouts: circle, grid, breadthfirst, etc.
}
```

---

## Routing Structure

### Page Routes

| Route | Component | Purpose |
|-------|-----------|---------|
| `/` | `app/page.tsx` | Landing page, redirects to `/graph` |
| `/graph` | `app/graph/page.tsx` | Main graph visualization |
| `/timeline` | `app/timeline/page.tsx` | Timeline-focused view |
| `/stats` | `app/stats/page.tsx` | Statistics dashboard |

### API Routes (Proxy)

| Route | Proxies To | Purpose |
|-------|------------|---------|
| `/api/events/paginated` | `Flask: /api/events/paginated` | Get paginated events |
| `/api/events/timewindow` | `Flask: /api/events/timewindow` | Get time-filtered events |
| `/api/events/:id` | `Flask: /api/events/:id` | Get event details |
| `/api/graph/stats` | `Flask: /api/graph/stats` | Get graph statistics |
| `/api/health` | `Flask: /health` | Health check |

---

## Technology Decisions

### Why Next.js 14?

✅ **App Router** - Modern React Server Components
✅ **API Routes** - Built-in proxy layer
✅ **TypeScript** - First-class support
✅ **Optimizations** - Automatic code splitting, image optimization
✅ **Developer Experience** - Fast refresh, great dev tools

### Why Cytoscape.js over D3.js?

✅ **Better for networks** - Built specifically for graph visualization
✅ **Performance** - Handles 1000+ nodes better
✅ **Built-in layouts** - Cose, circle, grid, breadthfirst
✅ **Easier expand/collapse** - Native support for showing/hiding nodes
✅ **Less code** - D3.js requires more manual work
❌ **Less flexible** - D3.js has more control (but we don't need it)

### Why React Query + Zustand (not Redux)?

✅ **React Query** - Best for server state (caching, refetch, mutations)
✅ **Zustand** - Simpler than Redux for UI state
✅ **Separation** - Clear boundary between server and UI state
✅ **Less boilerplate** - Redux requires actions, reducers, etc.
✅ **Better DevTools** - React Query Devtools are excellent

### Why Tailwind CSS?

✅ **Utility-first** - Fast development
✅ **Consistent design** - Design system built-in
✅ **Small bundle** - Purges unused styles
✅ **Mobile-first** - Responsive by default
✅ **Customizable** - Easy to extend with FE-EKG colors

---

## Deployment Strategy (Future)

### Development

```bash
# Frontend
npm run dev  # localhost:3000

# Backend (Flask)
python api/app.py  # localhost:5000
```

### Production

**Option 1: Vercel + Flask on VM**
- Frontend: Deploy to Vercel (zero-config)
- Backend: Flask on AWS EC2 / DigitalOcean
- CORS: Configured in Flask

**Option 2: Docker Compose**
- Single `docker-compose.yml` with:
  - Next.js (port 3000)
  - Flask (port 5000)
  - AllegroGraph (port 10035)

**Option 3: All on VM**
- Nginx reverse proxy
  - `/` → Next.js (PM2)
  - `/api` → Flask (Gunicorn)
  - `/ag` → AllegroGraph

---

## Performance Targets

| Metric | Target | How |
|--------|--------|-----|
| Initial Load | < 2s | Code splitting, lazy loading |
| Time to Interactive | < 3s | Optimized bundle, preload critical |
| Graph Render (100 nodes) | < 500ms | Cytoscape.js optimization |
| Graph Render (1000 nodes) | < 2s | Viewport culling, pagination |
| API Response | < 200ms | Backend optimization (done) |
| Lighthouse Score | 90+ | Image optimization, a11y |
| Bundle Size | < 500 KB | Tree shaking, dynamic imports |

---

## File Naming Conventions

- **Components:** PascalCase (e.g., `GraphView.tsx`, `EventCard.tsx`)
- **Hooks:** camelCase with `use` prefix (e.g., `useGraphData.ts`)
- **Utils:** camelCase (e.g., `formatDate.ts`, `api.ts`)
- **Types:** PascalCase (e.g., `Event`, `GraphNode`)
- **Constants:** UPPER_SNAKE_CASE (e.g., `API_BASE_URL`)

---

## Testing Strategy (Future)

- **Unit:** Vitest + React Testing Library
- **Integration:** Playwright
- **E2E:** Playwright
- **Coverage:** 80%+ target

---

**Next Steps:**
1. Read `FRONTEND_SETUP_GUIDE.md` to bootstrap the project
2. Review `COMPONENT_LIBRARY.md` for component specs
3. Check `STATE_MANAGEMENT_GUIDE.md` for patterns
4. Start building Phase 1 MVP

**Status:** Architecture defined ✅
**Last Updated:** 2025-11-15
