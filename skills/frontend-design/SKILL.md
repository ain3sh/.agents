---
name: frontend-design
description: Create distinctive, production-grade web interfaces with bold composition (typography, color, layout, atmosphere) that avoid generic AI aesthetics. Use when building components, pages, or applications and the visual direction is up to you. Includes 10 ready-made themes for consistent styling. Hands off to motion-polish for interaction craft.
---

This skill guides creation of distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

**Use this skill when the visual direction is yours to set.** When the user is working inside an established design system, brand kit, or strict component library (shadcn defaults, Material UI, an internal system), defer to those constraints rather than inventing a new aesthetic; the "pick an extreme" guidance below will actively backfire.

The user provides frontend requirements: a component, page, application, or interface to build. They may include context about the purpose, audience, or technical constraints.

## Design Thinking

Before coding, understand the context and commit to a BOLD aesthetic direction:
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme: brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc. There are so many flavors to choose from. Use these for inspiration but design one that is true to the aesthetic direction.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

**CRITICAL**: Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work - the key is intentionality, not intensity.

Then implement working code (HTML/CSS/JS, React, Vue, etc.) that is:
- Production-grade and functional
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

## Frontend Aesthetics Guidelines

Focus on:
- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt instead for distinctive choices that elevate the frontend's aesthetics; unexpected, characterful font choices. Pair a distinctive display font with a refined body font.
- **Color & Theme**: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion** (composition only): Pick *what* moves and *when*. One well-orchestrated page load with staggered reveals, dramatic entrances, or scroll-triggered surprises creates more delight than scattered micro-interactions. The `motion-polish` skill owns *how* it moves (easing, duration, spring physics, gesture mechanics). For HTML prefer CSS-only; for React reach for Motion (formerly Framer Motion).
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Add contextual effects and textures that match the overall aesthetic. Apply creative forms like gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, custom cursors, and grain overlays.

NEVER use generic AI-generated aesthetics like overused font families (Inter, Roboto, Arial, system fonts), cliched color schemes (particularly purple gradients on white backgrounds), predictable layouts and component patterns, and cookie-cutter design that lacks context-specific character.

Interpret creatively and make unexpected choices that feel genuinely designed for the context. No design should be the same. Vary between light and dark themes, different fonts, different aesthetics. NEVER converge on common choices (Space Grotesk, for example) across generations.

**IMPORTANT**: Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, precision, and careful attention to spacing, typography, and subtle details. Elegance comes from executing the vision well.

Remember: you are capable of extraordinary creative work. Don't hold back, show what can truly be created when thinking outside the box and committing fully to a distinctive vision.

## Pre-built Themes

When the user wants consistent, ready-made styling (slides, docs, reports, landing pages) rather than bespoke design, 10 curated themes are available in `themes/`. Each defines a color palette (hex codes) and font pairing.

**Available themes**: Ocean Depths, Sunset Boulevard, Forest Canopy, Modern Minimalist, Golden Hour, Arctic Frost, Desert Rose, Tech Innovation, Botanical Garden, Midnight Galaxy.

**Workflow**:
1. Present the list above and let the user pick (or describe what they want).
2. Read the chosen theme file from `themes/` (e.g. `themes/ocean-depths.md`).
3. Apply its colors and fonts consistently across the artifact.

**Custom themes**: If none fit, generate a new theme on-the-fly -- pick a evocative name, define 3-4 hex colors + a header/body font pair, and apply it. Follow the same structure as the existing theme files.

## Handoff: motion-polish

This skill owns *composition* (tone, typography, color, layout, atmosphere) and the *what/when* of motion. Once the interface is working, hand off to `motion-polish` for the *how* of motion: easing curves, durations, springs, gesture mechanics (drag, dismiss, damping), `transform-origin`, `clip-path`, performance rules (`transform`/`opacity` only, hardware acceleration), and `prefers-reduced-motion`.

Trigger it when the user asks for an animation review, says an interaction feels off, or after a build when you want a craft pass over the micro-interactions you just shipped.