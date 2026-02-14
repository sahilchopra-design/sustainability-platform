{
  "product": {
    "name": "Climate Credit Risk Intelligence Platform",
    "module": "Portfolio Scenario Analysis (NGFS)",
    "audience": ["Bank risk analysts", "Portfolio managers", "Asset managers"],
    "brand_attributes": [
      "trustworthy",
      "analytical",
      "calm under pressure",
      "data-dense but readable",
      "audit-friendly",
      "accessible"
    ],
    "style_fusion": {
      "layout_principle": "Swiss/International Typographic Style + Bento grid density (Bloomberg-like discipline without the harshness)",
      "visual_motif": "‘Scenario ribbons’ + ‘Risk chips’ + ‘Grid-first comparisons’",
      "surface_treatment": "mostly-solid neutrals with subtle noise; restrained glass only for overlays",
      "motion": "micro-interactions and purposeful loading feedback for long computations"
    }
  },
  "design_tokens": {
    "color_system": {
      "notes": [
        "No purple emphasis (finance+AI rule).",
        "Use color to encode scenarios and severity, but never rely on color alone—always pair with labels/icons/patterns.",
        "Gradients only for large section backgrounds and never more than 20% of viewport."
      ],
      "css_variables": {
        "light": {
          "--background": "210 20% 98%",
          "--foreground": "222 47% 11%",
          "--card": "0 0% 100%",
          "--card-foreground": "222 47% 11%",
          "--popover": "0 0% 100%",
          "--popover-foreground": "222 47% 11%",

          "--primary": "214 84% 32%",
          "--primary-foreground": "210 40% 98%",

          "--secondary": "210 22% 95%",
          "--secondary-foreground": "222 47% 11%",

          "--muted": "210 18% 96%",
          "--muted-foreground": "215 16% 42%",

          "--accent": "189 64% 28%",
          "--accent-foreground": "210 40% 98%",

          "--destructive": "0 72% 45%",
          "--destructive-foreground": "210 40% 98%",

          "--border": "214 20% 88%",
          "--input": "214 20% 88%",
          "--ring": "214 84% 32%",

          "--radius": "0.75rem",

          "--sidebar": "210 22% 96%",
          "--sidebar-foreground": "222 47% 11%",
          "--sidebar-active": "0 0% 100%",
          "--sidebar-active-foreground": "222 47% 11%",

          "--success": "158 64% 28%",
          "--warning": "30 90% 52%",
          "--info": "199 89% 48%",

          "--scenario-orderly": "158 64% 28%",
          "--scenario-disorderly": "30 90% 52%",
          "--scenario-hot-house": "0 72% 45%",

          "--heat-low": "203 92% 95%",
          "--heat-mid": "199 89% 48%",
          "--heat-high": "14 90% 63%",

          "--shadow-elev-1": "0 1px 2px rgba(16,24,40,0.06)",
          "--shadow-elev-2": "0 10px 24px rgba(16,24,40,0.10)",

          "--noise-opacity": "0.035"
        },
        "dark": {
          "--background": "222 35% 7%",
          "--foreground": "210 40% 98%",
          "--card": "222 30% 10%",
          "--card-foreground": "210 40% 98%",
          "--popover": "222 30% 10%",
          "--popover-foreground": "210 40% 98%",

          "--primary": "199 89% 56%",
          "--primary-foreground": "222 47% 11%",

          "--secondary": "222 22% 16%",
          "--secondary-foreground": "210 40% 98%",

          "--muted": "222 22% 16%",
          "--muted-foreground": "215 18% 70%",

          "--accent": "189 64% 38%",
          "--accent-foreground": "222 47% 11%",

          "--destructive": "0 72% 55%",
          "--destructive-foreground": "210 40% 98%",

          "--border": "222 18% 18%",
          "--input": "222 18% 18%",
          "--ring": "199 89% 56%",

          "--radius": "0.75rem",

          "--sidebar": "222 35% 8%",
          "--sidebar-foreground": "210 40% 90%",
          "--sidebar-active": "222 30% 12%",
          "--sidebar-active-foreground": "210 40% 98%",

          "--success": "158 64% 38%",
          "--warning": "30 90% 58%",
          "--info": "199 89% 56%",

          "--scenario-orderly": "158 64% 38%",
          "--scenario-disorderly": "30 90% 58%",
          "--scenario-hot-house": "0 72% 55%",

          "--heat-low": "203 55% 16%",
          "--heat-mid": "199 89% 56%",
          "--heat-high": "14 90% 63%",

          "--shadow-elev-1": "0 1px 2px rgba(0,0,0,0.35)",
          "--shadow-elev-2": "0 16px 32px rgba(0,0,0,0.45)",

          "--noise-opacity": "0.05"
        }
      },
      "scenario_mapping": {
        "orderly": {
          "label": "Orderly",
          "color_var": "--scenario-orderly",
          "pattern": "solid"
        },
        "disorderly": {
          "label": "Disorderly",
          "color_var": "--scenario-disorderly",
          "pattern": "strokeDasharray: '6 4'"
        },
        "hot_house_world": {
          "label": "Hot House World",
          "color_var": "--scenario-hot-house",
          "pattern": "strokeDasharray: '2 3'"
        }
      },
      "allowed_gradients": {
        "hero_band": {
          "usage": "Top header band behind page title + key filters only (max 15–20% viewport height)",
          "css": "background: radial-gradient(1200px 600px at 12% 20%, hsla(199,89%,56%,0.18), transparent 55%), radial-gradient(900px 500px at 78% 30%, hsla(158,64%,38%,0.12), transparent 60%), linear-gradient(180deg, hsla(210,20%,98%,1), hsla(210,20%,98%,0.0));"
        },
        "dark_header_band": {
          "usage": "Dark mode top band only; keep it subtle",
          "css": "background: radial-gradient(1100px 520px at 18% 18%, hsla(199,89%,56%,0.16), transparent 60%), radial-gradient(900px 420px at 76% 22%, hsla(158,64%,38%,0.10), transparent 62%);"
        }
      }
    },
    "typography": {
      "font_pairing": {
        "display": {
          "name": "Space Grotesk",
          "usage": "H1/H2, KPI numerals, section headings"
        },
        "body": {
          "name": "IBM Plex Sans",
          "usage": "tables, forms, paragraphs"
        },
        "mono": {
          "name": "IBM Plex Mono",
          "usage": "ISIN/tickers, IDs, JSON export preview"
        }
      },
      "react_google_fonts_install": {
        "notes": "Project uses .js components; import fonts in index.css via Google Fonts @import or in public/index.html.",
        "index_css_import": "@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');"
      },
      "scale_tailwind": {
        "h1": "text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight",
        "h2": "text-base md:text-lg text-muted-foreground",
        "section_title": "text-lg font-semibold tracking-tight",
        "kpi": "text-2xl sm:text-3xl font-semibold tabular-nums",
        "table": "text-sm",
        "caption": "text-xs text-muted-foreground"
      },
      "numeric_rules": [
        "Use tabular numbers for KPIs and tables: add `tabular-nums`.",
        "Always include unit and basis (e.g., bps, %, $m) in secondary text.",
        "For deltas, include sign and direction label (e.g., +12 bps vs baseline)."
      ]
    },
    "spacing_and_grid": {
      "layout": {
        "app_shell": "Left sidebar (collapsible) + top command bar + main content with max-w-[1400px] but NOT centered; use `mx-auto` only on wide screens when content would be too stretched.",
        "content_padding": "px-4 sm:px-6 lg:px-8 py-6",
        "desktop_grid": "Use 12-col grid with gap-6; KPIs: 4 cards across; charts: 8/4 or 7/5; tables full width.",
        "tablet": "Collapse sidebar into sheet; switch to 6-col grid.",
        "mobile": "Single-column; charts become stacked; tables use horizontal scroll with sticky first column."
      },
      "density_modes": {
        "comfortable": "default",
        "compact": "reduce paddings by 20%, table row height to 40px; provide toggle in Settings"
      }
    },
    "radius_and_shadows": {
      "radius": {
        "card": "rounded-xl",
        "input": "rounded-lg",
        "button": "rounded-lg"
      },
      "shadows": {
        "card": "shadow-[var(--shadow-elev-1)] hover:shadow-[var(--shadow-elev-2)]",
        "popover": "shadow-[var(--shadow-elev-2)]"
      }
    }
  },
  "component_system": {
    "primary_components": {
      "shadcn_paths": [
        "/app/frontend/src/components/ui/button.jsx",
        "/app/frontend/src/components/ui/card.jsx",
        "/app/frontend/src/components/ui/table.jsx",
        "/app/frontend/src/components/ui/tabs.jsx",
        "/app/frontend/src/components/ui/select.jsx",
        "/app/frontend/src/components/ui/dialog.jsx",
        "/app/frontend/src/components/ui/sheet.jsx",
        "/app/frontend/src/components/ui/dropdown-menu.jsx",
        "/app/frontend/src/components/ui/tooltip.jsx",
        "/app/frontend/src/components/ui/hover-card.jsx",
        "/app/frontend/src/components/ui/scroll-area.jsx",
        "/app/frontend/src/components/ui/resizable.jsx",
        "/app/frontend/src/components/ui/skeleton.jsx",
        "/app/frontend/src/components/ui/progress.jsx",
        "/app/frontend/src/components/ui/calendar.jsx",
        "/app/frontend/src/components/ui/sonner.jsx",
        "/app/frontend/src/components/ui/badge.jsx",
        "/app/frontend/src/components/ui/separator.jsx",
        "/app/frontend/src/components/ui/breadcrumb.jsx",
        "/app/frontend/src/components/ui/command.jsx",
        "/app/frontend/src/components/ui/collapsible.jsx",
        "/app/frontend/src/components/ui/switch.jsx",
        "/app/frontend/src/components/ui/checkbox.jsx",
        "/app/frontend/src/components/ui/popover.jsx",
        "/app/frontend/src/components/ui/pagination.jsx"
      ]
    },
    "custom_components_to_build": [
      {
        "name": "ScenarioRibbon",
        "purpose": "Top-of-page filter cluster that shows selected scenarios + horizons as removable chips and a compact legend.",
        "compose_from": ["badge.jsx", "button.jsx", "select.jsx", "popover.jsx", "separator.jsx"],
        "data_testids": [
          "scenario-ribbon",
          "scenario-ribbon-add-scenario-button",
          "scenario-ribbon-horizon-select",
          "scenario-ribbon-scenario-chip"
        ]
      },
      {
        "name": "KpiCard",
        "purpose": "A dense KPI card with primary metric, delta, sparkline, and footnote.",
        "compose_from": ["card.jsx", "tooltip.jsx"],
        "data_testids": ["kpi-card", "kpi-card-primary-value", "kpi-card-delta"]
      },
      {
        "name": "ScenarioComparisonChart",
        "purpose": "Line chart comparing multiple scenarios across horizons with pattern encoding (solid/dashed/dotted) and legend toggles.",
        "compose_from": ["card.jsx", "tabs.jsx", "tooltip.jsx"],
        "library": "recharts",
        "data_testids": ["scenario-comparison-chart", "scenario-comparison-chart-legend-toggle"]
      },
      {
        "name": "RiskHeatmap",
        "purpose": "Sector x Horizon heatmap for selected scenario; click cell to drill-down.",
        "compose_from": ["card.jsx", "tooltip.jsx"],
        "library": "custom svg + tailwind OR recharts ScatterChart grid",
        "data_testids": ["risk-heatmap", "risk-heatmap-cell"]
      },
      {
        "name": "HoldingsDataGrid",
        "purpose": "Table with sticky header, sticky first col, row selection, column visibility, and inline edit actions.",
        "compose_from": ["table.jsx", "dropdown-menu.jsx", "checkbox.jsx", "input.jsx", "button.jsx", "scroll-area.jsx"],
        "data_testids": ["holdings-datagrid", "holdings-datagrid-search-input", "holdings-datagrid-export-button"]
      },
      {
        "name": "LongRunJobToast",
        "purpose": "Sonner toast pattern for long-running analyses: queued → running → complete/failed with deep link to results.",
        "compose_from": ["sonner.jsx", "progress.jsx", "button.jsx"],
        "data_testids": ["analysis-job-toast", "analysis-job-toast-view-results-button"]
      }
    ],
    "buttons": {
      "brand": "Professional / Corporate",
      "variants": {
        "primary": {
          "usage": "Run analysis, Save, Export",
          "tailwind": "bg-primary text-primary-foreground hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        },
        "secondary": {
          "usage": "Compare, Add to portfolio",
          "tailwind": "bg-secondary text-secondary-foreground hover:bg-secondary/70"
        },
        "ghost": {
          "usage": "Table row actions",
          "tailwind": "hover:bg-accent/10"
        }
      },
      "interaction": {
        "press": "active:scale-[0.98]",
        "transition": "transition-colors duration-150",
        "rule": "Do NOT use transition-all"
      }
    },
    "forms_and_filters": {
      "pattern": "Left-to-right filter bar on desktop; collapses into a Sheet on tablet.",
      "controls": [
        "Scenario multi-select (custom using Popover + Command)",
        "Horizon select (Select)",
        "Sector select (Select)",
        "Portfolio select (Select)",
        "Run button (Button)",
        "Save config (Button variant=secondary)"
      ],
      "data_testids": [
        "filter-portfolio-select",
        "filter-scenario-multiselect",
        "filter-horizon-select",
        "filter-sector-select",
        "run-analysis-button"
      ]
    }
  },
  "page_blueprints": {
    "dashboard_home": {
      "layout": "KPI row + Recent analyses timeline + Portfolio table summary",
      "sections": [
        "Top band (title + quick actions)",
        "KPI cards (4-up)",
        "Charts: 'Portfolio risk trend' (line) + 'Exposure by sector' (bar)",
        "Recent analyses table (sortable, paginated)"
      ],
      "key_components": ["KpiCard", "ScenarioComparisonChart", "HoldingsDataGrid", "tabs.jsx"],
      "data_testids": ["home-kpi-row", "home-recent-analyses-table", "home-create-portfolio-button"]
    },
    "portfolio_list": {
      "layout": "Toolbar + table + right-side details drawer",
      "notes": "Use Resizable panels: table left, details right; on tablet use Sheet for details.",
      "data_testids": ["portfolio-list-table", "portfolio-create-button", "portfolio-search-input"]
    },
    "portfolio_detail": {
      "layout": "Header (portfolio name + actions) + holdings grid + allocation charts",
      "notes": "Inline edit uses Dialog; bulk actions use DropdownMenu.",
      "data_testids": ["portfolio-detail-header", "portfolio-holdings-grid", "portfolio-edit-button"]
    },
    "scenario_analysis": {
      "layout": "ScenarioRibbon + config cards + run drawer",
      "notes": "Put assumptions in an Accordion; keep primary action visible.",
      "data_testids": ["scenario-analysis-config", "scenario-analysis-run-button", "scenario-analysis-assumptions-accordion"]
    },
    "results_dashboard": {
      "layout": "Top comparison controls + tabs (Portfolio/Sector/Company/Asset) + split charts/table",
      "tabs": ["Portfolio", "Sector drill-down", "Company view", "Asset detail"],
      "notes": "Use breadcrumb for drill-down path; keep filters sticky.",
      "data_testids": ["results-tabs", "results-breadcrumb", "results-export-dropdown"]
    },
    "climate_data": {
      "layout": "Dataset list + dataset detail panel",
      "notes": "Provide refresh action with confirmation dialog; show last updated timestamp.",
      "data_testids": ["climate-data-refresh-button", "climate-data-dataset-table", "climate-data-last-updated"]
    },
    "settings": {
      "layout": "Preferences forms",
      "notes": "Theme toggle, density mode, default scenario/horizon.",
      "data_testids": ["settings-theme-toggle", "settings-density-toggle", "settings-default-horizon-select"]
    }
  },
  "data_visualization_guidelines": {
    "chart_principles": [
      "Default to line charts for scenario comparison across horizons; bars for sector contribution; heatmap for multi-dimensional scan.",
      "Use pattern encoding for scenario lines (solid/dashed/dotted) to remain readable in grayscale.",
      "Always include baseline (Current) if available as thin neutral line.",
      "Tooltips must be keyboard-accessible: allow focus on legend items and points.",
      "Provide a 'View as table' toggle for any critical chart (accessibility + audit)."
    ],
    "recharts_theme_scaffold_js": {
      "notes": "JS-only examples (no TSX).",
      "palette_vars": "Use CSS vars -> convert to hsl() in styles: `stroke=\"hsl(var(--scenario-orderly))\"`.",
      "line_example": "<Line type=\"monotone\" dataKey=\"orderly\" stroke=\"hsl(var(--scenario-orderly))\" strokeWidth={2} dot={false} />",
      "dashed_example": "<Line dataKey=\"disorderly\" stroke=\"hsl(var(--scenario-disorderly))\" strokeDasharray=\"6 4\" strokeWidth={2} dot={false} />"
    },
    "heatmap": {
      "encoding": "Use 5-step discrete ramp derived from --heat-low/mid/high with neutral steps in between.",
      "legend": "Always show numeric thresholds and units, not just colors.",
      "interaction": "Hover shows tooltip; click drills down; keyboard: cell is a button with focus ring.",
      "data_testids": ["heatmap-legend", "heatmap-view-table-toggle"]
    },
    "empty_and_error_states": {
      "empty": "Use Skeleton for initial load; use calm empty states with next-step CTA (e.g., Create portfolio).",
      "error": "Use Alert component with action to retry; include correlation ID in monospace.",
      "loading_long": "For runs >3s: show progress with stage labels (Fetching data → Computing sector shocks → Aggregating → Finalizing)."
    }
  },
  "motion_and_microinteractions": {
    "library": {
      "recommended": "framer-motion",
      "install": "npm i framer-motion",
      "usage": "Only for page transitions, drawer/dialog entrance, and KPI number fade-in; keep subtle."
    },
    "principles": [
      "150ms color transitions on hover for buttons/inputs (transition-colors).",
      "No layout jank: prefer opacity/transform for entrances.",
      "For resizable panels, animate only the drag handle hover (not panel width).",
      "For Run Analysis: button morphs to spinner + 'Running…' label; on completion show Sonner toast with deep link."
    ]
  },
  "accessibility_and_auditability": {
    "wcag": [
      "Meet WCAG AA contrast for text and interactive controls.",
      "Do not encode meaning by color alone; add labels, icons, or patterns.",
      "Keyboard: all menus, popovers, tabs, dialogs must be reachable and operable.",
      "Charts: provide aria title/desc and a table view for underlying values.",
      "Focus: always show visible focus ring using --ring; do not remove outlines."
    ],
    "content_rules": [
      "Use explicit units, time horizon, and scenario names in headings/subtitles.",
      "Show last-updated timestamps for datasets and analyses.",
      "Export actions must confirm what will be exported and include row counts."
    ],
    "data_testid_rule": "All interactive and key informational elements MUST include `data-testid` in kebab-case describing role (not appearance)."
  },
  "image_urls": {
    "usage_note": "For dashboards, keep imagery minimal. Use only subtle hero/background images in marketing-like top band if needed; do not place behind tables/charts.",
    "hero_background_optional": [
      {
        "url": "https://images.unsplash.com/photo-1660020619062-70b16c44bf0f?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NTN8MHwxfHNlYXJjaHwyfHxtb2Rlcm4lMjBmaW5hbmNpYWwlMjBhbmFseXRpY3MlMjBkYXNoYm9hcmQlMjBhYnN0cmFjdCUyMGJhY2tncm91bmR8ZW58MHx8fGJsdWV8MTc3MTAyOTE1OHww&ixlib=rb-4.1.0&q=85",
        "category": "decorative",
        "description": "Soft finance/chart photo for login/empty-state header band (apply 8–12% opacity + blur)."
      }
    ],
    "empty_state_illustration_optional": [
      {
        "url": "https://images.unsplash.com/photo-1660165458059-57cfb6cc87e5?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NTN8MHwxfHNlYXJjaHwzfHxtb2Rlcm4lMjBmaW5hbmNpYWwlMjBhbmFseXRpY3MlMjBkYXNoYm9hcmQlMjBhYnN0cmFjdCUyMGJhY2tncm91bmR8ZW58MHx8fGJsdWV8MTc3MTAyOTE1OHww&ixlib=rb-4.1.0&q=85",
        "category": "decorative",
        "description": "Abstract city/data blocks image for 'No analyses yet' empty state; keep small and subtle."
      }
    ]
  },
  "instructions_to_main_agent": [
    "Replace the default shadcn tokens in /app/frontend/src/index.css with the provided HSL variables (light + dark). Keep chart tokens aligned with scenario mapping.",
    "Remove/avoid using the default CRA App.css centered header patterns; do not center the app container.",
    "Implement an AppShell: Sidebar + Topbar. Sidebar uses NavigationMenu + Collapsible; on mobile use Sheet.",
    "All pages should use consistent page header: Title (H1), subtitle (H2), right-aligned action cluster (Run/Export/Save).",
    "Use Resizable panels on data-dense screens (Portfolio list/detail, Results dashboard) for table + detail.",
    "Use Sonner toasts for analysis runner lifecycle; include data-testid on toast action buttons.",
    "For charts: implement pattern encoding (dash arrays) and add a 'View as table' toggle for accessibility.",
    "Every interactive and key informational element MUST include a stable data-testid in kebab-case."
  ],
  "appendix_general_ui_ux_design_guidelines": "<General UI UX Design Guidelines>\n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
