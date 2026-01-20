# SynthLab Clean Minimal UI - Design Guide

**Version:** 3.0
**Created:** 2026-01-19
**File:** `app_theme.py`

---

## 🎨 Design Philosophy

Clean, minimal, and professional - inspired by modern web design (similar to Billey theme). Focus on clarity, usability, and simplicity.

---

## 🎯 Key Design Features

### 1. **Clean Color Palette**

**Light Theme (default):**
- Background: `#ffffff` (white)
- Secondary: `#fafafa` (light gray)
- Text Primary: `#1a1a1a` (dark gray/black)
- Text Secondary: `#6b7280` (medium gray)
- Border: `#e5e7eb` (light gray)
- Accent: `#3b82f6` (clean blue)

**Dark Theme:**
- Background: `#0f0f0f` (almost black)
- Secondary: `#1a1a1a` (dark gray)
- Cards: `#1e1e1e` (slightly lighter)
- Text Primary: `#ffffff` (white)
- Text Secondary: `#a0a0a0` (light gray)
- Border: `#333333` (dark gray)
- Accent: `#3b82f6` (blue)

### 2. **Typography**
- **Font:** Inter (modern, clean sans-serif)
- **Fallback:** -apple-system, BlinkMacSystemFont, 'Segoe UI'
- **Weights:** 300, 400, 500, 600, 700
- **Sizes:** Smaller, more refined than previous version

### 3. **Top Navigation**
- **Position:** Sticky to top (top: 0, z-index: 999)
- **Layout:**
  - Left: Logo (🧬 SynthLab)
  - Center: Nav menu (Generate, Privacy, Documentation)
  - Right: Theme toggle button (🌙/☀️)
- **Border:** 1px solid border-color
- **Shadow:** Subtle (0 1px 3px rgba(0,0,0,0.05))

### 4. **Components**

**Buttons:**
- Primary: Blue background, white text
- Border-radius: 8px (not pill-shaped)
- Padding: 0.625rem 1.5rem
- Hover: Slightly darker blue

**Cards:**
- Border: 1px solid border-color
- Border-radius: 12px
- Padding: 1.5rem
- Shadow: Subtle (0 1px 3px rgba(0,0,0,0.05))
- Hover: Slightly larger shadow

**Metric Cards:**
- Clean borders (no gradients)
- Center-aligned text
- Hover: Blue border accent

**Tabs:**
- Underline style (not pill-shaped)
- Active: Blue underline (2px)
- Inactive: Transparent
- Hover: Text color change

**Info Boxes:**
- Left border: 3px solid
- Border-radius: 8px
- Types: Info (blue), Success (green), Warning (orange), Error (red)
- Light theme: Colored backgrounds
- Dark theme: Darker colored backgrounds

---

## 📱 Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│ 🧬 SynthLab    Generate Privacy Documentation    [🌙]  │ ← Sticky top nav
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌────────┐                                            │
│  │Sidebar │  Main Content Area                         │
│  │        │  ┌─────────────────────────────────────┐   │
│  │Profile │  │ Generate | Privacy | Literature |...│   │
│  │        │  ├─────────────────────────────────────┤   │
│  │Settings│  │                                     │   │
│  │        │  │  Tab Content                        │   │
│  │Privacy │  │                                     │   │
│  │        │  │                                     │   │
│  └────────┘  └─────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Tabs

All 5 tabs are included:

1. **Generate** - Upload data and create synthetic datasets
2. **Privacy Analysis** - Analyze privacy metrics
3. **Literature** - Search academic papers (if available)
4. **Cache** - View cached models
5. **Users/Docs** - User management (admin) or documentation

---

## 🎨 vs Previous Purple Theme

| Feature | Purple Theme (v2.0) | Clean Minimal (v3.0) |
|---------|-------------------|---------------------|
| **Colors** | Purple gradients | Neutral (white/gray/blue) |
| **Buttons** | Pill-shaped (50px radius) | Rounded (8px radius) |
| **Tabs** | Pill-shaped with gradients | Underline style |
| **Cards** | Purple borders & shadows | Subtle gray borders |
| **Nav** | Middle of screen | Sticky to top |
| **Font** | Poppins | Inter |
| **Aesthetic** | Bold, colorful | Clean, minimal |

---

## 🚀 Features

### ✓ Theme Toggle
- Button in top-right corner
- Light mode: 🌙 (moon icon)
- Dark mode: ☀️ (sun icon)
- Instant theme switching

### ✓ Responsive Design
- Content wrapper: max-width 1400px
- Centered layout
- Clean spacing

### ✓ All Functionality Preserved
- Synthetic data generation
- Privacy analysis
- Literature search
- Model caching
- User management

### ✓ Lazy Imports
- Modules imported only when needed
- Faster startup time
- Better error handling
- Compatible with Python 3.14

---

## 🔧 Technical Details

### Lazy Import Pattern

Instead of importing all modules at startup (which caused SDV compatibility issues):

```python
# ❌ Old way (imports at startup)
from src.modules.synthesizer import SyntheticGenerator

# ✅ New way (lazy import when needed)
if st.button("Generate"):
    from src.modules.synthesizer import SyntheticGenerator
    generator = SyntheticGenerator()
```

This allows the UI to load even if some dependencies aren't available.

### CSS Architecture

- **Global styles:** Clean, consistent typography
- **Component-specific:** Scoped to Streamlit elements
- **Theme-aware:** All colors defined per theme
- **Minimal shadows:** Subtle depth
- **Clean borders:** 1px solid, rounded corners

---

## 📊 User Experience

### Visual Hierarchy
1. **Top Nav** → Draws eye to navigation
2. **Sidebar** → Settings and controls
3. **Main Content** → Primary focus area
4. **Cards** → Organized information blocks

### Consistency
- All buttons: 8px border-radius
- All cards: 12px border-radius
- All borders: 1px solid
- All shadows: Minimal and consistent

### Feedback
- Hover: All interactive elements respond
- Loading: Blue progress bar
- Success: Green info boxes
- Error: Red info boxes
- Warning: Orange info boxes

---

## 🌐 Browser Compatibility

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Responsive design for all screen sizes

---

## 📝 Usage

### Open in Browser
```bash
http://localhost:8501
```

### Login
```
Username: admin
Password: changeme123
```

### Toggle Theme
Click the 🌙 or ☀️ button in the top-right corner

---

## 🎯 Design Goals Achieved

✅ **Clean & Minimal** - Removed gradients, used neutral colors
✅ **Top Navigation** - Sticky header at very top of screen
✅ **Literature Tab** - Included in all tabs
✅ **Professional** - Modern web design aesthetic
✅ **Functional** - All features working
✅ **Fast** - Lazy imports for better performance

---

## 🔄 Comparison with Reference

Inspired by **Billey theme** screenshot:
- ✅ Clean top navigation bar
- ✅ Minimal color palette
- ✅ Simple, professional aesthetic
- ✅ Modern typography
- ✅ Organized layout
- ✅ Clear visual hierarchy

---

**Your clean, minimal UI is now live at:**
**http://localhost:8501**

Enjoy the new design! ✨
