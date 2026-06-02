# Script Contracts 第一版

## 目录

- `image_to_editable_ppt_runtime.py`
- `prepare_deck_run.py`
- `page_job_status.py`
- `record_page_dispatch.py`
- `record_page_result.py`
- `record_imagegen_result.py`
- `process_asset_sheet.py`
- `build_pptx_from_manifest.py`
- `validate_pptx.py`
- `make_page_contact_sheet.py`
- `queue_page_repairs.py`
- `finalize_deck_run.py`
- `smoke_test.py`

脚本只做确定性工作，不手工绘制复杂视觉资产，不把 SVG/native shape 当作 imagegen 的复杂视觉替代品。

## `image_to_editable_ppt_runtime.py`

职责：

- 创建 skill-local `.venv`。
- 安装依赖。
- doctor 检查。
- 输出 venv python。
- `doctor` 是 workflow preflight；缺少 `.venv` 时先运行 `bootstrap`。

## `prepare_deck_run.py`

职责：

- 归一化图片、PDF、图片版 PPT/PPTX。
- 创建 run 目录。
- 复制输入到 `input/`。
- 生成 `deck_manifest.json`。
- 生成 `page_jobs.json`。
- 为每页生成 `page_request.json` 和 `source.png`。
- 提取 `notes_manifest.json`。

不做页面理解或 imagegen 决策。

`--job-dir` 如果是相对路径，必须解释为 `--out-root` 下的目录；只有绝对路径才绕过 `--out-root`。

## `page_job_status.py`

职责：

- 只读 `page_jobs.json`。
- 输出 pending、dispatched、recorded、repair_needed、blocked pages。
- 输出 `max_concurrent_pages`、`active_dispatches`、`dispatch_slots_available`、`dispatchable_pages`、`next_dispatch_pages`，供主 agent 维护 rolling worker pool。
- `next_dispatch_pages` 必须限制为当前可用 slot 数量；主 agent 应优先按该列表补满 worker。
- 不修改状态。

## `record_page_dispatch.py`

职责：

- page spawn 后记录 dispatch。
- 推进 `pending -> dispatched` 或 `repair_needed -> repair_dispatched`。
- 写 dispatch prompt hash、page_request hash、agent id/nickname。
- 不负责 spawn，也不作为真实并发 scheduler；并发池由主 agent 根据 `page_job_status.py` 控制。
- 当 `dispatch_slots_available=0` 时拒绝记录新的 dispatch，防止超过 `max_concurrent_pages`。

## `record_page_result.py`

职责：

- 校验 page worker 返回路径。
- 校验 required outputs 存在且在 page dir 内。
- 校验 `qa_review.json` 存在且在 page dir 内。
- 记录 hash、完成时间、known limits。
- 推进 `dispatched -> recorded` 或 `repair_dispatched -> recorded`。

## `record_imagegen_result.py`

职责：

- 复制 `$imagegen` 选中输出到 page 目录。
- 写 source path、output path、role/intended layer、source type、model/tool、prompt hash、input image roles、hash、metadata。
- 推进 imagegen job 到 `recorded`。

## `process_asset_sheet.py`

职责：

- 调用 `$imagegen` chroma-key helper。
- 调用 splitter/cropper。
- 统一处理 asset sheet 自动切分和手动 crop。
- 校验 alpha 和组件。
- 推进 imagegen job 到 `processed`。
- 如果指定 `--job-id`，对应 job 必须已由 `record_imagegen_result.py` 记录，不能从缺失 job 直接创建 processed 状态。
- source-derived 小图标裁剪也应走这个脚本，使用 `--crop-source source.png --source-type source-derived-rasterization --crop-padding` 和必要的 `--crop-remove-border-bg`，避免 page worker 手写临时裁剪逻辑。

## `build_pptx_from_manifest.py`

职责：

- 从 page manifest 构建 page-level PPTX。
- 从 deck manifest 构建 final PPTX。
- 生成 preview。
- 支持 full-slide imagegen clean background 加 native editable text 的分层结构。

preview 只用于 QA，不是 PowerPoint/WPS 的精确排版引擎。它必须按 point-to-pixel 换算近似渲染文字，暴露字号过大、溢出和错位风险；page worker 不能把 preview 当成最终排版完全一致的证明。

`roundRect` 必须把 manifest 中的 `source_corner_radius_px`/`radius` 写入 OOXML adjustment，不能让 PowerPoint 使用默认圆角比例。

## `validate_pptx.py`

职责：

- 验证 page/deck PPTX。
- 检查 relationship、media hash、text inventory、notes hash、full-slide raster 违规。
- 检查 `qa_review.json` 存在，并可用于 repair evidence。
- 允许 imagegen clean background 作为 full-slide bottom raster。
- 拒绝原始 source.png 或 source-derived/user-provided full-slide screenshot 加 native text 的假可编辑模式。
- 拒绝 `.svg` 作为复杂视觉 asset。

## `make_page_contact_sheet.py`

职责：

- 生成 origin/preview side-by-side QA 图。

## `queue_page_repairs.py`

职责：

- 根据 validation 和 QA notes 写 `repair_queue.json`。
- repair item 必须包含 failure type、evidence、suggested scope、required output 和 previous attempt summary。
- 推进 page 到 `repair_needed`。

## `finalize_deck_run.py`

职责：

- 确认所有 page accepted。
- 组装 final PPTX。
- 复制 notes。
- 运行 deck validation。
- 生成 `run_summary.json`。
- 推进 run 到 complete。

## `smoke_test.py`

职责：

- 不调用 `$imagegen`。
- 创建临时单页输入和合规 synthetic page artifacts。
- 验证相对 `--job-dir` 会落在 `--out-root` 下。
- 验证 prepare/status/dispatch/result/finalize deterministic 脚本链路。
