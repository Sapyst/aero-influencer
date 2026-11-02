import json
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class SceneBeat(BaseModel):
    beat_id: int
    narration: str = Field(description="Spoken text for this beat")
    emotion: str = Field(description="Nova emotion: neutral, thinking, explaining, pointing_left, pointing_up, shocked, confused, smug, waving, whispering, facepalm, mindblown, laughing")
    preferred_side: str = Field(default="right", description="'left' or 'right' screen side for Nova")
    visual_type: str = Field(default="web_news", description="'web_news' or 'ai_image'")
    news_search_query: str = Field(default="", description="Search query for DuckDuckGo/Web to capture real article")
    target_url: Optional[str] = Field(default=None, description="Direct URL if known")
    image_prompt: Optional[str] = Field(default="", description="Prompt for AI image if visual_type is ai_image")

class DirectorScript(BaseModel):
    title: str
    video_type: str
    aspect_ratio: str
    beats: List[SceneBeat]
    outro_call_to_action: str = "Want to know more curious things like this? Just follow!"

SYSTEM_PROMPT = """You are the master creative director and screenwriter for 'AeroInfluencer', an autonomous video engine featuring Nova (a 2D doodle cartoon mascot girl in a lilac hoodie).

Your role is to produce a structured JSON screenplay based on the user's topic or news URL.
Nova's core personality: witty, curious, expressive, tech-savvy, slightly sarcastic commentary style.

Guidelines by Video Type:
1. 'shorts':
   - Duration: 30 to 45 seconds total (~75-100 words).
   - 4 to 6 rapid-fire beats.
   - Immediate high-retention hook (NO 'Hello guys' or 'Welcome to Nova').
   - Pacing: direct, shocking revelation, concrete numbers, brisk payoff.
   - Outro: Always end with 'Want to know more curious things like this? Just follow!'

2. 'full_video':
   - Duration: 2 to 4 minutes (~300-450 words).
   - 8 to 14 structured beats across narrative chapters:
     a) Dramatic Hook & The Mystery
     b) Context: What is this technology / company / event?
     c) The Incident Breakdown: Step-by-step what happened
     d) The Smoking Gun: Technical flaws, controller vulnerabilities, leaked data
     e) Global Consequences: Financial losses, government warnings, wider implications
     f) Thoughtful Closing Takeaway

Side Switching Rules for Nova:
- Start on 'right' by default.
- Switch to 'left' during:
  * Pattern interrupts: whispering secrets ('whispering'), cheeky smirks ('smug'), facepalm moments ('facepalm'), or mindblown revelations ('mindblown').
  * Contrasting two perspectives (e.g. Hacker point of view vs Victim point of view).
- Return to 'right' for the outro waving goodbye ('waving').
- Never switch back and forth on two consecutive short sentences.

Available Emotions:
['neutral', 'thinking', 'explaining', 'pointing_left', 'pointing_up', 'shocked', 'confused', 'smug', 'waving', 'whispering', 'facepalm', 'mindblown', 'laughing']

Return ONLY valid JSON matching the DirectorScript schema."""

