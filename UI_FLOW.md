# 🎨 UI/UX Flow Guide

## Visual Design & Interaction Patterns

---

## 🌟 Landing Page

```
┌─────────────────────────────────────────────────────────────┐
│  Rigveda Word Relationships                                 │
│  Explore connections between entities in the Rigveda        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│     ┌──────┐  • • • • • • • • • • • • • • • •             │
│     │Agni ●│  • • • • • • • • • • • • • • • •             │
│     └──────┘                                                │
│                  • • • • • • • • • • • • • • • •            │
│  • • • • • • ┌──────┐    ┌──────┐                         │
│  • • • • • • │Indra●│    │Soma ●│  • • • • • • •         │
│  • • • • • • └──────┘    └──────┘  • • • • • • •         │
│                                                             │
│       ┌──────┐           • • • • • • • • • •               │
│       │Vāyu ●│           • • • • • • • • • •               │
│       └──────┘   ┌──────────┐                              │
│                  │Sarasvatī●│      • • • • • • •          │
│  • • • • • • •   └──────────┘      • • • • • • •          │
│  • • • • • • •                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Features:
- White dotted background (grid pattern)
- Bubbles float gently with physics simulation
- Size = Frequency (bigger = more mentions)
- Colors: 🟡 Gold (deity), 🟢 Green (attribute), 🔵 Blue (rishi)
- Hover shows: Name, Type, Frequency
```

---

## 🎯 Entity Selection State

```
┌─────────────────────────────────────────────────────────────┐
│  Rigveda Word Relationships                                 │
│  Explore connections between entities in the Rigveda        │
├─────────────────────────────────────────────────────────────┤
│                                              ┌──────────────┐│
│                                              │  Agni        ││
│                 ┌────┐                       │  ───────────  │
│                 │Soma│                       │ Type: deity  ││
│                 └────┘                       │ Freq: 523    ││
│        ┌────┐     \                          │              ││
│        │Vāyu│      \   ┌───────┐            │ Relationships││
│        └────┘       \  │ AGNI ●│            │              ││
│                      \ │       │            │ • Indra 85%  ││
│                       \└───────┘            │ • Soma  72%  ││
│           ┌──────┐   /    |    \           │ • Vāyu  68%  ││
│           │Indra │  /     |     \          │ • Fire  54%  ││
│           └──────┘ /      |      \         │              ││
│                ┌────┐  ┌────┐  ┌──────┐    │              ││
│                │Fire│  │Dawn│  │Heaven│    │              ││
│                └────┘  └────┘  └──────┘    │              ││
│                                              │              ││
│                                              │      [×]     ││
│                                              └──────────────┘│
└─────────────────────────────────────────────────────────────┘

Features:
- Selected bubble moves to center, enlarges
- Related entities arrange in circle around it
- Lines connect center to related entities
- Line thickness = Relationship strength
- Side panel slides in from right
- Shows top relationships with score bars
- Click outside or × to reset
```

---

## 🔗 Relationship Detail State

```
┌─────────────────────────────────────────────────────────────┐
│  Rigveda Word Relationships                                 │
│  Explore connections between entities in the Rigveda        │
├─────────────────────────────────────────────────────────────┤
│                                              ┌──────────────┐│
│                                              │← Back        ││
│                                              │              ││
│                ┌────┐                        │ Relationship ││
│                │Soma│  ═══════════          │ with Indra   ││
│                └────┘                        │              ││
│                         ┌───────┐            │ Scores:      ││
│                         │ AGNI ●│            │ Overall: 85% ││
│                         │       │            │ ──────────── ││
│                         └───────┘            │              ││
│                            ║                 │ Conjunction: ││
│                            ║                 │ 92% ████████ ││
│                            ║                 │              ││
│           ┌──────┐         ║                 │ Hymn Co-occ: ││
│           │INDRA●│═════════╝                 │ 78% ██████   ││
│           └──────┘                           │              ││
│                                              │ Indirect:    ││
│                                              │ 65% █████    ││
│                                              │              ││
│                                              │ References:  ││
│                                              │ Book 1, H 12 ││
│                                              │ Book 2, H 45 ││
│                                              │ Book 3, H 78 ││
│                                              │              ││
│                                              │ Examples:    ││
│                                              │ "Agni and    ││
│                                              │  Indra..."   ││
│                                              └──────────────┘│
└─────────────────────────────────────────────────────────────┘

Features:
- Both entities highlighted
- Thick line between them (score-based)
- Other relationships fade
- Score breakdown visible
- Component scores shown with bars
- Hymn references listed
- Conjunction examples quoted
- Back button returns to relationship list
```

---

## 🎭 Animation States

### 1. Initial Load Animation
```
Bubbles fade in from center
  ↓
Expand to random positions
  ↓
Begin gentle floating
  ↓
Apply force simulation
  ↓
Settle into equilibrium
```

