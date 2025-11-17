# Performance Optimization Guide

Strategies to keep the FE-EKG frontend fast and responsive.

---

## 1. Pagination Strategy

### Backend Already Optimized (40x faster)

The Flask API provides paginated endpoints:

```typescript
// Load in chunks
const PAGE_SIZE = 100;

export function useInfiniteGraph() {
  return useInfiniteQuery({
    queryKey: ['graph'],
    queryFn: ({ pageParam = 0 }) =>
      fetchPaginatedEvents(pageParam, PAGE_SIZE),
    getNextPageParam: (lastPage, pages) => {
      const offset = pages.length * PAGE_SIZE;
      return offset < lastPage.total ? offset : undefined;
    },
  });
}
```

### Load More on Scroll

```typescript
const { data, fetchNextPage, hasNextPage } = useInfiniteGraph();

const handleScroll = () => {
  if (hasNextPage && !isFetching) {
    fetchNextPage();
  }
};
```

---

## 2. Graph Virtualization (1000+ Nodes)

### Viewport Culling

```typescript
// Only render nodes in viewport
cy.on('viewport', _.debounce(() => {
  const extent = cy.extent();
  const zoom = cy.zoom();

  cy.nodes().forEach((node) => {
    const pos = node.position();
    const inViewport =
      extent.x1 < pos.x && pos.x < extent.x2 &&
      extent.y1 < pos.y && pos.y < extent.y2;

    // Hide nodes outside viewport at low zoom
    if (zoom < 0.5 && !inViewport) {
      node.style('display', 'none');
    } else {
      node.style('display', 'element');
    }
  });
}, 100));
```

### Simplify Rendering at Low Zoom

```typescript
cy.on('zoom', () => {
  const zoom = cy.zoom();

  if (zoom < 0.6) {
    // Hide labels and edges at low zoom
    cy.nodes().style('label', '');
    cy.edges().style('display', 'none');
  } else {
    cy.nodes().style('label', 'data(label)');
    cy.edges().style('display', 'element');
  }
});
```

---

## 3. React Query Caching

### Aggressive Caching

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,    // 5 min - data fresh
      gcTime: 10 * 60 * 1000,      // 10 min - keep in cache
      refetchOnWindowFocus: false,  // Don't refetch on focus
      refetchOnMount: false,        // Use cached data
    },
  },
});
```

### Prefetch on Hover

```typescript
// Prefetch event details on hover
function prefetchEventDetails(eventId: string) {
  queryClient.prefetchQuery({
    queryKey: ['event', eventId],
    queryFn: () => fetchEventDetails(eventId),
  });
}

// In GraphView
cy.on('mouseover', 'node', (evt) => {
  prefetchEventDetails(evt.target.id());
});
```

---

## 4. Code Splitting & Lazy Loading

### Dynamic Imports

```typescript
// Lazy load heavy components
const GraphView = dynamic(
  () => import('@/components/GraphView'),
  { ssr: false, loading: () => <GraphSkeleton /> }
);

const Timeline = dynamic(
  () => import('@/components/Timeline'),
  { ssr: false }
);
```

### Route-Based Splitting

Next.js automatically splits by route:

```
/graph → graph.chunk.js
/timeline → timeline.chunk.js
/stats → stats.chunk.js
```

---

## 5. Bundle Size Optimization

### Tree Shaking

```typescript
// Don't import entire library
❌ import * as d3 from 'd3';

✅ import { scaleTime, axisBottom } from 'd3-scale';
```

### Analyze Bundle

```bash
npm install -D @next/bundle-analyzer

# next.config.js
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

module.exports = withBundleAnalyzer({});

# Run
ANALYZE=true npm run build
```

**Target:** Main bundle < 200 KB

---

## 6. Debounce User Input

### Search Debouncing

```typescript
import { useDebouncedValue } from '@/hooks/useDebounce';

export function SearchFilter() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebouncedValue(query, 300);

  // Only search after 300ms of no typing
  const { data } = useQuery({
    queryKey: ['search', debouncedQuery],
    queryFn: () => searchEvents(debouncedQuery),
    enabled: debouncedQuery.length > 2,
  });
}
```

### Resize Debouncing

```typescript
useEffect(() => {
  const handleResize = _.debounce(() => {
    cy?.resize();
    cy?.fit();
  }, 200);

  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, [cy]);
```

---

## 7. Memoization

### useMemo for Expensive Calculations

```typescript
const processedNodes = useMemo(() => {
  return nodes.map((node) => ({
    ...node,
    degree: calculateDegree(node, edges),
    centrality: calculateCentrality(node, graph),
  }));
}, [nodes, edges]);
```

### React.memo for Components

```typescript
export const EventCard = React.memo(
  ({ event }: EventCardProps) => {
    return <div>...</div>;
  },
  (prevProps, nextProps) =>
    prevProps.event.id === nextProps.event.id
);
```

---

## 8. Image Optimization

### Next.js Image Component

```typescript
import Image from 'next/image';

<Image
  src="/logo.png"
  width={200}
  height={50}
  alt="FE-EKG Logo"
  priority  // Load immediately
/>
```

---

## 9. Web Workers (Future)

For heavy computations (graph layouts, centrality):

```typescript
// worker.ts
self.onmessage = (e) => {
  const { nodes, edges } = e.data;
  const centrality = computeCentrality(nodes, edges);
  self.postMessage(centrality);
};

// Component
const worker = new Worker(new URL('./worker.ts', import.meta.url));

worker.postMessage({ nodes, edges });
worker.onmessage = (e) => {
  const centrality = e.data;
  updateGraph(centrality);
};
```

---

## 10. Performance Monitoring

### React Query Devtools

```typescript
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

<ReactQueryDevtools initialIsOpen={false} />
```

### Performance Metrics

```typescript
// Measure graph render time
const startTime = performance.now();
cy.layout({ name: 'cose' }).run();
const endTime = performance.now();
console.log(`Layout: ${endTime - startTime}ms`);
```

### Lighthouse Audit

```bash
npm install -g lighthouse

lighthouse http://localhost:3000/graph --view
```

**Targets:**
- Performance: 90+
- Accessibility: 95+
- Best Practices: 90+
- SEO: 90+

---

## Performance Checklist

### Initial Load
- [ ] Main bundle < 200 KB
- [ ] First Contentful Paint < 1.5s
- [ ] Time to Interactive < 3s

### Graph Rendering
- [ ] 100 nodes render in < 500ms
- [ ] 1000 nodes render in < 2s
- [ ] Pan/zoom at 60 FPS

### API
- [ ] Paginated requests < 200ms
- [ ] Time-window filter < 100ms (backend optimized)
- [ ] Cached stats < 10ms (backend optimized)

### User Experience
- [ ] Search debounced (300ms)
- [ ] Hover tooltips instant
- [ ] Layout changes smooth (500ms animation)

---

**Status:** Optimization strategies documented ✅
**Next:** See STATE_MANAGEMENT_GUIDE.md for state patterns
