import aiohttp
import json
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.models.enums import AdType
import logging
import re

logger = logging.getLogger(__name__)


class DifyService:
    """Service for interacting with Dify API"""

    def __init__(self):
        self.base_url = settings.DIFY_BASE_URL
        self.api_key = settings.DIFY_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.timeout = aiohttp.ClientTimeout(total=settings.DIFY_TIMEOUT)

    async def generate_ad(
            self,
            event_name: str,
            product_categories: List[str],
            company_name: str,
            location: Optional[str] = None,
            product_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate ad content using Dify"""

        prompt = self._build_generation_prompt(
            AdType.PRODUCT_GEN,
            event_name=event_name,
            product_categories=product_categories,
            company_name=company_name,
            location=location,
            product_name=product_name
        )

        payload = {
            "inputs": {},
            "query": prompt,
            "response_mode": "blocking",
            "user": f"company_{company_name}"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.base_url}/chat-messages",
                        headers=self.headers,
                        json=payload,
                        timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Dify API error: {response.status} - {error_text}")
                        raise Exception(f"Dify API returned status {response.status}")

                    result = await response.json()
                    logger.info(f"Dify response received: {result.get('answer', '')[:100]}...")

                    return self._parse_generation_response(result)

        except aiohttp.ClientError as e:
            logger.error(f"Dify connection error: {str(e)}")
            raise Exception(f"Failed to connect to AI service: {str(e)}")
        except Exception as e:
            logger.error(f"Dify request failed: {str(e)}")
            raise Exception(f"AI service error: {str(e)}")

    async def generate_image(self, image_prompt: str, ad_context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Generate image using Dify based on image prompt

        Args:
            image_prompt: The prompt for image generation
            ad_context: Optional context about the ad (event, product, etc.)

        Returns:
            Image URL from Dify response, or None if generation fails
        """

        # Build enhanced prompt with context
        enhanced_prompt = self._build_image_prompt(image_prompt, ad_context)

        prompt = f"""Generate a high-quality advertising image based on this description:

{enhanced_prompt}

Requirements:
- Professional advertising quality
- High resolution (1024x1024 or higher)
- Eye-catching and relevant to the description
- Brand-safe content
- Modern design aesthetic

Return the image URL or upload the image."""

        payload = {
            "inputs": {},
            "query": prompt,
            "response_mode": "blocking",
            "user": "image_generation"
        }

        try:
            logger.info(f"🎨 Sending image generation request to Dify...")
            logger.info(f"📝 Prompt: {enhanced_prompt[:100]}...")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.base_url}/chat-messages",
                        headers=self.headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"❌ Dify image API error: {response.status} - {error_text}")
                        raise Exception(f"Dify image API returned status {response.status}")

                    result = await response.json()

                    # Log the COMPLETE response for debugging
                    logger.info("=" * 80)
                    logger.info("📦 COMPLETE DIFY IMAGE RESPONSE:")
                    logger.info(json.dumps(result, indent=2))
                    logger.info("=" * 80)

                    # Parse and return image URL
                    image_url = self._parse_image_response(result, image_prompt)

                    if image_url:
                        logger.info(f"✅ Successfully extracted image URL: {image_url[:100]}...")
                    else:
                        logger.warning("⚠️ No image URL found in Dify response")

                    return image_url

        except aiohttp.ClientError as e:
            logger.error(f"🔌 Dify image connection error: {str(e)}")
            raise Exception(f"Failed to connect to image service: {str(e)}")
        except Exception as e:
            logger.error(f"💥 Dify image request failed: {str(e)}")
            raise Exception(f"Image generation error: {str(e)}")

    async def regenerate_ad(
            self,
            ad_data: Dict[str, Any],
            regenerate_image: bool = False,
            additional_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Regenerate ad or just image"""

        ad_type = AdType.REGEN_IMAGE if regenerate_image else AdType.REGEN

        prompt = self._build_regeneration_prompt(
            ad_type=ad_type,
            ad_data=ad_data,
            additional_instructions=additional_instructions
        )

        payload = {
            "inputs": {},
            "query": prompt,
            "response_mode": "blocking",
            "user": f"regen_{ad_data.get('company_name', 'unknown')}"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.base_url}/chat-messages",
                        headers=self.headers,
                        json=payload,
                        timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Dify API returned status {response.status}")

                    result = await response.json()
                    logger.info(f"Dify regeneration response received")

                    return self._parse_generation_response(result)

        except Exception as e:
            logger.error(f"Regeneration failed: {str(e)}")
            raise Exception(f"AI regeneration failed: {str(e)}")

    async def evaluate_ad(self, ad_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate ad quality"""

        prompt = self._build_evaluation_prompt(ad_data)

        payload = {
            "inputs": {},
            "query": prompt,
            "response_mode": "blocking",
            "user": f"eval_{ad_data.get('id', 'unknown')}"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.base_url}/chat-messages",
                        headers=self.headers,
                        json=payload,
                        timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        raise Exception(f"Dify API returned status {response.status}")

                    result = await response.json()
                    logger.info(f"Dify evaluation response received")

                    return self._parse_evaluation_response(result)

        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            raise Exception(f"AI evaluation failed: {str(e)}")

    def _build_generation_prompt(
            self,
            ad_type: AdType,
            event_name: str,
            product_categories: List[str],
            company_name: str,
            location: Optional[str] = None,
            product_name: Optional[str] = None
    ) -> str:
        """Build prompt for ad generation"""

        categories_str = ", ".join(product_categories)
        location_str = location or "Global"
        product_str = product_name or "General Products"

        return f"""Generate an advertising campaign for the following:

Event: {event_name}
Company: {company_name}
Location: {location_str}
Product Categories: {categories_str}
Product Name: {product_str}

Please respond with ONLY a valid JSON object (no additional text before or after) in this exact format:
{{
    "headline": "Catchy headline (max 60 characters)",
    "description": "Compelling description (max 150 characters)",
    "slogan": "Memorable slogan",
    "cta_text": "Call to action",
    "image_prompt": "Detailed image generation prompt describing the visual for this ad",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", "#hashtag5"],
    "platforms": ["google_ads", "meta_ads", "linkedin", "instagram", "tiktok"],
    "platform_details": {{
        "google_ads": {{"priority": 1, "budget_percentage": 40}},
        "meta_ads": {{"priority": 2, "budget_percentage": 30}},
        "linkedin": {{"priority": 3, "budget_percentage": 15}},
        "instagram": {{"priority": 4, "budget_percentage": 10}},
        "tiktok": {{"priority": 5, "budget_percentage": 5}}
    }},
    "posting_times": ["9:00 AM", "2:00 PM", "6:00 PM"],
    "budget_allocation": {{"google_ads": 40, "meta_ads": 30, "linkedin": 15, "instagram": 10, "tiktok": 5}}
}}

Make the content specific to the event, engaging, and optimized for conversions. Use only valid JSON format."""

    def _build_image_prompt(self, base_prompt: str, ad_context: Optional[Dict[str, Any]] = None) -> str:
        """Build enhanced image prompt with context"""

        if not ad_context:
            return base_prompt

        context_parts = []
        if ad_context.get('event_name'):
            context_parts.append(f"Event: {ad_context['event_name']}")
        if ad_context.get('product_categories'):
            context_parts.append(f"Products: {', '.join(ad_context['product_categories'])}")
        if ad_context.get('headline'):
            context_parts.append(f"Theme: {ad_context['headline']}")

        if context_parts:
            context_str = " | ".join(context_parts)
            return f"{base_prompt}\n\nContext: {context_str}\n\nStyle: Professional advertising, high-quality, modern, engaging"

        return base_prompt

    def _build_regeneration_prompt(
            self,
            ad_type: AdType,
            ad_data: Dict[str, Any],
            additional_instructions: Optional[str] = None
    ) -> str:
        """Build prompt for regeneration"""

        base_prompt = f"""Regenerate an improved version of this advertisement:

Event: {ad_data.get('event_name')}
Company: {ad_data.get('company_name')}
Product Categories: {', '.join(ad_data.get('product_categories', []))}

Original Content:
Headline: {ad_data.get('headline')}
Description: {ad_data.get('description')}
Slogan: {ad_data.get('slogan')}
"""

        if ad_type == AdType.REGEN_IMAGE:
            base_prompt += f"""

Generate ONLY a new image prompt. Respond with valid JSON:
{{
    "image_prompt": "New detailed image generation prompt"
}}
"""
        else:
            base_prompt += f"""

Generate completely new ad content while maintaining the same event theme. Respond with ONLY a valid JSON object in this exact format:
{{
    "headline": "New catchy headline",
    "description": "New compelling description",
    "slogan": "New memorable slogan",
    "cta_text": "Call to action",
    "image_prompt": "Detailed image prompt",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
    "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", "#hashtag5"],
    "platforms": ["google_ads", "meta_ads", "linkedin"],
    "platform_details": {{
        "google_ads": {{"priority": 1, "budget_percentage": 50}},
        "meta_ads": {{"priority": 2, "budget_percentage": 35}},
        "linkedin": {{"priority": 3, "budget_percentage": 15}}
    }},
    "posting_times": ["9:00 AM", "2:00 PM", "6:00 PM"],
    "budget_allocation": {{"google_ads": 50, "meta_ads": 35, "linkedin": 15}}
}}
"""

        if additional_instructions:
            base_prompt += f"\n\nAdditional Instructions: {additional_instructions}"

        return base_prompt

    def _build_evaluation_prompt(self, ad_data: Dict[str, Any]) -> str:
        """Build prompt for evaluation"""

        return f"""Evaluate this advertisement:

Event: {ad_data.get('event_name')}
Company: {ad_data.get('company_name')}
Product Categories: {', '.join(ad_data.get('product_categories', []))}

Ad Content:
Headline: {ad_data.get('headline')}
Description: {ad_data.get('description')}
Slogan: {ad_data.get('slogan')}
CTA: {ad_data.get('cta_text')}
Keywords: {', '.join(ad_data.get('keywords', []))}
Hashtags: {', '.join(ad_data.get('hashtags', []))}

Respond with ONLY a valid JSON object (no additional text) in this exact format:
{{
    "relevance_score": 8.5,
    "clarity_score": 9.0,
    "persuasiveness_score": 8.0,
    "brand_safety_score": 9.5,
    "overall_score": 8.75,
    "feedback": "Detailed feedback text explaining the scores",
    "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"]
}}

Scores should be between 0-10. Consider event relevance, message clarity, persuasiveness, and brand safety."""

    def _parse_generation_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Dify generation response - STRICT JSON parsing"""

        try:
            answer = response.get("answer", "{}").strip()

            if not answer:
                raise ValueError("Empty response from Dify")

            logger.debug(f"Raw Dify response: {answer[:500]}")

            # Try to find JSON in the response
            json_start = answer.find('{')
            json_end = answer.rfind('}')

            if json_start == -1 or json_end == -1:
                raise ValueError("No JSON object found in response")

            json_str = answer[json_start:json_end + 1]

            try:
                parsed = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                logger.error(f"Failed JSON string: {json_str[:500]}")
                raise ValueError(f"Invalid JSON in response: {str(e)}")

            # Validate required fields
            required_fields = ['headline', 'description', 'slogan', 'cta_text', 'keywords', 'hashtags', 'platforms']
            missing_fields = [field for field in required_fields if field not in parsed]

            if missing_fields:
                logger.warning(f"Missing required fields: {missing_fields}")
                defaults = {
                    'headline': 'Special Offer',
                    'description': 'Limited time offer',
                    'slogan': 'Act Now',
                    'cta_text': 'Learn More',
                    'keywords': ['sale', 'offer', 'limited'],
                    'hashtags': ['#sale', '#offer'],
                    'platforms': ['google_ads', 'meta_ads'],
                    'image_prompt': 'Professional marketing image',
                    'platform_details': {
                        'google_ads': {'priority': 1, 'budget_percentage': 50},
                        'meta_ads': {'priority': 2, 'budget_percentage': 50}
                    },
                    'posting_times': ['9:00 AM', '2:00 PM', '6:00 PM'],
                    'budget_allocation': {'google_ads': 50, 'meta_ads': 50}
                }
                for field in missing_fields:
                    parsed[field] = defaults.get(field, '')

            logger.info("Successfully parsed Dify generation response")
            return parsed

        except Exception as e:
            logger.error(f"Failed to parse Dify response: {str(e)}")
            raise ValueError(f"Unable to parse AI response: {str(e)}")

    def _parse_image_response(self, response: Dict[str, Any], original_prompt: str) -> Optional[str]:
        """
        Parse Dify image response - ULTRA ROBUST VERSION with 5 strategies
        """

        try:
            logger.info("🔍 Starting image URL extraction...")

            # STRATEGY 1: Files Array
            files = response.get("files", [])
            if files:
                logger.info(f"📁 Found {len(files)} files in response")
                for idx, file in enumerate(files):
                    logger.info(f"  File {idx + 1}: type={file.get('type')}, url={file.get('url', 'N/A')[:100]}")
                    url_candidates = [
                        file.get('url'), file.get('remote_url'), file.get('download_url'),
                        file.get('file_url'), file.get('path'), file.get('src'), file.get('href')
                    ]
                    for url in url_candidates:
                        if url and isinstance(url, str) and url.startswith('http'):
                            logger.info(f"✅ Found URL in files: {url[:100]}")
                            return url

            # STRATEGY 2: Answer Field
            answer = response.get("answer", "")
            if answer:
                logger.info(f"📄 Checking answer ({len(answer)} chars): {answer[:300]}")

                # Markdown images
                markdown_patterns = [
                    r'!\[.*?\]\((https?://[^\)]+)\)',
                    r'!\[.*?\]\((https?://[^\s\)]+)',
                    r'\[!\[.*?\]\((https?://[^\)]+)\)\]',
                ]
                for pattern in markdown_patterns:
                    matches = re.findall(pattern, answer)
                    if matches:
                        logger.info(f"✅ Found markdown URL: {matches[0][:100]}")
                        return matches[0].strip()

                # HTML img tags
                html_matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', answer)
                if html_matches:
                    logger.info(f"✅ Found HTML URL: {html_matches[0][:100]}")
                    return html_matches[0]

                # Plain URLs
                urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]\'()]+', answer)
                logger.info(f"   Found {len(urls)} URLs")
                for url in urls:
                    url = url.strip()
                    url_lower = url.lower()
                    indicators = [
                        '.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp',
                        'cloud.dify.ai', 'storage', 'cdn', 'amazonaws', 'cloudinary',
                        'imgix', 'cloudfront', 'imgur', 'image', 'media', 'assets',
                        'dify', 'file', 'download'
                    ]
                    if any(ind in url_lower for ind in indicators):
                        logger.info(f"✅ Found image URL: {url[:100]}")
                        return url

                # Base64 data
                base64_match = re.search(r'data:image/[^;]+;base64,[A-Za-z0-9+/=]+', answer)
                if base64_match:
                    logger.info(f"✅ Found base64 data ({len(base64_match.group(0))} chars)")
                    return base64_match.group(0)

            # STRATEGY 3: Metadata
            metadata = response.get("metadata", {})
            if isinstance(metadata, dict):
                logger.info("🔍 Checking metadata...")
                for field in ['image_url', 'url', 'image', 'file_url', 'download_url']:
                    url = metadata.get(field)
                    if url and isinstance(url, str) and url.startswith('http'):
                        logger.info(f"✅ Found URL in metadata.{field}: {url[:100]}")
                        return url

            # STRATEGY 4: Direct Fields
            logger.info("🔍 Checking direct fields...")
            for field in ['image_url', 'image', 'url', 'file_url', 'media_url', 'download_url']:
                url = response.get(field)
                if url and isinstance(url, str) and url.startswith('http'):
                    logger.info(f"✅ Found URL in {field}: {url[:100]}")
                    return url

            # STRATEGY 5: Constructed URLs
            conversation_id = response.get("conversation_id")
            if conversation_id and files:
                logger.info("🔍 Constructing URLs...")
                for file in files:
                    file_id = file.get('id') or file.get('file_id')
                    if file_id:
                        base_url = self.base_url.replace("/v1", "").rstrip("/")
                        urls = [
                            f"{base_url}/files/conversations/{conversation_id}/files/{file_id}",
                            f"{base_url}/files/{conversation_id}/{file_id}",
                            f"{base_url}/v1/files/{file_id}",
                        ]
                        for url in urls:
                            logger.info(f"   Trying: {url}")
                            return url

            # No URL found
            logger.error("❌ No image URL found using any strategy")
            logger.error(f"Keys: {list(response.keys())}, Files: {len(files)}, Answer: {len(answer)} chars")
            return None

        except Exception as e:
            logger.error(f"💥 Error: {str(e)}")
            logger.error(f"Response: {json.dumps(response, indent=2)[:1000]}")
            return None

    def _parse_evaluation_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Dify evaluation response"""

        try:
            answer = response.get("answer", "{}").strip()
            if not answer:
                raise ValueError("Empty evaluation response")

            json_start = answer.find('{')
            json_end = answer.rfind('}')
            if json_start == -1 or json_end == -1:
                raise ValueError("No JSON in evaluation response")

            parsed = json.loads(answer[json_start:json_end + 1])

            # Validate scores
            for field in ['relevance_score', 'clarity_score', 'persuasiveness_score',
                          'brand_safety_score', 'overall_score']:
                if field not in parsed:
                    parsed[field] = 5.0
                else:
                    parsed[field] = max(0.0, min(10.0, float(parsed[field])))

            if 'feedback' not in parsed:
                parsed['feedback'] = 'Evaluation completed'
            if 'recommendations' not in parsed:
                parsed['recommendations'] = []

            return parsed

        except Exception as e:
            logger.error(f"Failed to parse evaluation: {str(e)}")
            raise ValueError(f"Unable to parse evaluation: {str(e)}")