### 2. Selection Animation
```
Click detected
  ↓
Selected bubble scales up (1.5x)
  ↓
Other bubbles fade (opacity 0.3)
  ↓
Selected moves to center (smooth transition)
  ↓
Related bubbles appear around circle
  ↓
Lines draw from center outward
  ↓
Side panel slides in (spring animation)
```

### 3. Deselection Animation
```
Click × or outside
  ↓
Side panel slides out
  ↓
Lines fade out
  ↓
Related bubbles fade
  ↓
Selected bubble shrinks
  ↓
All bubbles fade in
  ↓
Resume force simulation
  ↓
Return to initial state
```

---

## 🎨 Color Scheme

### Entity Type Colors
```
Deities:    #FFD700 (Gold)        ●
Attributes: #32CD32 (Lime Green)  ●
Rishis:     #4169E1 (Royal Blue)  ●
```

### UI Colors
```
Background:  #FFFFFF (White)
Dots:        #DDDDDD (Light Gray)
Header:      Linear gradient (#667eea → #764ba2)
Panel:       rgba(255,255,255,0.98) with shadow
Text:        #333333 (Dark Gray)
Accent:      #667eea (Purple-Blue)
Lines:       #999999 (Gray, varying thickness)
```

### Interactive States
```
Hover:       Scale 1.1, Glow effect
Selected:    Scale 1.5, Full opacity
Unselected:  Opacity 0.3
Related:     Opacity 0.7, Stroke highlight
```

---

## 📐 Layout Specifications

### Bubble Sizes
```
Minimum Radius: 15px
Maximum Radius: 50px
Formula: radius = 15 + (normalized_frequency * 35)
```

### Force Simulation
```
Charge:     -100 (repulsion)
Center:     (width/2, height/2)
Collision:  radius + 5px padding
```

### Relationship Circle
```
Radius:       min(width, height) / 3
Arrangement:  Equal angles (2π / count)
```

### Side Panel
```
Width:     400px
Position:  Fixed right
Height:    100vh
Animation: Slide from right (spring damping: 20)
```

---

## 🖱️ User Interactions

### Mouse Events
```
Hover Bubble:
  → Scale up slightly
  → Show tooltip (top-right corner)
  → Display: name, type, frequency

Click Bubble (unselected):
  → Select and center
  → Load relationships
  → Show side panel

Click Bubble (selected, center):
  → Deselect
  → Return to overview

Click Related Bubble:
  → Show relationship details
  → Update side panel

Click Outside:
  → Deselect
  → Reset view

Click × Button:
  → Close side panel
  → Deselect entity
```

### Keyboard Events (Future)
```
Escape:        Deselect
Arrow Keys:    Navigate related entities
Enter:         Select focused entity
Tab:           Cycle through entities
```

---

## 📱 Responsive Design

### Desktop (> 1024px)
```
- Full side panel (400px)
- Large bubbles
- All features visible
```

### Tablet (768px - 1024px)
```
- Narrower side panel (300px)
- Medium bubbles
- Scrollable panel content
```

### Mobile (< 768px)
```
- Full-screen panel overlay
- Smaller bubbles
- Touch-optimized
- Swipe to close panel
```

---

## ⚡ Performance Optimizations

### D3 Simulation
```
- Alpha decay: 0.02 (faster settling)
- Max iterations: Limited
- Collision detection: Optimized quadtree
- Render throttling: RequestAnimationFrame
```

### React Rendering
```
- Memo for expensive components
- Callback refs for D3 integration
- Debounced resize handlers
- Lazy load relationship data
```

### Visual Smoothness
```
- CSS transforms (GPU accelerated)
- Will-change hints
- Backface-visibility optimization
- Smooth spring animations (Framer Motion)
```

---

## 🎪 Special Effects

### Dotted Background
```css
background-image: radial-gradient(circle, #ddd 1px, transparent 1px);
background-size: 30px 30px;
```

### Bubble Glow (on hover)
```css
box-shadow: 0 0 20px rgba(color, 0.5);
filter: brightness(1.1);
```

### Relationship Lines
```
- Thickness: score * 5px
- Opacity: score * 0.8
- Color: Gradient based on entity types
```

### Panel Slide Animation
```javascript
initial={{ x: 400 }}
animate={{ x: 0 }}
exit={{ x: 400 }}
transition={{ type: 'spring', damping: 20 }}
```

---

## 🎯 Accessibility Considerations

### Color Contrast
- Text on backgrounds: WCAG AA compliant
- Entity colors: Distinguishable patterns

### Keyboard Navigation
- Tab order: Logical flow
- Focus indicators: Visible outlines

### Screen Readers
- ARIA labels on interactive elements
- Semantic HTML structure

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  /* Disable animations */
  * { animation: none !important; }
}
```

---

**Design Philosophy**: Clean, modern, intuitive, and respectful of the sacred texts while making them accessible through technology.
