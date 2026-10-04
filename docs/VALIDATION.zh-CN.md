# 验证记录

[English](VALIDATION.md) · [安卓检查](ANDROID.md) · [项目介绍](../README.zh-CN.md)

## 当前版本：桌面 0.4.1 / 安卓 0.7.0

本地 Windows/Python 3.13 已通过 **188 项测试**与 Ruff，JavaScript 已通过 **87 项测试**。新增覆盖共享字体与配色、旧偏好保留、阶段边界、模板快照、步骤历史、媒体校验与桌面导入兼容。四环境桌面及安卓构建／设备检查等待发布工作流完成。

实际浏览器场景使用隔离的自制数据，覆盖中英文的新实验、步骤计时与现象关联、有理由跳过、重复执行、手动循环、快捷短语和重启恢复。当前截图采用矿物青配色。

## EnvEvidence 电脑版 · 0.4.0

本地 Windows/Python 3.13 已通过 **132 项测试**、Ruff、文献 CLI 演示，以及源码包和 wheel 构建。[四环境桌面工作流](https://github.com/gzpagg/envevidence/actions/workflows/ci.yml)记录各次发布修订在 Windows/Linux、Python 3.11/3.13 下的结果。

新增检查覆盖已知参数的降解、吸附及 Monod 曲线；固定参数、权重、线性化、弱可识别性和数值尺度；显式校正与单位；原始字节及哈希；手机 CSV/ZIP 与检测编号关联；原子保存与修订审计；兼容 SOP 模板；确认成果选择；PNG/TIFF/SVG 尺寸、中文字体和图例对应关系，以及实际 CLI 重跑后参数一致。原有文献回归测试仍在完整测试集中。

数值案例为自制数据。独立实验室真实检测数据的评估需另行开展；参数区间对应分析时记录的拟合假设。

## EnvEvidence 电脑版 · 0.3.0 基线

电脑版通过[已发布修订的自动检查](https://github.com/gzpagg/envevidence/actions/runs/36954317903)：Windows/Linux 与 Python 3.11/3.13 四个组合，每个环境均通过 **46 项测试**、Ruff、离线 CLI 演示，以及源码包和 wheel 构建。当前本地运行也已通过全部 46 项测试与 Ruff。

覆盖内容包括：

- 实验条件分离、污染物／TOC 指标区分、补充材料出处、伪造引用检测、单位遗漏和人工核验历史。
- OpenAI/Anthropic 模拟 HTTP 协议、拒绝／截断响应和提取中断恢复。
- CSV/Excel/JSON 导出、表格公式防护及运行数据的打包排除。
- 工作台原子保存、损坏文件保留、语言与外观持久化。
- 直接打开文献证据，以及 0.2 的学习、任务、便签在保存语言和外观后仍完整保留。

0.3.0 移除计划管理界面，相应调整四项界面测试；原有证据流程与回归检查继续保留。

## EnvBench 安卓版 · 0.6.1

[0.6.1 签名预览版](https://github.com/gzpagg/envevidence/releases/tag/v0.6.1-android-preview.1)已发布。[安卓自动检查](https://github.com/gzpagg/envevidence/actions/runs/36954317866)通过 **56/56 项 JavaScript 测试**、Android lint、JVM 单元测试、调试／发布 APK 构建，以及 **2/2 项 Android 15 模拟器原生测试**；本地 JavaScript 测试也通过 56/56 项。

新增回归覆盖无效／空白 LC 行对应、整批导入验证、样品测量来源、带历史的时间修订、有理由的拟合排除、计划内外取样与 CSV 审计列。原生导入测试检查无效／空白输入、成功应用与重启持久化；实验手记测试覆盖旧数据迁移、计数器、语言／活动重建、原图 ZIP 往返恢复和后台提醒。APK 校验值、签名与源码资源比对记录见[安卓检查](ANDROID.md)。

0.6.0 基线已通过 41 项 JavaScript 测试，以及 [Android lint、APK 构建和模拟器测试](https://github.com/gzpagg/envevidence/actions/runs/36945435012)。安卓测试使用合成实验和生成图片。

## 界面与演示资料

中英文演示使用自制合成示例。当前 26 张安卓截图来自本机 Chromium 中实际运行的 0.7.0 内置界面：预览视口及导出 PNG 均为 390 × 844 像素。12 张桌面截图来自实际运行的 EnvEvidence 0.4.1 Streamlit 界面，包含实验分析、拟合、图表、文献和外观，尺寸为 1440 × 1080；两者均使用隔离的合成数据。电脑版演示校验资料哈希并使用预录提取结果，载入演示不调用模型。

0.4.0 浏览器检查覆盖 1440 × 1080 下六个分析页面的中英文与四套配色，以及 390 × 844 下的中英文页面，未发现应用异常或页面横向溢出。检查脚本保存在 `scripts/check_desktop_layouts.js`。早期界面检查还覆盖深色自定义背景。Android 15 原生基线检查包含图片保存、ZIP 往返恢复、后台通知和活动重建。当前安卓截图及发布检查见安卓记录。

## 科研与设备评估

尚未建立真实 API 提取与真实论文科学准确性的评估集。原句定位检查引用文字是否存在于解析页面，实验归属、单位和解释由核验者判断。

实验计算使用合成比值与已知曲线检查。实体手机相机、长时间／重启运行、厂商省电策略与独立实验室试用需要单独评估；这些与单元测试及成功构建是不同的验证范围。

## 复现自动检查

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m envevidence demo --output data/demo
python -m build
node --test android/tests/*.test.cjs
```

具体修订的结果以对应工作流记录为准。[电脑版自动检查](https://github.com/gzpagg/envevidence/actions/workflows/ci.yml) · [安卓自动检查](https://github.com/gzpagg/envevidence/actions/workflows/android.yml)
