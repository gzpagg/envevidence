# Env studio design system

EnvBench and EnvEvidence share a research-tool interface: mineral teal actions, light grey pages, white working surfaces, restrained headings and readable measurements. Settings have one navigation destination. Existing saved palettes and custom colours remain available.

| Token | Value |
|---|---|
| Accent / 主色 | `#186B62` |
| Page / 页面 | `#F4F7F6` |
| Surface / 卡片 | `#FFFFFF` |
| Text / 正文 | `#243638` |
| Secondary text / 辅助文字 | `#5F6F70` |
| Body / 正文 | Source Sans 3, Env Sans CJK, 16 px / 1.55 |
| Page headings / 页面标题 | Source Serif 4; system Chinese serif fallback |
| Controls / 控件 | 10 px radius, 48 px minimum touch height |
| Cards / 卡片 | 16 px radius; 4/8 px spacing rhythm |

The canonical tokens are in `envevidence/assets/design-tokens.json`; Android ships the same file. Fonts are bundled for offline use and retain their OFL licenses. The Chinese UI font is a renamed GB2312 subset of the full Noto CJK font used for exported scientific figures.

Mobile pages concentrate on the current step, linked timer and observation actions. Full procedure/history, template details and advanced timer configuration open on demand. Desktop pages retain the conditions → measurements → processing → fitting → charts → export workflow.

The design work uses [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) for typography, interaction and accessibility checks, [Refero Design](https://github.com/referodesign/refero_skill) for its bundled research/craft method, and [Anthropic frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design) for coherent CSS and component execution. Refero's live case-library MCP was not connected. This project uses Java/WebView and Streamlit; Expo-specific components were not introduced.

Functional screenshots use fictional experiments through the running interfaces. Browser previews test layout and interaction; Android instrumentation separately tests native recording, media backup and lifecycle behaviour. Normal text and control contrast, visible keyboard focus, safe areas and reduced motion are included in the design checks.

两端采用矿物青主色、浅灰背景和白色工作卡片，共用字号、间距、圆角和操作规则。手机围绕实验步骤、计时与现象记录组织；电脑围绕数据处理与动力学分析组织。原有配色和自定义设置继续保留，中文输入及实验数据不随界面语言切换改写。