def generate_script(
    topic: str,
    api_key: Optional[str],
    video_type: str = "shorts",
    aspect_ratio: str = "vertical"
) -> DirectorScript:
    if api_key and len(api_key.strip()) > 15:
        # 1. Try universal requests REST API (pure Python)
        try:
            import requests
            prompt = f"Topic/News: {topic}\nFormat: {video_type.upper()}\nAspect Ratio: {aspect_ratio}\nGenerate the complete screenplay JSON matching the DirectorScript schema."
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={api_key.strip()}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "generationConfig": {
                    "temperature": 0.7,
                    "responseMimeType": "application/json"
                }
            }
            r = requests.post(url, json=payload, timeout=25)
            if r.status_code == 200:
                res_data = r.json()
                cand_parts = res_data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                if cand_parts and "text" in cand_parts[0]:
                    data = json.loads(cand_parts[0]["text"])
                    return DirectorScript(**data)
        except Exception as e:
            print(f"Notice: Gemini REST attempt error ({e}), trying SDK fallback...")

        # 2. Try SDK if available
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=api_key.strip())
            prompt = f"Topic/News: {topic}\nFormat: {video_type.upper()}\nAspect Ratio: {aspect_ratio}\nGenerate the complete screenplay JSON."
            
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=DirectorScript,
                    temperature=0.7
                )
            )
            if response and response.text:
                data = json.loads(response.text)
                return DirectorScript(**data)
        except Exception as e:
            print(f"Warning: Gemini API error ({e}), generating template screenplay...")

    # Robust built-in fallback director
    if video_type == "shorts":
        return DirectorScript(
            title=f"The Truth About {topic}",
            video_type="shorts",
            aspect_ratio=aspect_ratio,
            outro_call_to_action="Want to know more curious things like this? Just follow!",
            beats=[
                SceneBeat(
                    beat_id=1,
                    narration=f"Wait... have you seen what is happening with {topic}?!",
                    emotion="shocked",
                    preferred_side="right",
                    visual_type="web_news",
                    news_search_query=f"{topic} latest overview",
                ),
                SceneBeat(
                    beat_id=2,
                    narration="New discoveries and official reports are revealing details that few people anticipated.",
                    emotion="pointing_left",
                    preferred_side="right",
                    visual_type="web_news",
                    news_search_query=f"{topic} report findings",
                ),
                SceneBeat(
                    beat_id=3,
                    narration="And here is the fascinating twist that is catching everyone by surprise.",
                    emotion="whispering",
                    preferred_side="left",
                    visual_type="web_news",
                    news_search_query=f"{topic} investigation",
                ),
                SceneBeat(
                    beat_id=4,
                    narration="The scale of this revelation is sparking discussions across the entire world!",
                    emotion="mindblown",
                    preferred_side="left",
                    visual_type="web_news",
                    news_search_query=f"{topic} global impact",
                ),
                SceneBeat(
                    beat_id=5,
                    narration="It completely changes how we understand this whole question.",
                    emotion="thinking",
                    preferred_side="right",
                    visual_type="web_news",
                    news_search_query=f"{topic} analysis",
                ),
                SceneBeat(
                    beat_id=6,
                    narration="Want to know more curious things like this? Just follow!",
                    emotion="waving",
                    preferred_side="right",
                    visual_type="web_news",
                    news_search_query=f"{topic}",
                )
            ]
        )
    else:
        # Full Content Video template (multi-beat documentary)
        return DirectorScript(
            title=f"The Deep Investigation: {topic}",
            video_type="full_video",
            aspect_ratio=aspect_ratio,
            outro_call_to_action="If you enjoyed this deep dive, subscribe for more in-depth investigations!",
            beats=[
                SceneBeat(
                    beat_id=1,
                    narration=f"Today we are exploring one of the most intriguing stories of our time: {topic}.",
                    emotion="explaining",
                    preferred_side="right",
                    visual_type="web_news",
                    news_search_query=f"{topic} overview",
                ),
                SceneBeat(
                    beat_id=2,
                    narration="To truly understand the implications, we first need to look at how this all began.",
                    emotion="thinking",
                    preferred_side="right",
                    visual_type="web_news",
                    news_search_query=f"{topic} origins history",
                ),
                SceneBeat(
                    beat_id=3,
                    narration="For years, conventional wisdom took this for granted, until recent evidence challenged old assumptions.",
                    emotion="pointing_left",
                    preferred_side="right",
                    visual_type="web_news",
                    news_search_query=f"{topic} research documentation",
                ),
                SceneBeat(
                    beat_id=4,
                    narration="Then, a series of surprising breakthroughs brought this topic directly into the global spotlight.",
                    emotion="shocked",
                    preferred_side="left",
                    visual_type="web_news",
                    news_search_query=f"{topic} breakthrough timeline",
                ),
                SceneBeat(
                    beat_id=5,
                    narration="When researchers and analysts examined the raw data, the findings were unprecedented.",
                    emotion="smug",
                    preferred_side="left",
                    visual_type="web_news",
                    news_search_query=f"{topic} discoveries findings",
                ),
                SceneBeat(
                    beat_id=6,
                    narration="Questions that previously seemed simple suddenly revealed unexpected layers of complexity.",
                    emotion="confused",
                    preferred_side="right",
                    visual_type="web_news",
                    news_search_query=f"{topic} key challenges",
                ),
                SceneBeat(
                    beat_id=7,
                    narration="The global interest and future potential surrounding this are now growing faster than ever.",
                    emotion="mindblown",
                    preferred_side="left",
                    visual_type="web_news",
                    news_search_query=f"{topic} future predictions",
                ),
                SceneBeat(
                    beat_id=8,
                    narration="If you enjoyed this investigative journey, make sure to follow for our next deep dive!",
                    emotion="waving",
                    preferred_side="right",
                    visual_type="web_news",
                    news_search_query=f"{topic}",
                )
            ]
        )
