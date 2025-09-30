import base64
import logging
from typing import Optional

import aiohttp

from app.core.config import settings


logger = logging.getLogger(__name__)


class ImageGenerationService:
    """Service for generating images from prompts"""

    def __init__(self):
        # You can configure which image service to use
        self.service = "replicate"  # or "openai", "stability", etc.
        self.api_key = (
            settings.IMAGE_API_KEY if hasattr(settings, "IMAGE_API_KEY") else None
        )

    async def generate_image(self, prompt: str) -> Optional[str]:
        """
        Generate image from prompt and return base64 string

        Args:
            prompt: Text prompt for image generation

        Returns:
            Base64 encoded image string or None if generation fails
        """
        try:
            if self.service == "replicate":
                return await self._generate_with_replicate(prompt)
            elif self.service == "openai":
                return await self._generate_with_openai(prompt)
            elif self.service == "stability":
                return await self._generate_with_stability(prompt)
            else:
                # Fallback: generate a placeholder SVG
                return self._generate_placeholder(prompt)
        except Exception as e:
            logger.error(f"Image generation failed: {str(e)}")
            return self._generate_placeholder(prompt)

    async def _generate_with_replicate(self, prompt: str) -> Optional[str]:
        """Generate image using Replicate API"""
        if not self.api_key:
            logger.warning("No Replicate API key configured")
            return self._generate_placeholder(prompt)

        url = "https://api.replicate.com/v1/predictions"
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "version": "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            "input": {
                "prompt": prompt,
                "width": 1024,
                "height": 1024,
                "num_outputs": 1,
            },
        }

        async with aiohttp.ClientSession() as session:
            # Start prediction
            async with session.post(
                url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status != 201:
                    logger.error(f"Replicate API error: {response.status}")
                    return self._generate_placeholder(prompt)

                result = await response.json()
                prediction_url = result.get("urls", {}).get("get")

            # Poll for completion
            max_attempts = 30
            for _ in range(max_attempts):
                await asyncio.sleep(2)
                async with session.get(prediction_url, headers=headers) as response:
                    if response.status != 200:
                        continue

                    result = await response.json()
                    if result.get("status") == "succeeded":
                        image_url = result.get("output", [None])[0]
                        if image_url:
                            return await self._download_and_encode(image_url)
                    elif result.get("status") == "failed":
                        logger.error("Image generation failed")
                        break

        return self._generate_placeholder(prompt)

    async def _generate_with_openai(self, prompt: str) -> Optional[str]:
        """Generate image using DALL-E API"""
        if not self.api_key:
            return self._generate_placeholder(prompt)

        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "b64_json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status != 200:
                        logger.error(f"OpenAI API error: {response.status}")
                        return self._generate_placeholder(prompt)

                    result = await response.json()
                    return result["data"][0]["b64_json"]
        except Exception as e:
            logger.error(f"OpenAI image generation error: {str(e)}")
            return self._generate_placeholder(prompt)

    async def _generate_with_stability(self, prompt: str) -> Optional[str]:
        """Generate image using Stability AI"""
        if not self.api_key:
            return self._generate_placeholder(prompt)

        url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as response:
                    if response.status != 200:
                        logger.error(f"Stability AI error: {response.status}")
                        return self._generate_placeholder(prompt)

                    result = await response.json()
                    return result["artifacts"][0]["base64"]
        except Exception as e:
            logger.error(f"Stability AI error: {str(e)}")
            return self._generate_placeholder(prompt)

    async def _download_and_encode(self, url: str) -> Optional[str]:
        """Download image from URL and encode to base64"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        image_bytes = await response.read()
                        return base64.b64encode(image_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"Image download error: {str(e)}")
        return None

    def _generate_placeholder(self, prompt: str) -> str:
        """Generate a placeholder SVG image"""
        # Extract key words from prompt for the placeholder
        words = prompt.split()[:3]
        text = " ".join(words) if words else "Ad Image"

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="1024" viewBox="0 0 1024 1024">
            <defs>
                <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stop-color="#7c5cff"/>
                    <stop offset="100%" stop-color="#00d4ff"/>
                </linearGradient>
            </defs>
            <rect width="1024" height="1024" fill="url(#g)"/>
            <text x="512" y="512" font-family="Arial" font-size="48" font-weight="bold" fill="white" text-anchor="middle" dominant-baseline="middle">{text}</text>
        </svg>"""

        return base64.b64encode(svg.encode()).decode("utf-8")
