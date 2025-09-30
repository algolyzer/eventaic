import aiohttp
import json
import base64
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.models.enums import AdType
import logging

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

Return ONLY the base64 encoded image data with no additional text or formatting.
The response should be pure base64 string starting with the image data."""

        payload = {
            "inputs": {},
            "query": prompt,
            "response_mode": "blocking",
            "user": "image_generation"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                        f"{self.base_url}/chat-messages",
                        headers=self.headers,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60)  # Longer timeout for image generation
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Dify image API error: {response.status} - {error_text}")
                        raise Exception(f"Dify image API returned status {response.status}")

                    result = await response.json()
                    logger.info("Dify image response received")

                    return self._parse_image_response(result, image_prompt)

        except aiohttp.ClientError as e:
            logger.error(f"Dify image connection error: {str(e)}")
            raise Exception(f"Failed to connect to image service: {str(e)}")
        except Exception as e:
            logger.error(f"Dify image request failed: {str(e)}")
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

            # Log the raw response for debugging
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
                # Fill missing fields with defaults
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
        Parse Dify image response and return image URL

        Dify returns images in the 'files' array with URLs.
        This method extracts the URL for download.

        Returns:
            Image URL if found, None otherwise
        """

        try:
            # Check for files array in response
            files = response.get("files", [])

            if files and len(files) > 0:
                # Get the first file (should be the generated image)
                first_file = files[0]

                if first_file.get("type") == "image":
                    image_url = first_file.get("url")

                    if image_url:
                        logger.info(f"Image URL received from Dify: {image_url[:100]}...")
                        return image_url
                    else:
                        logger.warning("File found but no URL present")
                else:
                    logger.warning(f"File type is not image: {first_file.get('type')}")
            else:
                logger.warning("No files array in Dify response")

            # No valid image URL found
            return None

        except Exception as e:
            logger.error(f"Failed to parse image response: {str(e)}")
            return None

    def _generate_svg_placeholder(self, prompt: str) -> str:
        """Generate a high-quality SVG placeholder image"""

        # Extract key words from prompt for the placeholder
        words = prompt.split()[:5]
        title = ' '.join(words) if words else 'Ad Image'

        # Create modern gradient colors based on prompt hash
        prompt_hash = sum(ord(c) for c in prompt)
        hue1 = (prompt_hash % 360)
        hue2 = (hue1 + 60) % 360

        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
            <defs>
                <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:hsl({hue1}, 75%, 55%);stop-opacity:1" />
                    <stop offset="100%" style="stop-color:hsl({hue2}, 75%, 65%);stop-opacity:1" />
                </linearGradient>
                <filter id="shadow">
                    <feDropShadow dx="0" dy="4" stdDeviation="6" flood-opacity="0.3"/>
                </filter>
            </defs>

            <!-- Background -->
            <rect width="1200" height="630" fill="url(#bg)"/>

            <!-- Decorative circles -->
            <circle cx="150" cy="150" r="80" fill="white" opacity="0.1"/>
            <circle cx="1050" cy="480" r="100" fill="white" opacity="0.1"/>
            <circle cx="950" cy="150" r="60" fill="white" opacity="0.15"/>

            <!-- Content -->
            <g filter="url(#shadow)">
                <text x="600" y="280" font-family="Arial, sans-serif" font-size="42" font-weight="bold" 
                      fill="white" text-anchor="middle" opacity="0.95">
                    {title}
                </text>
                <text x="600" y="350" font-family="Arial, sans-serif" font-size="24" 
                      fill="white" text-anchor="middle" opacity="0.85">
                    Event-Driven Advertising
                </text>
            </g>

            <!-- Brand element -->
            <rect x="550" y="400" width="100" height="6" rx="3" fill="white" opacity="0.6"/>
        </svg>'''

        # Encode to base64
        return base64.b64encode(svg.encode('utf-8')).decode('utf-8')

    def _parse_evaluation_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Dify evaluation response - STRICT JSON parsing"""

        try:
            answer = response.get("answer", "{}").strip()

            if not answer:
                raise ValueError("Empty evaluation response from Dify")

            logger.debug(f"Raw evaluation response: {answer[:500]}")

            # Find JSON in response
            json_start = answer.find('{')
            json_end = answer.rfind('}')

            if json_start == -1 or json_end == -1:
                raise ValueError("No JSON object found in evaluation response")

            json_str = answer[json_start:json_end + 1]

            try:
                parsed = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Evaluation JSON decode error: {str(e)}")
                raise ValueError(f"Invalid JSON in evaluation: {str(e)}")

            # Validate and fix scores
            score_fields = ['relevance_score', 'clarity_score', 'persuasiveness_score', 'brand_safety_score',
                            'overall_score']
            for field in score_fields:
                if field not in parsed:
                    parsed[field] = 5.0
                else:
                    # Ensure scores are float and within 0-10 range
                    try:
                        score = float(parsed[field])
                        parsed[field] = max(0.0, min(10.0, score))
                    except (ValueError, TypeError):
                        parsed[field] = 5.0

            # Ensure feedback and recommendations exist
            if 'feedback' not in parsed or not parsed['feedback']:
                parsed['feedback'] = 'Evaluation completed successfully'

            if 'recommendations' not in parsed:
                parsed['recommendations'] = []
            elif not isinstance(parsed['recommendations'], list):
                parsed['recommendations'] = []

            logger.info("Successfully parsed Dify evaluation response")
            return parsed

        except Exception as e:
            logger.error(f"Failed to parse evaluation response: {str(e)}")
            raise ValueError(f"Unable to parse evaluation: {str(e)}")
