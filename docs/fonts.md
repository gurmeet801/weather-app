# Font Family Reference

This document describes the font families used in the Optivest Charles Schwab application and how to use them in other applications.

---

## Current Font Stack

```css
font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro', system-ui, sans-serif;
```

This stack uses **native system fonts** for optimal performance and readability across all platforms.

---

## Font by Platform

### iOS / iPhone / iPad
**Font Name:** **SF Pro** (San Francisco Pro)

- Apple's native system font
- Optimized for Retina displays
- Built into all iOS, iPadOS, and macOS devices
- No installation required

**Variants:**
- SF Pro Display (for larger text - headlines, titles)
- SF Pro Text (for body text - paragraphs, UI elements)
- SF Pro Rounded (rounded variant - optional)

**How to use in other apps:**
- **iOS/macOS Native Apps:** Font is automatically available as "San Francisco" or "SF Pro"
- **CSS/Web:** Use `-apple-system` or `'SF Pro'` in font-family
- **Design Tools (Figma, Sketch):** Select "SF Pro Display" or "SF Pro Text"

---

### Android Tablet
**Font Name:** **Roboto**

- Google's native system font
- Optimized for Android devices
- Built into all Android devices
- Clean, modern, geometric sans-serif

**How to use in other apps:**
- **Android Native Apps:** Font is automatically available as "Roboto"
- **CSS/Web:** Use `'Roboto'` in font-family or load from Google Fonts
- **Design Tools:** Download from [Google Fonts](https://fonts.google.com/specimen/Roboto)

---

### Windows Desktop
**Font Name:** **Segoe UI**

- Microsoft's native system font
- Built into Windows Vista and later
- Professional, readable, corporate standard

**How to use in other apps:**
- **Windows Apps:** Font is automatically available as "Segoe UI"
- **CSS/Web:** Use `'Segoe UI'` in font-family
- **Design Tools:** Available on Windows systems by default

---

## System Font Fallback

The CSS property `system-ui` automatically selects the appropriate system font:

- **macOS/iOS:** SF Pro
- **Android:** Roboto
- **Windows:** Segoe UI
- **Linux:** Usually DejaVu Sans or Liberation Sans

---

## How to Use These Fonts in Other Applications

### 1. **Web Browsers / HTML / CSS**

Copy this exact CSS:

```css
font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro', system-ui, sans-serif;
```

Or use the shorter version:

```css
font-family: system-ui, sans-serif;
```

---

### 2. **Microsoft Word / Excel / PowerPoint (Windows)**

1. Open font dropdown
2. Select **Segoe UI**
3. Alternative: Select **Calibri** (similar Microsoft font)

---

### 3. **Microsoft Word / Excel / PowerPoint (Mac)**

1. Open font dropdown
2. Select **San Francisco** or **SF Pro**
3. Alternative: Select **Helvetica Neue**

---

### 4. **Google Docs / Sheets / Slides**

**Best match:** Use **Roboto**

1. Open font dropdown
2. Type "Roboto"
3. Select **Roboto** (it's a Google Font, always available)

---

### 5. **Adobe Photoshop / Illustrator (Mac)**

1. Open font dropdown
2. Search for "San Francisco" or "SF Pro Display"
3. If not available, download from [Apple Developer Fonts](https://developer.apple.com/fonts/)

---

### 6. **Adobe Photoshop / Illustrator (Windows)**

1. Open font dropdown
2. Select **Segoe UI**
3. Alternative: Use **Arial** or **Helvetica**

---

### 7. **Figma / Sketch (Design Tools)**

**Mac users:**
1. Select font: **SF Pro Display** (for headers) or **SF Pro Text** (for body)
2. Font is pre-installed on macOS

**Windows users:**
1. Select font: **Segoe UI**
2. Or upload custom fonts to Figma

**Cross-platform projects:**
1. Use **Inter** font (free, similar to SF Pro)
2. Download from [Google Fonts](https://fonts.google.com/specimen/Inter)

---

### 8. **Mobile Apps (Native Development)**

**iOS (Swift/Objective-C):**
```swift
// Use system font
UIFont.systemFont(ofSize: 16)

// Or specify SF Pro explicitly
UIFont(name: "SFProDisplay-Regular", size: 16)
```

**Android (Kotlin/Java):**
```xml
<!-- Use system font in XML -->
android:fontFamily="sans-serif"

<!-- Or specify Roboto explicitly -->
android:fontFamily="sans-serif"
```

---

## Font Alternatives (If System Fonts Not Available)

If you need a web font that works across all platforms:

### **Recommended: Inter**
- Free, open-source
- Almost identical to SF Pro
- Available on Google Fonts
- Excellent for financial/numerical data

**How to add to web projects:**

```html
<!-- Add to <head> -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap">
```

```css
/* Use in CSS */
font-family: 'Inter', system-ui, sans-serif;
```

---

## Equal-Width Characters for Financial Data

**CRITICAL REQUIREMENT:** All numeric displays (prices, volumes, percentages) MUST use equal-width fonts.

### For Numeric Values

Use `font-variant-numeric: tabular-nums;` to ensure all digits (0-9) have equal width:

```css
.price, .volume, .percentage {
    font-variant-numeric: tabular-nums;
    font-family: var(--font-family-monospace);
}
```

**Why this matters:**
- `0` and `1` have the same width
- Decimal points align vertically in tables
- Numbers don't "jump" when values update in real-time
- Essential for streaming financial data

### For Code and Identifiers

Use monospace fonts for timestamps, ticker symbols, contract IDs:

```css
.timestamp, .ticker-symbol, .contract-id {
    font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
}
```

> **See also:** [UI_STANDARDS.md](UI_STANDARDS.md#equal-width-characters-required-for-financial-data) for complete implementation guidelines.

---

## Font Characteristics

All these fonts share similar characteristics that make them excellent for financial data:

### **SF Pro (Apple)**
- Clean, modern, geometric
- Large x-height (lowercase letters are tall)
- Clear distinction between 0 (zero) and O (letter O)
- Clear distinction between 1 (one) and l (lowercase L)
- 9 weights available (Ultralight to Black)

### **Roboto (Google)**
- Clean, modern, geometric
- Similar proportions to SF Pro
- Slightly wider than SF Pro
- Excellent for on-screen reading
- 6 weights available (Thin to Black)

### **Segoe UI (Microsoft)**
- Clean, professional, corporate
- Slightly warmer than SF Pro
- Excellent readability at small sizes
- Standard in Microsoft Office
- 4 weights available (Regular, Semilight, Semibold, Bold)

---

## Quick Reference Table

| Platform | Primary Font | CSS Property | Installation |
|----------|-------------|--------------|--------------|
| **iPhone** | SF Pro | `-apple-system` | Pre-installed |
| **iPad** | SF Pro | `-apple-system` | Pre-installed |
| **Android** | Roboto | `system-ui` | Pre-installed |
| **Windows** | Segoe UI | `system-ui` | Pre-installed |
| **Mac** | SF Pro | `-apple-system` | Pre-installed |
| **Web (cross-platform)** | Inter | `'Inter'` | [Google Fonts](https://fonts.google.com/specimen/Inter) |

---

## Summary

The font stack we're using prioritizes **native system fonts** for:
- **Fast loading** (no downloads required)
- **Optimal rendering** (designed for each platform)
- **Consistent look** (professional across all devices)
- **Better readability** (especially for financial/numerical data)

For other applications, simply use the native font for your platform:
- **Apple devices:** SF Pro (San Francisco)
- **Android devices:** Roboto
- **Windows devices:** Segoe UI
- **Cross-platform web:** Inter (from Google Fonts)
