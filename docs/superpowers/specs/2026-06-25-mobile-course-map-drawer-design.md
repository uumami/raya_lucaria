---
id: superpowers-mobile-course-map-drawer-design
title: Mobile Course Map Drawer Design
status: approved
date: 2026-06-25
workflow: superpowers
---
# Mobile Course Map Drawer Design

## Purpose

Make the tablet and mobile course map feel like an intentional reader drawer instead of a clipped desktop panel. The drawer must help students orient quickly without breaking article-first reading, and it must remain static, local, non-persistent, and accessible.

## Scope

This loop updates only the course-map drawer shell on viewports below the desktop shell breakpoint. It keeps the existing static navigation data, workspace shortcuts, filter, section controls, focus trap, and Escape/backdrop close behavior. It does not add progress, recommendations, personalization, browser-side MathJax, external assets, external requests, storage-backed course state, or a new source/artifact schema.

## Reader Behavior

On tablet and mobile, the command-bar Course map control opens a full-height drawer with a visible drawer header, a small visual grip, a Course map title, the current structural page position when available, and a clear close button. The drawer uses a comfortable width bounded by the viewport, rounded right-side edges, stable internal scrolling, and a dimmed blurred backdrop. The article and right learning rail remain the normal reading flow when the drawer is closed.

Opening the drawer locks background page scrolling and marks the root with explicit transient drawer and scroll-lock state. Closing through the close button, Escape, or backdrop removes the lock, hides the drawer from keyboard and assistive navigation, and restores focus to the control that opened it when possible. Resizing back to desktop also clears drawer state and scroll lock.

## Accessibility And State

The drawer remains a native `nav` region with `aria-label="Course map"`. Closed mobile drawer content is inert, `aria-hidden`, and removed from sequential keyboard navigation. Open drawer content is focusable and trapped until the drawer closes. The drawer chrome must be real HTML, not only pseudo-element decoration, so assistive technologies and browser tests can inspect it.

Course-map drawer state is volatile display state. The shell must not use `localStorage` or `sessionStorage` for drawer openness, scroll position, filter text, section expansion, or reader progress.

## Styling

CSS stays in the static renderer resource and uses existing skin tokens. The implementation may add drawer-specific classes for chrome, grip, title, and subtitle. The drawer overlay should feel smoother through transition-ready opacity, transform, border, and shadow rules, while honoring reduced-motion preferences.

## Documentation

Update the learning renderer contract and student/agent role docs in English and Spanish. Documentation should state that the mobile course map is a temporary drawer, background scrolling is paused while open, and the close paths are the close button, backdrop, and Escape.

## Testing

Add browser-driven e2e coverage against the render fixture. The focused test must verify drawer chrome exists, the drawer opens from the command bar on a mobile viewport, root scroll-lock state and CSS overflow are applied while open, the backdrop is visible and styled as an overlay, the drawer is bounded by viewport width, and Escape/backdrop close removes scroll lock and restores focus. Contract tests should verify the generated static HTML includes drawer chrome and the static resources include scroll-lock styling.
