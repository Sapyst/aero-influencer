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
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=api_key.strip())
            prompt = f"Topic/News: {topic}\nFormat: {video_type.upper()}\nAspect Ratio: {aspect_ratio}\nGenerate the complete screenplay JSON."
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
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
            title=f"The Shocking Truth About {topic}",
            video_type="shorts",
            aspect_ratio=aspect_ratio,
            outro_call_to_action="Want to know more curious things like this? Just follow!",
            beats=[
                SceneBeat(
                    beat_id=1,
                    narration=f"Wait... did you hear what just happened with {topic}?!",
                    emotion="shocked",
                    preferred_side="right",
                    visual_type="web_news",
                    news_search_query=f"{topic} breaking news",
                ),
                SceneBeat(
                    beat_id=2,
                    narration="It started when researchers discovered something completely unexpected in the latest report.",
                    emotion="pointing_left",
                    preferred_side="right",
                    visual_type="web_news",
                    news_search_query=f"{topic} report findings",
                ),
                SceneBeat(
                    beat_id=3,
                    narration="And here is the crazy part that almost nobody noticed until now.",
                    emotion="whispering",
                    preferred_side="left",
                    visual_type="web_news",
                    news_search_query=f"{topic} investigation",
                ),
                SceneBeat(
                    beat_id=4,
                    narration="The entire system was left wide open, affecting thousands of people worldwide!",
                    emotion="mindblown",
                    preferred_side="left",
                    visual_type="web_news",
                    news_search_query=f"{topic} impact numbers",
                ),
                SceneBeat(
                    beat_id=5,
                    narration="Honestly, how does this keep happening in modern tech?",
                    emotion="facepalm",
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
                    narration=f"Today we are diving deep into one of the most astonishing stories in recent tech: the case of {topic}.",
                    emotion="explaining",
                    preferred_side="right",
                    visual_type="web_news",
                    news_search_query=f"{topic} overview",
                ),
                SceneBeat(
                    beat_id=2,
                    narration="To understand how this disaster unfolded, we have to look back at how this infrastructure was originally set up.",
                    emotion="thinking",
                    preferred_side="right",
                    visual_type="web_news",
                    news_search_query=f"{topic} history background",
                ),
                SceneBeat(
                    beat_id=3,
                    narration="Industrial systems like these were designed decades ago, prioritizing convenience and remote monitoring over zero-trust security.",
                    emotion="pointing_left",
                    preferred_side="right",
                    visual_type="web_news",
                    news_search_query=f"{topic} architecture documentation",
                ),
                SceneBeat(
                    beat_id=4,
                    narration="Then, without warning, the anomaly struck simultaneously across multiple regions.",
                    emotion="shocked",
                    preferred_side="left",
                    visual_type="web_news",
                    news_search_query=f"{topic} incident timeline",
                ),
                SceneBeat(
                    beat_id=5,
                    narration="When technicians looked at the telemetry logs, what they saw was completely unbelievable.",
                    emotion="smug",
                    preferred_side="left",
                    visual_type="web_news",
                    news_search_query=f"{topic} technical flaw",
                ),
                SceneBeat(
                    beat_id=6,
                    narration="Default credentials, unpatched firmware, and exposed ports had created the perfect storm.",
                    emotion="facepalm",
                    preferred_side="right",
                    visual_type="web_news",
                    news_search_query=f"{topic} vulnerability advisory",
                ),
                SceneBeat(
                    beat_id=7,
                    narration="The total economic damage is already climbing into the tens of millions, sparking urgent emergency directives.",
                    emotion="mindblown",
                    preferred_side="left",
                    visual_type="web_news",
                    news_search_query=f"{topic} economic loss damage",
                ),
                SceneBeat(
                    beat_id=8,
                    narration="If you enjoyed this deep dive into modern technology and curious events, make sure to follow for the next one!",
                    emotion="waving",
                    preferred_side="right",
                    visual_type="web_news",
                    news_search_query=f"{topic}",
                )
            ]
        )
