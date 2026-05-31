# Image to Editable PPT Skill

[![English](https://img.shields.io/badge/docs-English-blue)](README_en.md) [![GitHub stars](https://img.shields.io/github/stars/Bronto-p/image-to-editable-ppt-skill?style=flat&logo=github&label=stars)](https://github.com/Bronto-p/image-to-editable-ppt-skill/stargazers) [![GitHub forks](https://img.shields.io/github/forks/Bronto-p/image-to-editable-ppt-skill?style=flat&logo=github&label=forks)](https://github.com/Bronto-p/image-to-editable-ppt-skill/forks)

![Image to Editable PPT 项目概览](assets/image-to-editable-ppt-overview.png)

一个面向 Codex 的图片、PDF、图片版 PPT/PPTX 转高保真可编辑 PowerPoint 的 skill。本 fork 的核心策略是 **imagegen-first layered reconstruction**：每页先用 `$imagegen` / GPT Image 2 生成高保真视觉层，再把标题、正文、普通标签等主文字作为原生 PowerPoint text box 叠加。

它不是把原始整页截图塞进 PPT，也不是用 SVG/native shape 粗糙拼复杂视觉。默认让背景、嵌入图片、含字图片、图表视觉、UI 截图、艺术字、图标、装饰和复杂纹理都走图片生成/编辑；PPT 原生对象主要负责后续需要改的主文字和少量确定简单的几何对象。

> [!TIP]
> 本 skill 不负责从文章、报告、大纲或想法直接生成全新 PPT。如果你要做的是“生成一份 PPT”，可以使用 [codex-ppt-skill](https://github.com/ningzimu/codex-ppt-skill)。
>
> 关于 `codex-ppt` 和 `image-to-editable-ppt` 这两个技能的详细介绍，参见 [skill_duo_intro.pdf](assets/skill_duo_intro.pdf)。

## 转换效果示例

<table>
  <tr>
    <th>原图</th>
    <th>转换后可编辑效果</th>
  </tr>
  <tr>
    <td><img src="assets/showcase-origin-market-snapshot.png" alt="市场概览原图" width="420"></td>
    <td><img src="assets/showcase-editable-ppt-result-market-snapshot.png" alt="市场概览转换后可编辑效果" width="420"></td>
  </tr>
  <tr>
    <td><img src="assets/showcase-origin-status-report.png" alt="项目进展汇报原图" width="420"></td>
    <td><img src="assets/showcase-editable-ppt-result-status-report.png" alt="项目进展汇报转换后可编辑效果" width="420"></td>
  </tr>
  <tr>
    <td><img src="assets/showcase-origin-mdt-kidney-cancer.jpg" alt="肾癌 MDT 信息图原图" width="420"></td>
    <td><img src="assets/showcase-editable-ppt-result-mdt-kidney-cancer.png" alt="肾癌 MDT 信息图转换后可编辑效果" width="420"></td>
  </tr>
</table>

## 特点

- 支持多种输入：单张图片、多张图片、多页 PDF、图片版 PPT/PPTX 到 `.pptx`。
- 使用 Codex page subagents 并行重建页面；主 agent 负责分派、状态记录、修复调度和最终组装。
- 默认 imagegen-first：生成 clean background、嵌入图片资产、艺术字资产、图标/装饰资产，再叠加 native editable text。
- 允许 full-slide imagegen clean background 作为底层，但拒绝原始 `source.png` 整页截图加文字覆盖的假可编辑模式。
- 禁止用 SVG 作为复杂视觉 fallback；复杂视觉必须走 `$imagegen`，否则报告 blocker。
- `.pptx` 输入的页面备注会复制到输出对应页，备注内容不改动。
- 每页必须留下 manifest、visual layer plan、imagegen job 记录、preview、contact sheet 和 validation，便于检查和返工。

## 输入与输出契约

输出始终是 PowerPoint `.pptx`：

| 输入 | 输出 |
| --- | --- |
| 1 张图片 | 1 页 `.pptx` |
| 多张图片 | 多页 `.pptx`，每张图片 1 页，按提供顺序排列 |
| 多页 PDF | 多页 `.pptx`，PDF 第 N 页对应输出第 N 页 |
| 图片版 PPT/PPTX | 页数一致的 `.pptx`，原第 N 页对应输出第 N 页 |

只有 `.pptx` 输入会处理页面备注。备注由主 agent 按页原样复制到输出 PPTX：不翻译、不摘要、不改写，也不交给 page subagent 处理。

## 重建策略

每页先生成 `visual_layer_plan`，再进入重建：

1. **Generated clean background**：用 `$imagegen` / GPT Image 2 生成无主文字的高保真整页背景，保留构图、颜色、容器、图片区域、装饰氛围和必要的背景小字/水印。
2. **Generated picture assets**：照片、截图、UI、图表视觉、证书、产品图、医学图、含字图片等默认用 imagegen 高保真重建为独立图片资产。
3. **Generated art text assets**：手写字、发光字、渐变描边字、贴纸字、徽章字等艺术字默认生成透明图片资产。
4. **Native editable text**：标题、正文、普通标签、按钮文字、主要数据数字等需要后续修改的文字使用 PowerPoint text box。
5. **Minimal native shapes**：只使用简单 primitive，例如直线、矩形、圆、表格线、坐标轴和基础容器。

## 运行要求

- Codex 需要能分派 page subagent；如果不能创建 page subagent，skill 会停止并报告 blocker。
- 视觉层生成、背景修复、图片资产、艺术字、透明 asset sheet 和局部修复依赖 `$imagegen` / built-in `image_gen`。
- 如果 `$imagegen` 支持模型选择，应使用 `gpt-image-2` 或当前可用的最高保真 GPT Image 模型。

## 已知限制

- 本 skill 针对 Codex 进行深度适配，目前不支持其他 agent。
- 第三方 API 接入方式的兼容性未测试。
- 复杂视觉和艺术字由图片生成模型承担，结果质量取决于当前可用 imagegen 能力、输入清晰度和 prompt 遵循度。
- 主文字可编辑；图片资产、艺术字资产、复杂图表视觉和截图内部通常不可作为 PowerPoint 对象逐元素编辑。
- 如果缺少 subagent 或 `$imagegen` 能力，相关页面会作为 blocker 处理，不降级为 SVG/native shape 拼图。

## 安装

推荐使用 `skills` CLI 安装到 Codex 的全局 skills 目录：

```bash
npx -y skills@latest add Bronto-p/image-to-editable-ppt-skill \
  --skill image-to-editable-ppt \
  --agent codex \
  --global
```

也可以直接在 Codex 对话里输入：

```text
$skill-installer https://github.com/Bronto-p/image-to-editable-ppt-skill
```

也可以从 GitHub Releases 下载 `image-to-editable-ppt-skill-v*.zip`，解压后把其中的 `image-to-editable-ppt` 文件夹放到 `~/.codex/skills/image-to-editable-ppt`。

安装完成后，重启 Codex 让新 skill 生效。

## 使用方式

在 Codex 里可以用 `$image-to-editable-ppt` 显式选中这个技能。图片、PDF 和 `.pptx` 可以直接粘贴或附加到对话框，也可以提供本地路径：

```text
$image-to-editable-ppt 把这张图片转成可编辑 PPT。
$image-to-editable-ppt 把这些图片转成一个可编辑 PPT。
$image-to-editable-ppt 把 /path/to/deck.pdf 转成可编辑 PPT。
$image-to-editable-ppt 把 /path/to/image-based.pptx 转成可编辑 PPT。
```

skill 通常会完成这些步骤：

1. 创建独立任务目录，并把输入归一化为 `pages/page_NNN/source.png`。
2. 每一页都分配给 page subagent，包括单页输入；多页输入按 `max_concurrent_pages` 分批分派。
3. 每页创建 `visual_layer_plan`，生成 imagegen 视觉层，重建 native editable text。
4. 用状态脚本记录 dispatch、imagegen result、page result、repair 和 accepted 状态。
5. 主 agent 组装最终 `.pptx`，复制 `.pptx` 页面备注，并运行 deck validation。

## 输出结构

每次转换必须使用一个独立输出目录，所有中间文件和最终结果都保存在其中：

```text
output/image-to-editable-ppt/{job-id}/
├── input/
├── deck_manifest.json
├── page_jobs.json
├── run_state.json
├── notes_manifest.json
├── final/
│   ├── {origin}_edited.pptx
│   ├── validation.json
│   └── run_summary.json
└── pages/
    ├── page_001/
    │   ├── source.png
    │   ├── page_request.json
    │   ├── imagegen-jobs.json
    │   ├── generated/
    │   ├── assets/
    │   ├── page.pptx
    │   ├── preview.png
    │   ├── split_assets_contact.png
    │   ├── manifest.json
    │   ├── validation.json
    │   └── page_result.json
    └── page_002/
        └── ...
```

## QA 与验证

- `validate_pptx.py` 允许 `imagegen-clean-background` 整页底图叠 native editable text。
- `validate_pptx.py` 拒绝原始 `source.png` 或 source-derived/user raster 整页底图叠 native text。
- `validate_pptx.py` 拒绝 `.svg` 作为 imagegen-first 复杂视觉资产。
- 每页必须记录 `visual_layer_plan`、`background_strategy`、`visual_inventory` 和 imagegen visual layer quality checks。

## 仓库结构

```text
.
├── .github/                              # GitHub 工作流和仓库检查配置
├── assets/                               # README 示例图片和说明材料
├── skills/
│   └── image-to-editable-ppt/            # 可安装的 Codex skill
│       ├── SKILL.md
│       ├── requirements.txt
│       ├── agents/
│       ├── prompts/
│       ├── references/
│       └── scripts/
├── tests/                                # 仓库级脚本和契约测试
├── AGENTS.md
├── CHANGELOG.md
├── LICENSE
├── README.md
└── README_en.md
```

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Bronto-p/image-to-editable-ppt-skill&type=Date)](https://www.star-history.com/#Bronto-p/image-to-editable-ppt-skill&Date)

## 许可证

MIT
