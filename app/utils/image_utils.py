import aiohttp
import aiofiles
import hashlib
import logging
from pathlib import Path
from typing import Optional
from uuid import UUID
import os

logger = logging.getLogger(__name__)

# Static images directory
STATIC_DIR = Path("static")
IMAGES_DIR = STATIC_DIR / "images" / "ads"


def ensure_images_directory() -> None:
    """Ensure the images directory exists"""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Images directory ensured at: {IMAGES_DIR}")


def get_image_path(ad_id: UUID, filename: str) -> Path:
    """
    Get the full path for an ad image

    Args:
        ad_id: The ad UUID
        filename: The image filename

    Returns:
        Path object for the image
    """
    ad_dir = IMAGES_DIR / str(ad_id)
    ad_dir.mkdir(parents=True, exist_ok=True)
    return ad_dir / filename


def get_image_url(ad_id: UUID, filename: str) -> str:
    """
    Get the public URL for an ad image

    Args:
        ad_id: The ad UUID
        filename: The image filename

    Returns:
        URL string for accessing the image
    """
    return f"/static/images/ads/{ad_id}/{filename}"


async def download_image_from_url(
    url: str, ad_id: UUID, original_filename: Optional[str] = None
) -> Optional[tuple[str, str]]:
    """
    Download image from URL and save to static directory

    Args:
        url: Image URL to download from
        ad_id: The ad UUID
        original_filename: Original filename (optional)

    Returns:
        Tuple of (saved_filename, public_url) if successful, None otherwise
    """

    ensure_images_directory()

    try:
        logger.info(f"Downloading image from: {url[:100]}...")

        # Download the image
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    logger.error(f"Failed to download image: HTTP {response.status}")
                    return None

                image_data = await response.read()

                if not image_data:
                    logger.error("Downloaded image data is empty")
                    return None

                # Generate filename from content hash if no original filename
                if not original_filename:
                    content_hash = hashlib.md5(image_data).hexdigest()
                    original_filename = f"{content_hash}.png"

                # Ensure extension
                if not original_filename.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".webp", ".gif")
                ):
                    original_filename += ".png"

                # Get save path
                save_path = get_image_path(ad_id, original_filename)

                # Save the image
                async with aiofiles.open(save_path, "wb") as f:
                    await f.write(image_data)

                # Get public URL
                public_url = get_image_url(ad_id, original_filename)

                logger.info(f"Image saved successfully: {save_path}")
                logger.info(f"Public URL: {public_url}")

                return (original_filename, public_url)

    except aiohttp.ClientError as e:
        logger.error(f"Network error downloading image: {str(e)}")
        return None
    except IOError as e:
        logger.error(f"File I/O error saving image: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading image: {str(e)}")
        return None


async def delete_ad_images(ad_id: UUID) -> bool:
    """
    Delete all images for a specific ad

    Args:
        ad_id: The ad UUID

    Returns:
        True if successful, False otherwise
    """

    try:
        ad_dir = IMAGES_DIR / str(ad_id)

        if ad_dir.exists():
            import shutil

            shutil.rmtree(ad_dir)
            logger.info(f"Deleted images directory for ad: {ad_id}")
            return True
        else:
            logger.warning(f"Images directory not found for ad: {ad_id}")
            return False

    except Exception as e:
        logger.error(f"Error deleting ad images: {str(e)}")
        return False


def get_image_size(ad_id: UUID, filename: str) -> Optional[int]:
    """
    Get the size of an image file in bytes

    Args:
        ad_id: The ad UUID
        filename: The image filename

    Returns:
        File size in bytes, or None if file doesn't exist
    """

    try:
        image_path = get_image_path(ad_id, filename)

        if image_path.exists():
            return image_path.stat().st_size
        else:
            return None

    except Exception as e:
        logger.error(f"Error getting image size: {str(e)}")
        return None


def list_ad_images(ad_id: UUID) -> list[str]:
    """
    List all images for a specific ad

    Args:
        ad_id: The ad UUID

    Returns:
        List of filenames
    """

    try:
        ad_dir = IMAGES_DIR / str(ad_id)

        if ad_dir.exists():
            return [f.name for f in ad_dir.iterdir() if f.is_file()]
        else:
            return []

    except Exception as e:
        logger.error(f"Error listing ad images: {str(e)}")
        return []
