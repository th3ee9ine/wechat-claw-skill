# AI配图 Prompt 参考库

## 封面图 Prompt 模板

### AI日报封面
```
A futuristic AI daily news cover image for [DATE]. Dark blue and purple gradient background with glowing neural network nodes and circuit patterns. Center text area with '🤖 AI日报' in large bold white Chinese characters and '[DATE]' below in smaller text. Modern tech aesthetic with subtle holographic effects. Clean, professional magazine cover style. 16:9 aspect ratio suitable for WeChat article cover.
```

### 财经周报封面
```
A dramatic financial news magazine cover for [DATE]. Dark red and black gradient background with oil barrel silhouettes and stock market chart lines falling. Globe showing [REGION] highlighted in red. Center text '📊 财经周报' in large bold white Chinese characters and '[DATE]' below. Urgent, serious tone like The Economist or Bloomberg Businessweek cover. Professional magazine style. 16:9 aspect ratio for WeChat article cover.
```

### 科技周报封面
```
A sleek technology weekly cover for [DATE]. Deep dark blue background with holographic chip circuits and data streams. Center text '🔬 科技周报' in large bold white Chinese characters. Futuristic, clean design inspired by WIRED magazine. 16:9 aspect ratio.
```

## 正文配图 Prompt 模板

### 地缘政治/能源危机
```
Dramatic aerial view of [LOCATION] with massive oil tankers stuck in a bottleneck. Dark stormy sky with orange fire glow on the horizon. Military ships patrolling. Photorealistic, cinematic lighting, news photography style. Wide angle shot.
```

### 股市/金融市场
```
Modern [COUNTRY] stock exchange trading floor with large digital screens showing [green upward/red downward] arrows on [SECTOR] stocks. Traders looking at screens with [SPECIFIC] charts. Professional financial photography style. Warm lighting, busy atmosphere.
```

### 科技/AI
```
Futuristic AI laboratory with holographic displays showing [SPECIFIC TECH]. Scientists in modern lab coats interacting with floating data visualizations. Blue and white color scheme. Clean, high-tech atmosphere. Cinematic lighting.
```

### 政策/会议
```
Grand government conference hall with [COUNTRY] flags. Officials at a long table with microphones. Large screen showing [TOPIC] data charts. Formal, authoritative atmosphere. News photography style.
```

### 下周前瞻/事件预览
```
Split screen infographic style image. Left side: [EVENT_1 VISUAL]. Right side: [EVENT_2 VISUAL]. Connected by a glowing timeline bar showing 'Week Ahead [DATE_RANGE]'. Dark blue professional financial media style, clean modern design.
```

### 数据/图表场景
```
Clean data visualization dashboard on a large curved monitor. Multiple charts showing [SPECIFIC DATA]. Dark background with glowing blue and green data points. Modern fintech aesthetic. Professional, clean design.
```

## Prompt 写作原则

1. **具体化**：避免模糊描述，给出具体场景、颜色、构图
2. **风格锚定**：引用知名出版物风格（The Economist, Bloomberg, WIRED）
3. **比例指定**：封面图用 16:9，正文配图默认 16:9 或 4:3
4. **色调一致**：同一篇文章的配图保持色调统一
5. **避免文字**：AI生成的图片中文字容易出错，尽量避免在prompt中要求文字（封面图除外）
6. **标注来源**：配图下方统一标注"AI 生成"

## 生成命令

```bash
# 封面图（上传为永久素材）
uv run {nanobanana}/scripts/generate_image.py --prompt "..." --filename "/tmp/cover-[DATE].png" --resolution 1K
uv run {wechat-mp}/scripts/wechat_mp.py upload-image /tmp/cover-[DATE].png

# 正文配图（上传获取CDN URL）
uv run {nanobanana}/scripts/generate_image.py --prompt "..." --filename "/tmp/img-[NAME].png" --resolution 1K
uv run {wechat-mp}/scripts/wechat_mp.py upload-content-image /tmp/img-[NAME].png
```

## 嵌入HTML

```html
<section style="background: #ffffff; padding: 15px 20px; text-align: center;">
<img src="微信CDN_URL" style="width: 100%; border-radius: 4px; margin: 0;" />
<p style="font-size: 11px; color: #999; text-align: center; margin: 5px 0 0; font-style: italic;">图片说明 | AI 生成</p>
</section>
```
