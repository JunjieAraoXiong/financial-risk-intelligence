# FE-EKG UI/UX Design System

Design tokens, color palette, typography, and component styling.

---

## Color Palette

### Primary Colors (from backend docs)

```typescript
// src/lib/constants.ts
export const COLORS = {
  // Relationship types
  hasActor: '#10b981',      // Emerald - entity performs action
  hasTarget: '#ef4444',     // Red - entity affected
  involves: '#3b82f6',      // Blue - general involvement
  relatedTo: '#a855f7',     // Purple - entity connections
  evolvesTo: '#f59e0b',     // Orange - event evolution

  // Entity types
  bank: '#3b82f6',          // Blue
  regulator: '#8b5cf6',     // Purple
  investment_bank: '#ec4899', // Pink

  // Event severity
  high: '#ef4444',          // Red
  medium: '#f59e0b',        // Amber
  low: '#10b981',           // Emerald

  // UI elements
  background: '#f8fafc',
  surface: '#ffffff',
  border: '#e2e8f0',
  text: {
    primary: '#0f172a',
    secondary: '#64748b',
    tertiary: '#94a3b8',
  },
};
```

### Tailwind Config Extension

```typescript
// tailwind.config.ts
theme: {
  extend: {
    colors: {
      emerald: {
        DEFAULT: '#10b981',
        50: '#ecfdf5',
        500: '#10b981',
        600: '#059669',
      },
      indigo: {
        DEFAULT: '#6366f1',
        50: '#eef2ff',
        500: '#6366f1',
        600: '#4f46e5',
      },
      // ... other colors
    },
  },
}
```

---

## Typography

### Font Family

```typescript
export const TYPOGRAPHY = {
  fontFamily: {
    sans: ['Inter', 'system-ui', 'sans-serif'],
    mono: ['Monaco', 'Courier New', 'monospace'],
  },

  sizes: {
    xs: '0.75rem',     // 12px
    sm: '0.875rem',    // 14px
    base: '1rem',      // 16px
    lg: '1.125rem',    // 18px
    xl: '1.25rem',     // 20px
    '2xl': '1.5rem',   // 24px
    '3xl': '1.875rem', // 30px
  },

  weights: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
};
```

### Usage

```tsx
<h1 className="text-3xl font-bold text-gray-900">Title</h1>
<p className="text-base text-gray-600">Body text</p>
<span className="text-sm text-gray-500">Caption</span>
```

---

## Spacing

### Base Grid: 8px

```typescript
export const SPACING = {
  base: 8,

  components: {
    card: 16,      // 2 × base
    panel: 24,     // 3 × base
    section: 32,   // 4 × base
    page: 48,      // 6 × base
  },

  gaps: {
    tight: 4,
    normal: 8,
    relaxed: 16,
    loose: 24,
  },
};
```

### Tailwind Classes

- `p-4` = 16px (card padding)
- `p-6` = 24px (panel padding)
- `p-8` = 32px (section padding)
- `gap-4` = 16px (grid gap)

---

## Component Styles

### Card

```tsx
<div className="bg-white rounded-lg shadow-lg p-6 space-y-4">
  <h3 className="text-lg font-semibold text-gray-900">Card Title</h3>
  <p className="text-sm text-gray-600">Card content</p>
</div>
```

### Button

```tsx
// Primary
<button className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 font-medium">
  Primary Button
</button>

// Secondary
<button className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 font-medium">
  Secondary Button
</button>

// Danger
<button className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 font-medium">
  Delete
</button>
```

### Input

```tsx
<input
  type="text"
  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
  placeholder="Search..."
/>
```

### Badge

```tsx
// Event type badge
<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
  Merger
</span>

// Severity badge
<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
  High
</span>
```

---

## Graph Visualization Styles

### Cytoscape.js Stylesheet

```typescript
// src/lib/cytoscape/styles.ts
export const GRAPH_STYLES = [
  {
    selector: 'node',
    style: {
      'background-color': '#10b981',
      'border-width': 2,
      'border-color': '#ffffff',
      'label': 'data(label)',
      'font-size': 11,
      'font-weight': 600,
      'text-outline-width': 2,
      'text-outline-color': '#1e293b',
      'color': '#ffffff',
      'text-valign': 'center',
      'text-halign': 'center',
    },
  },
  {
    selector: 'node:selected',
    style: {
      'border-width': 3,
      'border-color': '#fbbf24',
      'box-shadow': '0 0 20px rgba(251, 191, 36, 0.6)',
    },
  },
  {
    selector: 'edge',
    style: {
      'width': 2,
      'line-color': '#6366f1',
      'target-arrow-color': '#6366f1',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'opacity': 0.6,
    },
  },
];
```

---

## Layout Patterns

### Dashboard Layout

```tsx
<div className="h-screen flex bg-gray-50">
  {/* Sidebar */}
  <aside className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
    <div className="p-6 space-y-6">
      {/* Filters */}
    </div>
  </aside>

  {/* Main content */}
  <main className="flex-1 flex flex-col">
    {/* Header */}
    <header className="h-16 bg-white border-b border-gray-200 flex items-center px-6">
      <h1 className="text-xl font-bold">Graph View</h1>
    </header>

    {/* Graph */}
    <div className="flex-1">
      {/* GraphView component */}
    </div>

    {/* Timeline */}
    <div className="h-32 bg-white border-t border-gray-200">
      {/* Timeline component */}
    </div>
  </main>

  {/* Detail panel (conditional) */}
  {selectedNode && (
    <aside className="w-96 bg-white border-l border-gray-200 overflow-y-auto">
      {/* EventCard component */}
    </aside>
  )}
</div>
```

---

## Animations

### Transitions

```typescript
export const ANIMATIONS = {
  duration: {
    fast: 150,
    normal: 300,
    slow: 500,
  },

  easing: {
    ease: 'cubic-bezier(0.4, 0, 0.2, 1)',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
  },
};
```

### Usage

```tsx
// Slide-in panel
<div className="transform transition-transform duration-300 ease-out translate-x-0">
  {/* Content */}
</div>

// Fade
<div className="transition-opacity duration-200 opacity-100">
  {/* Content */}
</div>

// Scale on hover
<button className="transform transition-transform hover:scale-105">
  Click me
</button>
```

---

## Responsive Design

### Breakpoints (Tailwind default)

- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

### Mobile-First Approach

```tsx
<div className="w-full md:w-1/2 lg:w-1/3">
  {/* Full width on mobile, half on tablet, third on desktop */}
</div>

<div className="hidden lg:block">
  {/* Hidden on mobile, visible on desktop */}
</div>

<div className="flex flex-col lg:flex-row">
  {/* Stack on mobile, row on desktop */}
</div>
```

---

## Accessibility

### Color Contrast

All text meets WCAG AA standards:
- Large text (18px+): 3:1 minimum
- Normal text: 4.5:1 minimum

### Focus States

```tsx
<button className="focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2">
  Accessible Button
</button>
```

### ARIA Labels

```tsx
<button aria-label="Close panel" onClick={onClose}>
  <XIcon className="w-5 h-5" />
</button>

<input
  aria-label="Search events"
  placeholder="Search..."
/>
```

---

## Dark Mode (Future)

```typescript
// Prepare for dark mode
export const COLORS_DARK = {
  background: '#0f172a',
  surface: '#1e293b',
  border: '#334155',
  text: {
    primary: '#f8fafc',
    secondary: '#cbd5e1',
    tertiary: '#64748b',
  },
};
```

---

**Status:** Design system documented ✅
**Next:** See GRAPH_INTERACTION_GUIDE.md for UX patterns
