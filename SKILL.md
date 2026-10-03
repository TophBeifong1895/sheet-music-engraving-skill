---
name: sheet-music-engraving
description: 把简谱（数字谱）或旋律素材转写、校验并排印成专业五线谱 PDF 的完整工作流。当用户要求制作/整理/打印乐谱（小提琴谱、歌曲谱等）、把简谱转成五线谱、检查谱子节奏/拍数/升降号是否正确、或需要用 ABC notation / verovio 打谱排印时使用。Use for jianpu transcription, sheet-music typesetting, rhythm/bar validation, accidental audits, and ABC-to-PDF engraving.
---

# 简谱转写与五线谱排印

## 总流程

1. **获取可靠源谱**：优先直接找到目标乐器的现成谱；找不到再选权威演唱/演奏版简谱转写。保存原图到工作区，记录来源。
2. **识读简谱**（规则与技巧见 [references/jianpu-reading.md](references/jianpu-reading.md)）：按系统裁图、逐小节写下"简谱记号 → ABC"，**每小节当场算拍数**，必须等于拍号；疑点回原图未缩放像素核对。
3. **写 ABC**（纪律见 [references/abc-and-verovio.md](references/abc-and-verovio.md)）：单旋律谱用 `M:4/4 L:1/8 K:<调>`；调号覆盖的升降号一律不写。
4. **机械校验**：`python scripts/check_bars.py tune.abc`——除设计内的弱起/变拍/反复结尾外必须全部满拍；`python scripts/check_range.py tune.abc`——每个音必须在目标乐器音域内（默认小提琴 G3–E7，可 `--instrument viola` 等）；再做升降号审计 `grep -o '[\^_=][A-Ga-g]' tune.abc | sort | uniq -c`。
5. **排印**：`python scripts/abc_to_pdf.py tune.abc --title ... --out tune.pdf`。
6. **视觉验收**：PDF 逐页渲染 PNG 抽查（谱面铺满页宽、无大留白、升降号只在调号、变拍/反复/延音线渲染正常、最低音不低于乐器下限——小提琴谱上不允许出现超过下加二线的音）。

## 铁律（每条都对应过真实交付事故）

- **节奏不是转写完就完事**：简谱转写的节奏层极易大面积出错（16 分 vs 32 分、附点丢失、增时线漏看）。没有通过 check_bars.py 全量验证的谱子不得交付。
- **调号内的升降号写进 ABC = 每个音符旁都出现 ♯/♭**。只有调号外的临时变音才允许显式标注。
- **放大图不可信**：平滑放大的裁切图会伪造/吞掉附点和减时线。任何节拍疑点，回到原图原生像素 `Image.NEAREST` 放大核对，并用小节拍数反推消歧。
- **排版问题先怀疑管线**：谱面只占页面一部分、五线谱线消失，是 verovio 嵌套 SVG 与 `currentColor` 的已知坑，scripts/abc_to_pdf.py 已修复，不要绕过它手改 SVG。
- **用户说"拍子不对"时，先机械验证再回答**，不要凭印象辩护。
- **音域必须在交付前机检**：从声乐谱转写时，原唱低于乐器下限的音（如女低音旋律里的 D3/E3/F#3 之于小提琴 G3 下限）会被原样搬进谱面。简谱里"带一个低音点"到底是哪个八度，要结合主音域判断：歌曲主音域在 G4 附近时，5̠=D4 而不是 D3——ABC 里写成 `D,`（D3）就是整整低了一个八度，五线谱上会掉到下加三线以外。修正手法：越界音上移八度；含越界音的短句整体移一个八度以保持句内平滑；滑音装饰音里的越界音可改用空弦音（如 `{B,D,}` → `{B,G,}`）。

## 脚本

- `scripts/check_bars.py <abc...>`：逐小节累加时值并对照当前拍号（跟踪 `[M:]` 变拍）；OVER 必错，short 需人工确认是设计内（弱起/变拍/反复）。OVER 时退出码为 1。
- `scripts/check_range.py <abc...> [--min G3 --max E7 | --instrument violin|viola|cello|flute]`：逐音核对乐器音域（默认小提琴 G3–E7），越界音带小节号打印，退出码为 1。装饰音/滑音里的越界音也会被检出。
- `scripts/abc_to_pdf.py <abc> [--title --subtitle --left --right --out --scale --spacing-system ...]`：ABC → A4 PDF，含标题区与全部管线修复。依赖 verovio、svglib、reportlab 及一个 CJK 字体。

## 参考资料

- 简谱记号规则、识读流程、消歧技巧、高发错误清单：[references/jianpu-reading.md](references/jianpu-reading.md)
- ABC 书写纪律、排印管线的坑与修复、版式参数起点、交付核验清单：[references/abc-and-verovio.md](references/abc-and-verovio.md)
