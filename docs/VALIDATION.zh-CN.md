# 验证记录

[English](VALIDATION.md) · [安卓检查](ANDROID.md) · [项目介绍](../README.zh-CN.md)

## EnvEvidence 电脑版 · 0.3.0

已合并的电脑版实现通过[自动检查](https://github.com/gzpagg/envevidence/actions/runs/36945434951)：Windows/Linux 与 Python 3.11/3.13 四个组合，运行 Ruff、pytest、离线 CLI 演示与包构建。测试共 46 项。当前本地运行也已通过全部 46 项测试与 Ruff 检查。

覆盖内容包括：

- 实验条件分离、污染物／TOC 指标区分、补充材料出处、伪造引用检测、单位遗漏和人工核验历史。
- OpenAI/Anthropic 模拟 HTTP 协议、拒绝／截断响应和提取中断恢复。
- CSV/Excel/JSON 导出、表格公式防护及运行数据的打包排除。
- 工作台原子保存、损坏文件保留、语言与外观持久化。
- 直接打开文献证据，以及 0.2 的学习、任务、便签在保存语言和外观后仍完整保留。

0.3.0 移除计划管理界面，相应调整四项界面测试；原有证据流程与回归检查继续保留。

## EnvBench 安卓版 · 0.6.1

当前版本在 0.6.0 检查基础上增加：无效／空白 LC 行对应关系、整批导入验证、样品测量来源、带历史的时间修订、有理由的拟合排除、计划内外取样与 CSV 审计列。当前本地 JavaScript 测试已通过 **56/56 项**。新增 0.6.1 原生 Android lint／构建／模拟器工作流尚未运行；当前范围与已验证的早期记录见[安卓检查](ANDROID.md)。

0.6.0 基线已通过 41 项 JavaScript 测试，以及 [Android lint、APK 构建和模拟器测试](https://github.com/gzpagg/envevidence/actions/runs/36945435012)。安卓测试使用合成实验和生成图片。

## 界面与演示资料

中英文演示使用自制合成示例。当前 16 张安卓截图来自本机 Chromium 中实际运行的 0.6.1 内置界面：预览视口及导出 PNG 均为 390 × 844 像素。6 张桌面截图来自实际运行的 EnvEvidence 0.3.0 Streamlit 界面，尺寸为 1440 × 1080；两者均使用隔离的合成数据。电脑版演示校验资料哈希并使用预录提取结果，载入演示不调用模型。

早期电脑版界面检查包含 1440 px、390 px 两种宽度、四套配色与深色自定义背景。Android 15 原生基线检查包含图片保存、ZIP 往返恢复、后台通知和活动重建。当前截图及发布检查见安卓记录。

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
