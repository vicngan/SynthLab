# SynthLab Themed UI Guide

**Version:** 2.0
**Created:** 2026-01-19
**File:** `app_theme.py`

---

## 🎨 Design Features

### Color Scheme
- **Primary Color:** Purple (#9b59b6)
- **Secondary Color:** Red (#e74c3c)
- **Accent Color:** Blue (#3498db)
- **Gradient:** Purple to Red

### Theme Support
- ✅ **Light Theme** (default)
  - Background: #f8f9fa (soft gray)
  - Cards: White (#ffffff)
  - Text: Dark gray (#2d3436)

- ✅ **Dark Theme** (toggle button)
  - Background: #1a1a2e (navy blue)
  - Cards: #0f3460 (dark blue)
  - Text: White (#ffffff)

---

## 🧩 UI Components

### 1. Top Navigation Bar
```
┌─────────────────────────────────────────────────────────────┐
│ 🧬 SynthLab                [🔍 Search bar...]     [Buttons]  │
│ Privacy-Safe Synthetic Data Platform                         │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- **Title:** Large, gradient purple-red-blue text
- **Subtitle:** "Privacy-Safe Synthetic Data Platform"
- **Search Bar:** Pill-shaped with purple border, 500px wide
- **Menu Buttons:** Pill-shaped (Generate, Privacy, Docs)
- **Border:** 3px solid purple bottom border
- **Theme Toggle:** "🌓 Theme" button in top-right

---

### 2. Sidebar (Highlighted Border)

```
┌─────────────┐
│   👤        │ ← User profile card
│  Admin      │
│  Role: Admin│
└─────────────┘

⚙️ Synthesis Settings
• Method: CTGAN
• Rows: 1000

🔒 Privacy Controls
• Enable DP: ☑
• ε: 1.0
• 🔒 Strong Privacy

📊 Privacy Metrics
• k-anonymity: 3
• l-diversity: 2
• t-closeness: 0.2

☑ Apply Constraints
```

**Features:**
- **Border:** 4px solid purple right border
- **Shadow:** Purple glow
- **Profile Card:** White card with purple border
- **Toggle Switches:** Modern Streamlit toggles
- **Privacy Indicator:** Pill-shaped badge (green/blue/orange)

---

### 3. Main Content Area

**Tabs (Pill-shaped):**
```
┌──────────┐  ┌─────────┐  ┌───────┐  ┌───────┐
│🎨 Generate│  │🔒 Privacy│  │💾 Cache│  │👥 Users│
└──────────┘  └─────────┘  └───────┘  └───────┘
  (active)      (inactive)   (inactive) (inactive)
```

- Active: Purple-red gradient background, white text
- Inactive: White background, purple border
- Hover: Slight lift, purple tint

---

### 4. Metric Cards

```
┌─────────────────┐
│  PRIVACY SCORE  │ ← Label (uppercase)
│                 │
│      98%        │ ← Value (large, bold)
│                 │
│   ✓ No leaks    │ ← Delta (smaller)
└─────────────────┘
```

**Gradient Options:**
- **Default:** Purple → Red
- **Success:** Green → Blue
- **Warning:** Orange → Red

**Effects:**
- Shadow: Purple glow
- Hover: Scale up 1.05x

---

### 5. Info Boxes

**Success Box:**
```
┌──────────────────────────────────────┐
│ ✅ Success! Generated 1,000 rows     │ ← Green-blue gradient
└──────────────────────────────────────┘
```

**Warning Box:**
```
┌──────────────────────────────────────┐
│ ⚠️ Risk: 5 exact matches. Enable DP  │ ← Yellow-orange gradient
└──────────────────────────────────────┘
```

**Error Box:**
```
┌──────────────────────────────────────┐
│ ❌ Error: Failed to load data        │ ← Red gradient
└──────────────────────────────────────┘
```

**Info Box:**
```
┌──────────────────────────────────────┐
│ ℹ️ Generate data first to analyze    │ ← Blue-purple gradient
└──────────────────────────────────────┘
```

All have 4px left border in accent color.

---

### 6. Buttons (Pill-shaped)

**Primary Button:**
```
┌───────────────────────────┐
│ 🚀 Generate Synthetic Data │ ← Purple-red gradient, white text
└───────────────────────────┘
```

**Secondary Button:**
```
┌─────────────┐
│   Generate  │ ← Transparent, purple border
└─────────────┘
```

**Hover Effects:**
- Lift up 2px
- Shadow increases
- Purple glow

---

### 7. File Uploader

```
┌────────────────────────────────────────┐
│                                        │
│   Drop CSV file here or click to      │ ← 3px dashed purple border
│           browse                       │    Rounded 20px
│                                        │
└────────────────────────────────────────┘
```

**Hover:**
- Border changes to red
- Background: Light purple tint

---

### 8. Data Tables

```
┌───────────────────────────────────────┐
│ Column 1  │ Column 2  │ Column 3      │
├───────────┼───────────┼───────────────┤ ← Purple border
│ Value     │ Value     │ Value         │
│ ...       │ ...       │ ...           │
└───────────────────────────────────────┘
```

- Border: 2px solid purple
- Rounded corners: 15px

---

## 🔄 Theme Toggle

**Location:** Top-right corner
**Button:** "🌓 Theme"

**How it works:**
1. Click theme button
2. `st.session_state.theme` switches between 'light' and 'dark'
3. Page reloads with new theme
4. All colors update automatically

---

## 📱 Responsive Design

**Desktop (>1200px):**
- Full sidebar (expanded)
- 4-column metric grids
- Wide search bar (500px)

**Tablet (768px-1200px):**
- Collapsible sidebar
- 2-column grids
- Narrower search bar

**Mobile (<768px):**
- Hidden sidebar (hamburger menu)
- Single column
- Stacked buttons

---

## 🎯 User Experience Features

### Visual Hierarchy
1. **Top Nav:** Purple border draws eye to title
2. **Sidebar:** Purple highlight shows it's important
3. **Metric Cards:** Gradient backgrounds = key info
4. **Buttons:** Pill shape = call-to-action

### Consistency
- **All buttons:** Pill-shaped
- **All cards:** 20px border-radius
- **All borders:** Purple (#9b59b6)
- **All gradients:** Purple → Red

### Feedback
- **Hover:** All interactive elements lift/glow
- **Loading:** Purple progress bar
- **Success:** Green-blue info boxes
- **Error:** Red info boxes

---

## 🚀 Getting Started

### 1. Open in Browser
```
http://localhost:8501
```

### 2. You'll See

**Login Page:**
- Large SynthLab title (purple gradient)
- White card with purple border
- Modern input fields
- Pill-shaped "Sign In" button

**After Login:**
- Top nav with search bar
- Theme toggle (top-right)
- Highlighted sidebar (purple border)
- 4 pill-shaped tabs

### 3. Try the Features

**Upload Data:**
- Drag-drop or click to browse
- Dashed purple border shows drop zone
- Hover for red highlight

**Generate:**
- Click purple gradient button
- Watch purple progress bar
- See gradient metric cards

**Toggle Theme:**
- Click 🌓 Theme button
- Watch UI flip to dark mode
- All purple accents remain

---

## 🎨 Color Psychology

**Purple (#9b59b6):**
- Represents: Creativity, wisdom, innovation
- Perfect for: Synthetic data (creative generation)
- Feeling: Premium, professional

**White (#ffffff):**
- Represents: Clarity, simplicity, cleanliness
- Perfect for: Data visualization
- Feeling: Trustworthy, modern

**Gradient (Purple → Red → Blue):**
- Dynamic, energetic
- Catches attention
- Modern, tech-forward

---

## 🔧 Customization

### Change Primary Color

In `app_theme.py`, find:
```python
border_color = "#9b59b6"  # Purple
```

Change to:
```python
border_color = "#3498db"  # Blue
border_color = "#e74c3c"  # Red
border_color = "#2ed573"  # Green
```

### Change Gradient

Find:
```css
background: linear-gradient(135deg, #9b59b6 0%, #e74c3c 100%);
```

Change to your preferred colors!

---

## 📊 Comparison: Old vs New UI

| Feature | Old (app_enhanced.py) | New (app_theme.py) |
|---------|----------------------|-------------------|
| **Top Nav** | ❌ None | ✅ Search + Menu |
| **Theme** | ❌ Light only | ✅ Light/Dark toggle |
| **Sidebar** | ⚠️ Basic | ✅ Highlighted purple border |
| **Buttons** | ⚠️ Rectangular | ✅ Pill-shaped |
| **Colors** | ⚠️ Generic | ✅ Purple & white branding |
| **Title** | ⚠️ Small | ✅ Large gradient |
| **Search** | ❌ None | ✅ Pill-shaped bar |
| **Cards** | ⚠️ Basic | ✅ Bordered, animated |
| **Metrics** | ⚠️ Standard | ✅ Gradient with hover |

---

## ✨ Summary

**SynthLab Themed UI provides:**
- 🎨 Beautiful purple & white design
- 🌓 Light/Dark theme support
- 🔍 Integrated search bar
- 💊 Pill-shaped buttons and tabs
- 🔲 Highlighted sidebar border
- 📊 Gradient metric cards
- ✨ Smooth animations and transitions
- 🎯 Consistent, modern design language

**Perfect for:**
- Professional presentations
- Academic research portals
- Enterprise deployments
- Healthcare institutions

---

**Your beautiful UI is now live at:**
**http://localhost:8501**

Enjoy the new look! 🎉
