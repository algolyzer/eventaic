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
                        raise Exception(f"Dify API error: {response.status}")

                    result = await response.json()
                    return self._parse_generation_response(result)

        except aiohttp.ClientError as e:
            logger.error(f"Dify connection error: {str(e)}")
            raise Exception(f"Failed to connect to Dify: {str(e)}")

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
                        raise Exception(f"Dify API error: {response.status}")

                    result = await response.json()
                    return self._parse_generation_response(result)

        except Exception as e:
            logger.error(f"Regeneration failed: {str(e)}")
            raise

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
                        raise Exception(f"Dify API error: {response.status}")

                    result = await response.json()
                    return self._parse_evaluation_response(result)

        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            raise

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

        return f"""
        Type: {ad_type.value}
        Company: {company_name}
        Location: {location_str}
        Product Categories: {categories_str}
        Event: {event_name}
        Product Name: {product_str}

        Generate a complete advertising campaign with the following JSON structure:
        {{
            "headline": "Catchy headline (max 60 characters)",
            "description": "Compelling description (max 150 characters)",
            "slogan": "Memorable slogan",
            "cta_text": "Call to action",
            "image_prompt": "Detailed image generation prompt",
            "image_base64": "Base64 encoded image if generated",
            "keywords": ["keyword1", "keyword2", ...],
            "hashtags": ["#hashtag1", "#hashtag2", ...],
            "platforms": ["google_ads", "meta_ads", ...],
            "platform_details": {{
                "google_ads": {{"priority": 1, "budget_percentage": 40}},
                "meta_ads": {{"priority": 2, "budget_percentage": 30}}
            }},
            "posting_times": ["9:00 AM", "2:00 PM", "6:00 PM"],
            "budget_allocation": {{"platform": percentage}}
        }}

        Ensure the content is event-specific, engaging, and optimized for conversions.
        """

    def _build_regeneration_prompt(
            self,
            ad_type: AdType,
            ad_data: Dict[str, Any],
            additional_instructions: Optional[str] = None
    ) -> str:
        """Build prompt for regeneration"""

        base_prompt = f"""
        Type: {ad_type.value}

        Original Ad Data:
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

            Generate ONLY a new image with the same theme but different visual approach.
            Return JSON with:
            {{
                "image_prompt": "New detailed image prompt",
                "image_base64": "Base64 encoded image if generated"
            }}
            """
        else:
            base_prompt += f"""

            Generate completely new ad content while maintaining the same event and product context.
            Return complete JSON structure as in original generation.
            """

        if additional_instructions:
            base_prompt += f"\n\nAdditional Instructions: {additional_instructions}"

        return base_prompt

    def _build_evaluation_prompt(self, ad_data: Dict[str, Any]) -> str:
        """Build prompt for evaluation"""

        return f"""
        Type: {AdType.EVALUATE.value}

        Evaluate the following advertisement:

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

        Provide evaluation in JSON format:
        {{
            "relevance_score": 0-10,
            "clarity_score": 0-10,
            "persuasiveness_score": 0-10,
            "brand_safety_score": 0-10,
            "overall_score": 0-10,
            "feedback": "Detailed feedback text",
            "recommendations": ["recommendation1", "recommendation2", ...]
        }}

        Consider event relevance, message clarity, persuasiveness, and brand safety.
        """

    def _parse_generation_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Dify generation response"""

        try:
            answer = response.get("answer", "{}")

            # Try to parse JSON from the answer
            try:
                parsed = json.loads(answer)
            except json.JSONDecodeError:
                # Extract JSON from text if needed
                import re
                json_match = re.search(r'\{.*\}', answer, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                else:
                    # Fallback to default structure
                    parsed = self._get_default_ad_content()

            return parsed

        except Exception as e:
            logger.error(f"Failed to parse Dify response: {str(e)}")
            return self._get_default_ad_content()

    def _parse_evaluation_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Dify evaluation response"""

        try:
            answer = response.get("answer", "{}")

            try:
                parsed = json.loads(answer)
            except json.JSONDecodeError:
                # Extract JSON from text if needed
                import re
                json_match = re.search(r'\{.*\}', answer, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                else:
                    parsed = self._get_default_evaluation()

            return parsed

        except Exception as e:
            logger.error(f"Failed to parse evaluation response: {str(e)}")
            return self._get_default_evaluation()

    def _get_default_ad_content(self) -> Dict[str, Any]:
        """Default ad content structure"""

        return {
            "headline": "Special Event Sale",
            "description": "Don't miss our exclusive offers",
            "slogan": "Quality You Can Trust",
            "cta_text": "Shop Now",
            "image_prompt": "Professional advertisement for special event",
            "keywords": ["sale", "discount", "special"],
            "hashtags": ["#sale", "#special"],
            "platforms": ["google_ads", "meta_ads"],
            "platform_details": {
                "google_ads": {"priority": 1, "budget_percentage": 50},
                "meta_ads": {"priority": 2, "budget_percentage": 50}
            },
            "posting_times": ["9:00 AM", "2:00 PM", "6:00 PM"],
            "budget_allocation": {"google_ads": 50, "meta_ads": 50}
        }

    def _get_default_evaluation(self) -> Dict[str, Any]:
        """Default evaluation structure"""

        return {
            "relevance_score": 5.0,
            "clarity_score": 5.0,
            "persuasiveness_score": 5.0,
            "brand_safety_score": 5.0,
            "overall_score": 5.0,
            "feedback": "Unable to evaluate at this time",
            "recommendations": []
        }
