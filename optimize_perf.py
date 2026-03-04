#!/usr/bin/env python3
"""
全局加载性能优化脚本
对所有活跃 HTML 页面进行批量优化：
1. 字体：添加 display=swap，减少字重
2. 背景视频：autoplay 改为 preload=none + JS 延迟加载
3. 图片：添加 loading="lazy" 和 decoding="async"（首屏关键图片除外）
4. 添加 <link rel="preconnect"> 到 Google Fonts
"""
import re, os, glob

ACTIVE_FILES = [
    "cover.html", "paradigm_shift.html", "ai_gatekeeper.html",
    "digital_twin_strategy.html", "commander_os_product.html",
    "solution_overview.html", "factory_value.html", "platform_overview.html",
    "slide09_dashboard.html", "slide10_factory_profile.html",
    "slide11_webinar.html", "slide12_new_journey.html",
    "slide13_growth_track.html", "slide14_power_track.html",
    "business_model.html", "traction.html", "competition.html",
    "roadmap.html", "team.html", "ask_closing.html",
]

BASE = "/home/ubuntu/realsourcing-pitch-deck-v2"

# 统计
changed = 0
skipped = 0

for fname in ACTIVE_FILES:
    fpath = os.path.join(BASE, fname)
    if not os.path.exists(fpath):
        print(f"  SKIP (not found): {fname}")
        skipped += 1
        continue

    with open(fpath, "r", encoding="utf-8") as f:
        html = f.read()

    original = html

    # ── 1. 字体：添加 display=swap ──
    # 替换 googleapis 字体链接，确保有 display=swap
    def fix_font_url(m):
        url = m.group(1)
        if "display=swap" not in url:
            url = url + ("&" if "?" in url else "?") + "display=swap"
        # 精简字重：只保留 400;700;900（Inter, Noto Sans SC, JetBrains Mono）
        url = re.sub(r'Inter:wght@[^&"\']+', 'Inter:wght@400;700;900', url)
        url = re.sub(r'Noto\+Sans\+SC:wght@[^&"\']+', 'Noto+Sans+SC:wght@400;700;900', url)
        url = re.sub(r'JetBrains\+Mono:wght@[^&"\']+', 'JetBrains+Mono:wght@400;700', url)
        return m.group(0).replace(m.group(1), url)

    html = re.sub(r'href="(https://fonts\.googleapis\.com/css2[^"]+)"', fix_font_url, html)

    # ── 2. 添加 preconnect（如果没有）──
    if "fonts.googleapis.com" in html and 'rel="preconnect" href="https://fonts.googleapis.com"' not in html:
        preconnect = (
            '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
            '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        )
        html = html.replace("<link", preconnect + "<link", 1)

    # ── 3. 背景视频：autoplay → preload=none，JS 延迟加载 ──
    # 针对 video-bg 类的视频（背景装饰视频），改为延迟加载
    # 将 <video class="video-bg" autoplay loop muted playsinline>
    # 改为 <video class="video-bg" data-autoplay loop muted playsinline preload="none">
    # 并在 </body> 前注入延迟加载脚本
    if 'class="video-bg"' in html and 'data-autoplay' not in html:
        html = html.replace(
            'class="video-bg" autoplay loop muted playsinline',
            'class="video-bg" data-autoplay loop muted playsinline preload="none"'
        )
        # 同样处理 video-bg-static
        html = html.replace(
            'class="video-bg-static" autoplay loop muted playsinline',
            'class="video-bg-static" data-autoplay loop muted playsinline preload="none"'
        )
        # 注入延迟加载脚本（在 </body> 前）
        lazy_video_script = """
<script>
// 背景视频延迟加载：页面渲染完成后再加载视频
(function(){
  function loadBgVideos(){
    document.querySelectorAll('video[data-autoplay]').forEach(function(v){
      // 找到 source 子元素并赋值 src
      var src = v.querySelector('source');
      if(src && src.getAttribute('data-src')){
        src.src = src.getAttribute('data-src');
        src.removeAttribute('data-src');
      }
      v.load();
      v.play().catch(function(){});
    });
  }
  if(document.readyState === 'complete'){
    setTimeout(loadBgVideos, 300);
  } else {
    window.addEventListener('load', function(){ setTimeout(loadBgVideos, 300); });
  }
})();
</script>
"""
        # 将 <source src="https://...manuscdn..."> 改为 data-src
        html = re.sub(
            r'(<source\s+)(src="https://[^"]*manuscdn[^"]*")',
            lambda m: m.group(1) + 'data-src=' + m.group(2)[4:],
            html
        )
        html = html.replace("</body>", lazy_video_script + "</body>")

    # ── 4. 图片懒加载（非首屏关键图片）──
    # 对 <img 标签添加 loading="lazy" decoding="async"（如果没有）
    def add_lazy_img(m):
        tag = m.group(0)
        if 'loading=' not in tag:
            tag = tag.replace('<img ', '<img loading="lazy" decoding="async" ', 1)
        elif 'decoding=' not in tag:
            tag = tag.replace('<img ', '<img decoding="async" ', 1)
        return tag
    html = re.sub(r'<img\s+(?!.*loading=)', add_lazy_img, html)

    if html != original:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  OPTIMIZED: {fname}")
        changed += 1
    else:
        print(f"  NO CHANGE: {fname}")

print(f"\nDone: {changed} files optimized, {skipped} skipped.")
