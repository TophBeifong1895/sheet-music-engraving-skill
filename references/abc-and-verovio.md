# ABC 记谱规范与 verovio→PDF 排印要点

## ABC 书写纪律（违反任意一条，谱面就会出典型错误）

1. **调号覆盖的升降号绝不写进音符**。K:D 里 F、C 自动是 F♯、C♯，写 `F` 不写 `^F`。
   - ABC 标准里 `^F` 是"显式临时变音"，verovio 会老老实实把 ♯ 渲染在每个音符旁。
   - 交稿前做一次审计：`grep -o '[\^_=][A-Ga-g]' file.abc | sort | uniq -c`，确认剩下的显式变音都是调号之外的**真**临时变音（如 G♯、还原记号）。
2. **选定 L: 后，裸字母 = 默认时值**。L:1/8 下 `A`=八分、`A2`=四分、`A/`=十六分、`A3/`=附点八分。最易错的是句尾两个八分误加 `/` 变成两个十六分。
3. 音高八度：中音 `A B c d`，低八度加 `,`（`A,`），高八度小写/加 `'`（`a`、`c'`）。
4. 装饰音零时值：`{^FA}` `{d}` `{B,D,}`，不参与小节拍数。
5. 结构记号：弱起直接写不完全小节；反复 `|: ... :|`；房子 `[1` `[2`；中途变拍 `[M:2/4]`（写在小节内）；力度 `!p! !mp! !mf! !f!`；文字提示 `"^rit."` `"^原速"`；波音 `!mordent!`；延长 `!fermata!`。
6. 头部字段顺序：`X T C Z M L Q K`（K: 必须是最后一个头字段）。
7. 速度文本不要直接用 `♩` 字符进 PDF 标题——很多 CJK 字体（如微软雅黑 Light）没有该字形；写"四分音符= 64"。

## 排印管线（scripts/abc_to_pdf.py 已封装）

`ABC → verovio(SVG) → flatten_nested_svg → svglib → reportlab(A4 PDF)`

必须知道的三个坑（脚本已修复，改管线时不要回退）：

1. **嵌套 SVG 缩放错误**：verovio 每页输出 `<svg class="definition-scale" viewBox>` 嵌套层，svglib 会错误缩放，导致整个谱面系统只占页宽约 68%（"音符又小又密、页面大片留白"的根因）。修复：把嵌套层替换为 `<g color="black" transform="scale(sx,sy)">`。
2. **五线谱线消失**：verovio 的 CSS 用 `stroke:currentColor`，svglib 不解析。上面 `<g color="black">` 一并解决。
3. **中文标题**：reportlab 内置字体无 CJK，需注册外部 TTF/TTC（Windows 用 `C:\Windows\Fonts\msyh.ttc`，`subfontIndex=0`）。

## 版式参数起点（A4，歌曲长度独奏谱）

| 参数 | 起点值 | 调整方向 |
|---|---|---|
| pageWidth / pageHeight | 1160 / 1770 | 谱面密度整体过小时同步调大 |
| scale | 60 | 音符大小 |
| spacingSystem | 10 | 行距；末页太空→加大，过挤→减小 |
| spacingStaff | 9 | 五线谱内部间距 |

验收标准：逐页渲染成 PNG 抽查——谱面横向铺满页宽、每行 2–3 小节、无大面积留白、升降号只出现在调号处、每小节拍数经 check_bars.py 验证。

## 交付前核验清单

1. `python scripts/check_bars.py tune.abc`：除弱起/变拍/反复结尾等**设计内**不完全小节外，无 OVER、无非预期 short。
2. 升降号审计（见上）只剩真临时变音。
3. PDF 渲染成图逐页目检：拍号只在调号变更处出现、变拍小节（如 2/4）排版正常、延音线/反复/房子渲染正确。
