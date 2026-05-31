# Image to Editable PPT Skill

[![中文](https://img.shields.io/badge/docs-中文-red)](README.md) [![GitHub stars](https://img.shields.io/github/stars/Bronto-p/image-to-editable-ppt-skill?style=flat&logo=github&label=stars)](https://github.com/Bronto-p/image-to-editable-ppt-skill/stargazers) [![GitHub forks](https://img.shields.io/github/forks/Bronto-p/image-to-editable-ppt-skill?style=flat&logo=github&label=forks)](https://github.com/Bronto-p/image-to-editable-ppt-skill/forks)

![Image to Editable PPT project overview](assets/image-to-editable-ppt-overview.png)

A Codex skill for converting images, PDFs, and image-based PPT/PPTX files into high-fidelity editable PowerPoint `.pptx` output. This fork is built around **imagegen-first layered reconstruction**: each page first gets high-fidelity visual layers generated with `$imagegen` / GPT Image 2, then main titles, body copy, and ordinary labels are overlaid as native PowerPoint text boxes.

It is not a full-slide screenshot wrapper, and it does not use SVG/native shapes to approximate complex visuals. By default, backgrounds, embedded pictures, text-bearing pictures, chart visuals, UI screenshots, art text, icons, decorations, and complex textures are generated or edited as raster visual layers. Native PowerPoint objects are reserved for main editable text and a small set of confidently simple geometry.

> [!TIP]
> This skill does not create new decks from articles, reports, outlines, or ideas. If your goal is to generate a PPT, use [codex-ppt-skill](https://github.com/ningzimu/codex-ppt-skill).
>
> For a detailed introduction to `codex-ppt` and `image-to-editable-ppt`, see [skill_duo_intro.pdf](assets/skill_duo_intro.pdf).

## Conversion Examples

<table>
  <tr>
    <th>Original</th>
    <th>Editable Result</th>
  </tr>
  <tr>
    <td><img src="assets/showcase-origin-market-snapshot.png" alt="Market snapshot original" width="420"></td>
    <td><img src="assets/showcase-editable-ppt-result-market-snapshot.png" alt="Market snapshot editable result" width="420"></td>
  </tr>
  <tr>
    <td><img src="assets/showcase-origin-status-report.png" alt="Status report original" width="420"></td>
    <td><img src="assets/showcase-editable-ppt-result-status-report.png" alt="Status report editable result" width="420"></td>
  </tr>
  <tr>
    <td><img src="assets/showcase-origin-mdt-kidney-cancer.jpg" alt="Kidney cancer MDT infographic original" width="420"></td>
    <td><img src="assets/showcase-editable-ppt-result-mdt-kidney-cancer.png" alt="Kidney cancer MDT infographic editable result" width="420"></td>
  </tr>
</table>

## Highlights

- Supports one image, multiple images, multi-page PDFs, and image-based PPT/PPTX files.
- Uses Codex page subagents to rebuild pages in parallel; the parent agent owns dispatch, state recording, repair orchestration, and final assembly.
- Defaults to imagegen-first reconstruction: generate clean backgrounds, embedded picture assets, art-text assets, icon/decor assets, then overlay native editable text.
- Allows a full-slide imagegen clean background as the bottom layer, while rejecting the fake-editable pattern of original `source.png` plus text overlays.
- Rejects SVG as a complex-visual fallback; complex visuals must use `$imagegen` or the page reports a blocker.
- Preserves `.pptx` speaker notes on matching output slides without modifying note text.
- Requires manifest, visual layer plan, imagegen job records, preview, contact sheet, and validation artifacts for every page.

## Input And Output Contract

Output is always a PowerPoint `.pptx` file:

| Input | Output |
| --- | --- |
| 1 image | 1-slide `.pptx` |
| Multiple images | Multi-slide `.pptx`, one slide per image, in the provided order |
| Multi-page PDF | Multi-slide `.pptx`; PDF page N maps to output slide N |
| Image-based PPT/PPTX | `.pptx` with the same slide count; source slide N maps to output slide N |

Speaker notes are handled only for `.pptx` input. The parent agent copies notes to matching output slides unchanged: no translation, summarization, rewriting, or page-subagent processing.

## Reconstruction Strategy

Each page starts with `visual_layer_plan`, then proceeds through layered reconstruction:

1. **Generated clean background**: `$imagegen` / GPT Image 2 creates a high-fidelity full-slide background without primary text, preserving composition, color, containers, picture regions, decorative atmosphere, and allowed decorative microtext or watermarks.
2. **Generated picture assets**: photos, screenshots, UI, chart visuals, certificates, product images, medical images, and text-bearing picture regions are rebuilt as independent high-fidelity imagegen assets by default.
3. **Generated art text assets**: handwriting, glow text, gradient-outline text, sticker text, badge text, and other decorative typography become transparent image assets.
4. **Native editable text**: titles, body copy, ordinary labels, button text, and major data numbers that users are likely to edit become PowerPoint text boxes.
5. **Minimal native shapes**: only simple primitives such as lines, rectangles, circles, table/grid lines, axes, and basic containers use native shapes.

## Runtime Requirements

- Codex must be able to dispatch page subagents; if page subagents cannot be created, the skill stops and reports a blocker.
- Visual-layer generation, background repair, picture assets, art text, transparent asset sheets, and targeted repairs depend on `$imagegen` / built-in `image_gen`.
- If `$imagegen` supports model selection, use `gpt-image-2` or the highest-fidelity currently available GPT Image model.

## Known Limitations

- This skill is deeply adapted for Codex and currently does not support other agents.
- Compatibility with third-party API integrations has not been tested.
- Complex visuals and art text are handled by image generation, so quality depends on current imagegen capability, source clarity, and prompt adherence.
- Main text is editable; picture assets, art text assets, complex chart visuals, and screenshots are usually not internally editable as PowerPoint objects.
- If subagents or `$imagegen` are unavailable, affected pages are blockers. The skill does not degrade to SVG/native-shape approximation.

## Install

Recommended Codex installation:

```bash
npx -y skills@latest add Bronto-p/image-to-editable-ppt-skill \
  --skill image-to-editable-ppt \
  --agent codex \
  --global
```

You can also type this directly in a Codex conversation:

```text
$skill-installer https://github.com/Bronto-p/image-to-editable-ppt-skill
```

You can also download `image-to-editable-ppt-skill-v*.zip` from GitHub Releases, unzip it, and place the contained `image-to-editable-ppt` folder at `~/.codex/skills/image-to-editable-ppt`.

Restart Codex after installation.

## Usage

Use `$image-to-editable-ppt` to explicitly select this skill. Images, PDFs, and `.pptx` files can be pasted or attached directly in the conversation, or provided as local paths:

```text
$image-to-editable-ppt convert this image into an editable PowerPoint.
$image-to-editable-ppt convert these images into one editable PowerPoint.
$image-to-editable-ppt convert /path/to/deck.pdf into an editable PowerPoint.
$image-to-editable-ppt convert /path/to/image-based.pptx into an editable PowerPoint.
```

The normal workflow is:

1. Create an isolated job folder and normalize inputs into `pages/page_NNN/source.png`.
2. Dispatch every page to a page subagent, including single-page inputs; batch multi-page runs by `max_concurrent_pages`.
3. Create `visual_layer_plan` for every page, generate imagegen visual layers, and rebuild native editable text.
4. Use state scripts to record dispatch, imagegen results, page results, repair, and accepted status.
5. Assemble the final `.pptx`, copy `.pptx` speaker notes when present, and run deck validation.

## Output Layout

Use one isolated output directory per conversion. All intermediate files and final outputs stay inside it:

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

## QA And Validation

- `validate_pptx.py` allows an `imagegen-clean-background` full-slide bottom image under native editable text.
- `validate_pptx.py` rejects original `source.png` or source-derived/user raster full-slide backgrounds under native text.
- `validate_pptx.py` rejects `.svg` as an imagegen-first complex visual asset.
- Every page must record `visual_layer_plan`, `background_strategy`, `visual_inventory`, and imagegen visual-layer quality checks.

## Repository Layout

```text
.
├── .github/                              # GitHub workflows and repository checks
├── assets/                               # README examples and explanatory material
├── skills/
│   └── image-to-editable-ppt/            # Installable Codex skill
│       ├── SKILL.md
│       ├── requirements.txt
│       ├── agents/
│       ├── prompts/
│       ├── references/
│       └── scripts/
├── tests/                                # Repository-level script and contract tests
├── AGENTS.md
├── CHANGELOG.md
├── LICENSE
├── README.md
└── README_en.md
```

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Bronto-p/image-to-editable-ppt-skill&type=Date)](https://www.star-history.com/#Bronto-p/image-to-editable-ppt-skill&Date)

## License

MIT
