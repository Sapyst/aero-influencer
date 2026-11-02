import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter

class SEOPackage:
    def __init__(
        self,
        title: str,
        description: str,
        tags: List[str],
        hashtags: List[str],
        sources: List[str],
        thumbnail_path: Optional[Path] = None
    ):
        self.title = title
        self.description = description
        self.tags = tags
        self.hashtags = hashtags
        self.sources = sources
        self.thumbnail_path = thumbnail_path

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "hashtags": self.hashtags,
            "sources": self.sources,
            "thumbnail": str(self.thumbnail_path) if self.thumbnail_path else None
        }

def generate_seo_package(
    topic: str,
    script_beats: List[Dict],
    sources: List[str],
    video_type: str = "shorts",
    api_key: Optional[str] = None
) -> Dict:
    """
    Generates high-CTR SEO title, comprehensive YouTube description with timestamps,
    hashtags, and relevant search tags.
    """
    clean_topic = topic.strip().title()
    is_shorts = (video_type == "shorts")
    
    if is_shorts:
        title = f"{clean_topic}?! 😱 #shorts"
        if len(title) > 60:
            title = f"{clean_topic[:45]}... 😱 #shorts"
            
        desc = (
            f"Você sabia sobre isso? A verdade chocante sobre {clean_topic}!\n\n"
            f"Curtiu a curiosidade? Inscreva-se e ative o sininho para mais fatos do mundo tech!\n\n"
            f"📌 Fontes e Referências:\n" + "\n".join([f"- {s}" for s in sources[:4]]) + "\n\n"
            f"#shorts #tecnologia #curiosidades #noticias #aerointeligencia"
        )
        tags = [
            topic.lower(), "shorts", "tecnologia", "curiosidades",
            "fatos desconhecidos", "cibersegurança", "inovação", "viral"
        ]
        hashtags = ["#shorts", "#tecnologia", "#curiosidades", "#viral"]
    else:
        title = f"Como {clean_topic} Aconteceu: A Investigação Completa"
        desc = (
            f"Neste documentário investigativo, desvendamos todos os detalhes sobre {clean_topic}.\n\n"
            f"⏱️ Capítulos:\n"
            f"0:00 - Introdução e o Mistério\n"
            f"0:45 - O Contexto da Infraestrutura\n"
            f"1:30 - Como a Falha Ocorreu\n"
            f"2:15 - Consequências e Danos Globais\n"
            f"3:00 - Conclusão e Futuro\n\n"
            f"📌 Fontes Investigadas:\n" + "\n".join([f"- {s}" for s in sources[:6]]) + "\n\n"
            f"Deixe seu like e inscreva-se para mais investigações aprofundadas!\n\n"
            f"#documentario #tecnologia #investigacao #noticias #analise"
        )
        tags = [
            topic.lower(), "documentario", "investigacao", "tecnologia",
            "segurança da informacao", "analise completa", "noticias tech"
        ]
        hashtags = ["#documentario", "#tecnologia", "#investigacao", "#analise"]

    return {
        "title": title,
        "description": desc,
        "tags": tags,
        "hashtags": hashtags,
        "sources": sources
    }

def generate_click_thumbnail(
    topic: str,
    mascot_sprite_path: Path,
    bg_frame_path: Path,
    out_thumb_path: Path,
    aspect_ratio: str = "vertical"
) -> Path:
    """
    Renders an eye-catching YouTube thumbnail:
    - High-contrast background with subtle vignette
    - Cutout character with radiant contour / glow
    - Bold attention-grabbing headline text
    """
    is_vertical = (aspect_ratio == "vertical")
    w, h = (576, 1024) if is_vertical else (1280, 720)
    
    # Base background
    if bg_frame_path.exists():
        bg = Image.open(bg_frame_path).convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
    else:
        bg = Image.new("RGBA", (w, h), (18, 18, 28, 255))

    # Dark overlay for contrast
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 75))
    bg.paste(overlay, (0, 0), overlay)
    
    # Mascot Cutout
    if mascot_sprite_path.exists():
        sprite = Image.open(mascot_sprite_path).convert("RGBA")
        bbox = sprite.getbbox()
        if bbox:
            sprite = sprite.crop(bbox)
        
        target_h = int(h * 0.65)
        target_w = int(target_h * (sprite.width / sprite.height))
        sprite_resized = sprite.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
        # Mascot Glow / Shadow
        alpha = sprite_resized.split()[3]
        glow_alpha = alpha.filter(ImageFilter.GaussianBlur(radius=8))
        glow_layer = Image.new("RGBA", (target_w, target_h), (155, 114, 207, 180))
        glow_img = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
        glow_img.paste(glow_layer, (0, 0), glow_alpha)
        
        pos_x = w - target_w - (10 if is_vertical else 40)
        pos_y = h - target_h + (20 if is_vertical else 10)
        
        bg.paste(glow_img, (pos_x, pos_y), glow_img)
        bg.paste(sprite_resized, (pos_x, pos_y), sprite_resized)

    # Headline Text Box
    draw = ImageDraw.Draw(bg)
    headline = topic.upper()[:28]
    
    if is_vertical:
        box_y = 120
        draw.rounded_rectangle((24, box_y, w - 24, box_y + 90), radius=16, fill=(235, 30, 85, 230))
        draw.text((44, box_y + 26), headline, fill=(255, 255, 255))
    else:
        box_y = 80
        draw.rounded_rectangle((40, box_y, 720, box_y + 110), radius=20, fill=(235, 30, 85, 230))
        draw.text((64, box_y + 32), headline, fill=(255, 255, 255))

    out_thumb_path.parent.mkdir(parents=True, exist_ok=True)
    bg.convert("RGB").save(out_thumb_path, quality=95)
    return out_thumb_path

def upload_to_youtube_direct(
    video_path: Path,
    seo: Dict,
    thumbnail_path: Optional[Path] = None,
    client_secrets_file: Optional[Path] = None,
    privacy_status: str = "public"
) -> Dict:
    """
    Automated YouTube Upload via YouTube Data API v3.
    Can publish directly or schedule without any manual interaction.
    """
    if not client_secrets_file or not client_secrets_file.exists():
        return {
            "status": "manual_ready",
            "message": "Upload direto não configurado. Pacote SEO pronto para copiar e colar!",
            "video": str(video_path),
            "seo": seo
        }
    
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2.credentials import Credentials
        
        # Load stored credentials
        token_file = client_secrets_file.parent / "yt_token.json"
        if not token_file.exists():
            return {
                "status": "auth_needed",
                "message": "Autenticação do canal do YouTube pendente."
            }
            
        with open(token_file) as f:
            creds_data = json.load(f)
        creds = Credentials.from_authorized_user_info(creds_data)
        
        youtube = build("youtube", "v3", credentials=creds)
        
        body = {
            "snippet": {
                "title": seo["title"],
                "description": seo["description"],
                "tags": seo["tags"],
                "categoryId": "28"  # Science & Technology
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False
            }
        }
        
        media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        
        video_id = response.get("id")
        video_url = f"https://youtu.be/{video_id}"
        
        # Upload Thumbnail if provided
        if thumbnail_path and thumbnail_path.exists() and video_id:
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/png")
                ).execute()
            except Exception as e:
                print(f"Thumbnail upload warning: {e}")
                
        return {
            "status": "published",
            "video_id": video_id,
            "url": video_url,
            "message": f"Vídeo publicado com sucesso no YouTube: {video_url}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro no upload do YouTube: {str(e)}",
            "seo": seo
        }
