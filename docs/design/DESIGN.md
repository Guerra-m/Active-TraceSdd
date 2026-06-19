---
name: Activia-Trace Design System
colors:
  surface: '#fbf9fa'
  surface-dim: '#dbd9db'
  surface-bright: '#fbf9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f3f4'
  surface-container: '#efedef'
  surface-container-high: '#e9e8e9'
  surface-container-highest: '#e4e2e3'
  on-surface: '#1b1c1d'
  on-surface-variant: '#43474c'
  inverse-surface: '#303032'
  inverse-on-surface: '#f2f0f2'
  outline: '#74777d'
  outline-variant: '#c4c6cd'
  surface-tint: '#4e6073'
  primary: '#162839'
  on-primary: '#ffffff'
  primary-container: '#2c3e50'
  on-primary-container: '#96a9be'
  inverse-primary: '#b5c8df'
  secondary: '#4b6076'
  on-secondary: '#ffffff'
  secondary-container: '#cce2fc'
  on-secondary-container: '#50657b'
  tertiary: '#362308'
  on-tertiary: '#ffffff'
  tertiary-container: '#4e381c'
  on-tertiary-container: '#c1a17d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d1e4fb'
  primary-fixed-dim: '#b5c8df'
  on-primary-fixed: '#091d2e'
  on-primary-fixed-variant: '#36485b'
  secondary-fixed: '#cfe5ff'
  secondary-fixed-dim: '#b3c9e2'
  on-secondary-fixed: '#051d30'
  on-secondary-fixed-variant: '#34495e'
  tertiary-fixed: '#ffddb7'
  tertiary-fixed-dim: '#e3c19b'
  on-tertiary-fixed: '#291802'
  on-tertiary-fixed-variant: '#5a4225'
  background: '#fbf9fa'
  on-background: '#1b1c1d'
  surface-variant: '#e4e2e3'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  title-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  label-caps:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 16px
    letterSpacing: 0.05em
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  table-cell-x: 12px
  table-cell-y: 8px
---

## Brand & Style
The design system is engineered for high-utility B2B academic management, prioritizing cognitive clarity and long-form data processing. The brand personality is authoritative yet unobtrusive, drawing inspiration from high-performance developer tools and modern fintech interfaces. 

The aesthetic follows a **Modern Corporate** approach with a focus on **Information Density**. It utilizes a refined grayscale palette and precision-engineered typography to ensure that complex academic hierarchies and administrative workflows remain legible. The goal is to evoke a sense of reliability and systematic order, reducing the "noise" typically found in legacy educational software.

## Colors
The palette is anchored by Petroleum and Grayish blues to establish a professional, sober foundation. 

- **Primary & Secondary:** Used for navigation sidebars, headers, and structural elements to provide a weighted frame for content.
- **Background:** The base layer uses a specific off-white (#F7F8FA) to mitigate screen glare during extended administrative sessions. 
- **Accent:** A muted Teal (#0D9488) is reserved strictly for primary actions and "Success" states that require user attention.
- **Semantic Tones:** These are desaturated to prevent "alert fatigue." Red, Amber, and Green tones are adjusted to a lower chroma, ensuring they sit comfortably within dense tables without overpowering the text.

## Typography
This design system utilizes **Inter** for its exceptional legibility in UI environments. To handle the density of academic data, the scale is intentionally compact.

- **Primary Scale:** The standard body size is set to 14px, with a 13px variant for sidebars and secondary metadata.
- **Data Tables:** For ID numbers, grades, and timestamps, **JetBrains Mono** is employed at small scales to ensure character distinction and alignment.
- **Hierarchy:** Use semi-bold (600) for headers to provide clear section breaks without requiring massive font sizes.

## Layout & Spacing
The layout follows a **Fluid Grid** model optimized for wide-screen monitors commonly used in administrative offices. 

- **Density:** We utilize a 4px baseline grid. Content-heavy views (like student rosters or grade books) should use "Compact" spacing (8px gutters) to maximize information above the fold.
- **Structure:** A persistent left-hand navigation rail (240px) provides the primary anchor.
- **Breakpoints:** 
  - Desktop: 1280px+ (Full 12-column)
  - Tablet: 768px - 1279px (8-column, sidebar collapses to icons)
  - Mobile: Under 768px (1-column, bottom navigation or drawer)

## Elevation & Depth
Depth is communicated through **Tonal Layers** rather than heavy shadows. This maintains a flat, modern profile that feels integrated into the screen.

- **Level 0 (Base):** The #F7F8FA background.
- **Level 1 (Cards/Surface):** Pure #FFFFFF with a subtle 1px border (#E2E8F0). No shadow.
- **Level 2 (Popovers/Modals):** Pure #FFFFFF with a soft, 8% opacity neutral shadow and a 1px border. 
- **Active States:** Subtle inset shadows or slight shifts in background tint (e.g., #EDF2F7) indicate pressed or active navigation items.

## Shapes
The shape language is disciplined and geometric. 
- **Standard Radius:** 4px (Soft) is the default for buttons, input fields, and small containers. This provides just enough approachable warmth without losing the "professional" edge.
- **Large Components:** Modals and main content cards may use up to 8px (rounded-lg) for clear containment.
- **Strictness:** Icons and decorative elements should maintain sharp corners or very minimal rounding to align with the technical nature of the platform.

## Components
- **Buttons:** Primary buttons use the Teal accent. Secondary buttons use a white background with a #CBD5E1 border. Text is always medium weight.
- **Data Tables:** The core of the system. Use alternating row stripes (Zebra striping) with a very faint gray (#F1F5F9). Headers are sticky, using `label-caps` typography with a bottom border.
- **Input Fields:** Use a 1px border. On focus, the border shifts to the primary petroleum blue with a soft blue outer glow (2px).
- **Status Chips:** Small, low-contrast pills. For example, a "Pending" status uses a soft amber background (#FEF3C7) with dark amber text (#92400E).
- **Cards:** Used for dashboard widgets. They should feature a header row with a 1px bottom divider to separate titles from the data visualization or list below.
- **Breadcrumbs:** Essential for academic hierarchies (Department > Course > Section). Use `body-sm` with a chevron separator.