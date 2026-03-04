#!/usr/bin/env python3
"""
全局加载性能优化 v2
1. 修复剩余视频：preload=none + 延迟加载
2. 所有动画元素添加 will-change: transform, opacity（通过全局 CSS 注入）
3. index.html iframe 预加载策略优化
"""
import os, re

ACTIVE = [
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

# 全局注入的 CSS：开启 GPU 加速，减少重绘
GLOBAL_PERF_CSS = """
    /* === 全局性能优化 === */
    /* 动画元素 GPU 加速 */
    [class*="anim"], [class*="fade"], [class*="slide-in"],
    [class*="float"], [class*="pulse"], [class*="glow"],
    [class*="spin"], [class*="rotate"], [class*="bounce"],
    .card, .metric-card, .track-card, .stat-box,
    .nav-dot, .timeline-node {
        will-change: transform, opacity;
        transform: translateZ(0);
    }
    /* 视频容器 GPU 加速 */
    video { transform: translateZ(0); }
    /* 减少字体渲染开销 */
    body { text-rendering: optimizeSpeed; -webkit-font-smoothing: antialiased; }
"""

# 延迟加载视频的 JS 片段
LAZY_VIDEO_JS = """
<script>
(function(){
  // 延迟加载非背景视频（内容视频）
  function lazyLoadVideos(){
    document.querySelectorAll('video[data-lazy-src]').forEach(function(v){
      var src = v.getAttribute('data-lazy-src');
      if(src){ v.src = src; v.removeAttribute('data-lazy-src'); v.load(); }
    });
    document.querySelectorAll('video source[data-lazy-src]').forEach(function(s){
      var src = s.getAttribute('data-lazy-src');
      if(src){ s.src = src; s.removeAttribute('data-lazy-src'); s.parentElement.load(); }
    });
  }
  if(document.readyState === 'complete'){
    setTimeout(lazyLoadVideos, 500);
  } else {
    window.addEventListener('load', function(){ setTimeout(lazyLoadVideos, 500); });
  }
})();
</script>
"""

changed = 0

for fname in ACTIVE:
    fpath = os.path.join(BASE, fname)
    if not os.path.exists(fpath):
        print(f"  SKIP: {fname}")
        continue

    html = open(fpath, encoding="utf-8").read()
    original = html

    # ── 1. 注入全局性能 CSS（在 </style> 前，只注入一次）──
    if "全局性能优化" not in html:
        # 找到第一个 </style> 并在其前插入
        html = html.replace("</style>", GLOBAL_PERF_CSS + "\n    </style>", 1)

    # ── 2. 修复未处理的视频：添加 preload=none ──
    # 处理 <video autoplay ...> 没有 data-autoplay 且没有 preload=none 的
    def fix_video_tag(m):
        tag = m.group(0)
        if 'preload=' not in tag and 'data-autoplay' not in tag:
            # 背景视频（video-bg 类）已处理过，这里处理内容视频
            if 'video-bg' in tag or 'video-bg-static' in tag:
                return tag  # 已由上一轮处理
            # 内容视频：添加 preload=none，保留 autoplay（用户可见时需要播放）
            tag = tag.replace('autoplay', 'autoplay preload="none"', 1)
        return tag

    html = re.sub(r'<video\b[^>]*>', fix_video_tag, html)

    # ── 3. platform_overview.html 特殊处理：内容视频延迟加载 ──
    if fname == "platform_overview.html":
        # 将内容视频的 src 改为 data-lazy-src
        def lazy_content_video_src(m):
            tag = m.group(0)
            if 'data-lazy-src' not in tag and 'data-src' not in tag:
                tag = re.sub(r'\bsrc="(assets/[^"]+)"', r'data-lazy-src="\1"', tag)
            return tag
        # 只处理 <source> 标签中的本地 assets 路径
        html = re.sub(r'<source\s+src="(assets/[^"]+)"', r'<source data-lazy-src="\1"', html)
        # 注入延迟加载 JS（如果还没有）
        if "lazyLoadVideos" not in html:
            html = html.replace("</body>", LAZY_VIDEO_JS + "</body>")

    if html != original:
        open(fpath, "w", encoding="utf-8").write(html)
        print(f"  OPTIMIZED: {fname}")
        changed += 1
    else:
        print(f"  NO CHANGE: {fname}")

print(f"\nDone: {changed} files optimized.")
