# Glacier design system

EnvBench and EnvEvidence share an interface built for active experiments and focused analysis: blue actions, soft blue-to-teal highlights, floating frosted navigation and clear white working surfaces. Headings and controls use the same local sans-serif family. Settings have one navigation destination.

## Materials, typography and motion

| Token | Value and use |
|---|---|
| Accent / 主色 | `#176BDA`; primary actions and selected navigation |
| Page / 页面 | `#F5F8FC` |
| Highlight / 重点区域 | `#E8F3FF` → `#E4F6F2`; static blue-to-teal gradient |
| Surface / 工作面板 | `#FFFFFF`; tables, plots, forms and source text |
| Text / 正文 | `#142C43` |
| Glass / 磨砂 | White at about 75% opacity, 16 px background blur, a fine highlight edge and soft shadow |
| Typography / 字体 | Source Sans 3 and Env Sans CJK; sans-serif headings, 16 px body / 1.5–1.55 line height |
| Timer digits / 计时数字 | Tabular numbers; updates do not animate the whole panel |
| Controls / 控件 | At least 48 px touch height, visible focus and labelled state |
| Rhythm / 间距 | 4/8 px spacing rhythm; distinct featured panels, ordinary panels and compact rows |
| Transitions / 过渡 | 180–220 ms for interaction feedback; respect reduced-motion preferences |

Glass is used for navigation and floating action bars. Data surfaces retain a solid background, and stacked glass layers are avoided. The **Reduce transparency** setting makes these controls solid; an unsupported `backdrop-filter` also uses a solid fallback. Semantic success, warning and error states keep readable labels and recognizable icons alongside their colors.

The canonical tokens are in `envevidence/assets/design-tokens.json`; Android ships the same file. Local fonts retain their OFL licenses. Env Sans CJK is a renamed GB2312 subset of the full Noto CJK font used for exported scientific figures. Source Serif 4 remains a bundled asset for compatibility; primary interface headings use sans-serif type.

## Page hierarchy

- **Android experiments:** a compact header leads to the current run, current step and next sampling checkpoint. Other experiments are grouped by status. Photo, observation and counter actions share a floating action bar inside the run; full conditions and history open on demand.
- **Android timers:** one focused timer has room for its digits, stage and cycle. Other timers use compact panels. Running, paused, awaiting confirmation and elapsed states combine words, icons and color.
- **Android records and templates:** observations form a dated timeline with experiment and step context. Templates show a process identity, step count and planned duration. Language, appearance and backups stay in My space.
- **Desktop analysis:** compact project and series controls lead into conditions → measurements → processing → fitting → charts → export. Wide screens place controls beside results; narrow screens follow the same sequence vertically. Charts and tables use solid surfaces.
- **Desktop evidence:** values, source quotations and review actions are adjacent on wide screens and stack in order on smaller displays.

Appearance settings are saved separately from scientific records. New installations use Glacier and glass effects. An unchanged default Mineral palette migrates to Glacier once; other presets and custom colors remain configured, and Mineral stays selectable. Interface language changes labels without rewriting research content.

## Reference decisions

The following official references were reviewed on 2026-10-05. They inform interaction and hierarchy; project screenshots and interface assets are original.

| Reference | Pattern applied here |
|---|---|
| [Apple: Meet Liquid Glass](https://developer.apple.com/videos/play/wwdc2025/219/) | Separate floating navigation from content, use depth and edge highlights to define controls, and preserve clear content surfaces. |
| [eLabNext: Procedures on mobile](https://support.elabnext.com/hc/en-us/articles/36677057038996-Procedures-Mobile-App) | Move between the current procedure step and a view of the complete procedure. |
| [Structured](https://structured.app/) | Use a visual timeline to make the current item and sequence easy to locate. |
| [ReadCube](https://about.readcube.com/) | Organize the literature workspace around the paper, its reading context and annotations. |

The glass effect is implemented in CSS in the existing Java/WebView and Streamlit apps. It uses blur, translucent surfaces, highlights and shadows; it does not invoke Apple's native Liquid Glass APIs or a dynamic refraction renderer.

The design workflow uses [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) for typography, interaction and accessibility checks, [Refero Design](https://github.com/referodesign/refero_skill) for its bundled research/craft method. Refero's live case-library MCP was not connected. The existing Java/WebView and Streamlit stacks are retained.

## Interface verification

Functional screenshots are captured from the running interfaces with fictional experiments. The release check covers both languages, 360/390 px phones, 768 px layouts and desktop widths; long titles, empty states, multiple experiments, mixed media, dialogs and keyboard entry are included. Readability checks cover contrast after glass compositing, visible focus, safe areas, 48 px targets, reduced motion and solid-surface fallbacks. Twenty simultaneous timers exercise scrolling and per-digit updates without animated card redraws.

Browser previews establish layout and interaction behavior. Android instrumentation separately covers native media, backup and lifecycle behavior; automated scientific regressions cover the desktop processing and evidence workflows. Actual results and remaining device coverage are recorded in [Android validation](ANDROID.md) and [desktop validation](VALIDATION.md).

两端采用冰川蓝青、浅色渐变与明亮磨砂导航，数据表、图像与原文保持清晰的白色工作面。手机优先展示当前实验、计时和记录操作；电脑为参数、结果与原文核验留出空间。减少透明效果可切换为实色导航，旧配色、自定义设置和科研资料按迁移规则保留。
