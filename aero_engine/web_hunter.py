import os
import time
from pathlib import Path
from typing import Optional, List, Dict
from PIL import Image, ImageDraw, ImageFont
import urllib.parse

def build_mobile_browser_frame(web_shot_path: Path, out_path: Path, url_label: str = "🔒 news.com") -> Path:
    im_mob = Image.open(web_shot_path)
    target_w = 576
    aspect = im_mob.height / im_mob.width
    target_h = int(target_w * aspect)
    mob_scaled = im_mob.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    canvas = Image.new("RGB", (576, 1024), (255, 255, 255))
    draw = ImageDraw.Draw(canvas)
    
    # Mobile Status Bar (y=0..40)
    draw.rectangle((0, 0, 576, 88), fill=(246, 246, 248))
    draw.text((36, 12), "9:41", fill=(18, 18, 20))
    # Dynamic Island
    draw.rounded_rectangle((228, 8, 348, 28), radius=10, fill=(0, 0, 0))
    # Battery icon
    draw.rectangle((510, 14, 536, 26), outline=(20, 20, 20), width=2)
    draw.rectangle((512, 16, 530, 24), fill=(20, 20, 20))
    draw.rectangle((536, 18, 538, 22), fill=(20, 20, 20))
    
    # Safari Mobile Address Bar (y=40..80)
    draw.rounded_rectangle((24, 40, 552, 80), radius=16, fill=(232, 233, 238))
    draw.text((220, 50), url_label, fill=(50, 52, 60))
    draw.ellipse((520, 54, 532, 66), fill=(140, 145, 155))
    
    # Paste mobile webpage at y=88
    canvas.paste(mob_scaled, (0, 88))
    canvas.save(out_path)
    return out_path

def build_desktop_browser_frame(web_shot_path: Path, out_path: Path, url_label: str = "https://news.com/article", tab_title: str = "Breaking News") -> Path:
    im_desk = Image.open(web_shot_path)
    target_w = 1280
    target_h = 720
    
    canvas = Image.new("RGB", (target_w, target_h), (240, 242, 245))
    draw = ImageDraw.Draw(canvas)
    
    header_h = 82
    draw.rectangle((0, 0, target_w, header_h), fill=(232, 234, 237))
    
    # macOS window buttons
    draw.ellipse((16, 14, 28, 26), fill=(255, 95, 87))   # Close (red)
    draw.ellipse((36, 14, 48, 26), fill=(254, 188, 46))  # Minimize (yellow)
    draw.ellipse((56, 14, 68, 26), fill=(40, 200, 64))   # Zoom (green)
    
    # Active Browser Tab
    draw.rounded_rectangle((80, 8, 320, 42), radius=8, fill=(255, 255, 255))
    draw.text((100, 16), f"🌐 {tab_title[:24]}", fill=(30, 30, 35))
    
    # URL Navigation Bar
    draw.rounded_rectangle((120, 46, target_w - 60, 76), radius=15, fill=(255, 255, 255), outline=(218, 220, 224), width=1)
    draw.text((140, 52), f"🔒 {url_label[:75]}", fill=(60, 64, 67))
    
    # Scale webpage to fit remainder
    content_h = target_h - header_h
    aspect = im_desk.height / im_desk.width
    scaled_h = int(target_w * aspect)
    desk_scaled = im_desk.resize((target_w, max(content_h, scaled_h)), Image.Resampling.LANCZOS)
    cropped_desk = desk_scaled.crop((0, 0, target_w, content_h))
    
    canvas.paste(cropped_desk, (0, header_h))
    canvas.save(out_path)
    return out_path

def search_duckduckgo_news(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=max_results))
            if results:
                return [{"title": r.get("title", ""), "url": r.get("url", ""), "body": r.get("body", "")} for r in results]
            
            # Fallback to standard text search
            text_results = list(ddgs.text(f"{query} news", max_results=max_results))
            return [{"title": r.get("title", ""), "url": r.get("href", ""), "body": r.get("body", "")} for r in text_results]
    except Exception as e:
        print(f"DuckDuckGo search error: {e}")
        return []

def capture_smart_webpage(
    url: str,
    out_path: Path,
    aspect_ratio: str = "vertical",
    timeout_sec: int = 15
) -> Optional[Path]:
    """
    Spawns headless Firefox with Geckodriver, applies DOM Smart Auto-Framing
    to eliminate whitespace and overlays, then captures a clean screenshot.
    """
    try:
        from selenium import webdriver
        from selenium.webdriver.firefox.options import Options
    except ImportError:
        print("Selenium indisponível nesta plataforma; captura de página ignorada.")
        return None

    options = Options()
    options.add_argument("--headless")
    
    is_vertical = (aspect_ratio == "vertical")
    if is_vertical:
        # iPhone 15 Pro viewport
        options.set_preference("general.useragent.override", "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
        window_w, window_h = 430, 932
    else:
        # Desktop viewport
        options.set_preference("general.useragent.override", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        window_w, window_h = 1280, 720
        
    driver = None
    try:
        driver = webdriver.Firefox(options=options)
        driver.set_window_size(window_w, window_h)
        driver.get(url)
        time.sleep(3.0)
        
        # Smart Auto-Framing JS script
        auto_frame_js = """
        try {
            // Remove floating cookie banners and sticky overlays
            const killSelectors = [
                '#onetrust-consent-sdk', '.cookie-banner', '[id*="cookie"]', '[class*="consent"]',
                '.ad-banner', '[id*="modal"]', '[class*="modal"]', '.advertisement'
            ];
            killSelectors.forEach(sel => {
                document.querySelectorAll(sel).forEach(el => el.remove());
            });

            // Find H1 headline
            const h1 = document.querySelector('h1') || document.querySelector('article h2');
            if (h1) {
                const rect = h1.getBoundingClientRect();
                const headers = Array.from(document.querySelectorAll('header, nav, .header, .nav'));
                let headerBottom = 0;
                headers.forEach(h => {
                    const r = h.getBoundingClientRect();
                    if (r.top < 100 && r.bottom > headerBottom && r.bottom < 250) {
                        headerBottom = r.bottom;
                    }
                });
                const emptyGap = rect.top - headerBottom;
                if (emptyGap > 30) {
                    window.scrollBy(0, emptyGap - 15);
                }
            }
        } catch(e) {}
        """
        driver.execute_script(auto_frame_js)
        time.sleep(1.0)
        
        out_path.parent.mkdir(parents=True, exist_ok=True)
        driver.save_screenshot(str(out_path))
        return out_path
    except Exception as e:
        print(f"Error capturing webpage {url}: {e}")
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
