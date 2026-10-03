# sheet-music-engraving

Kimi skill：把简谱（数字谱）转写、校验并排印成专业五线谱 PDF 的完整工作流。
方法论提炼自真实交付事故（节奏大面积错误、调号内升号被逐音标注、谱面排版塌陷、声乐谱音域低于小提琴下限），
每条规则都对应一个踩过的坑。

## 内容

```
SKILL.md                        工作流与铁律
references/jianpu-reading.md    简谱记号规则、识读流程、消歧技巧、高发错误清单
references/abc-and-verovio.md   ABC 书写纪律、verovio→PDF 管线的坑与修复、版式参数
scripts/check_bars.py           小节拍数校验器（跟踪 [M:] 变拍，OVER 必错）
scripts/check_range.py          乐器音域校验器（默认小提琴 G3–E7，越界音带小节号打印）
scripts/abc_to_pdf.py           ABC → A4 PDF 排印（含嵌套 SVG / currentColor / CJK 字体修复）
```

## 用法

```bash
# 校验：除设计内的弱起/变拍外，每小节必须满拍
python scripts/check_bars.py tune.abc

# 校验：每个音必须在目标乐器音域内
python scripts/check_range.py tune.abc                      # 默认小提琴
python scripts/check_range.py tune.abc --instrument viola   # 中提琴等

# 排印
python scripts/abc_to_pdf.py tune.abc --title 敕勒歌 --subtitle 小提琴独奏谱 \
    --left "刘洲 曲" --right "四分音符= 64（约）　D 大调" --out tune.pdf
```

依赖：`verovio`、`svglib`、`reportlab`，以及一个 CJK 字体（Windows 默认用微软雅黑）。

## 安装为 Kimi skill

把本仓库内容打包为 zip 并改名为 `sheet-music-engraving.skill`，
或将 `SKILL.md` 所在目录放到 Kimi 的 skills 目录（如 `~/.config/agents/skills/sheet-music-engraving/`）。
