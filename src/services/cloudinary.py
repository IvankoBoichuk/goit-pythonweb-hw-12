import cloudinary
import cloudinary.uploader
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import io
import logging

from src.conf.config import settings

logger = logging.getLogger(__name__)

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.cloudinary_name,
    api_key=settings.cloudinary_api_key,
    api_secret=settings.cloudinary_api_secret
)

class CloudinaryService:
    @staticmethod
    def validate_image_file(file: UploadFile) -> None:
        """Validate uploaded image file."""
        # Check file size
        if file.size and file.size > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size too large. Maximum size is {settings.max_file_size / 1024 / 1024:.1f}MB"
            )
        
        # Check file type
        if file.content_type not in settings.allowed_image_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(settings.allowed_image_types)}"
            )

    @staticmethod
    def optimize_image(file_content: bytes, max_size: tuple = (300, 300)) -> bytes:
        """Optimize image size and quality for avatar."""
        try:
            # Open image
            image = Image.open(io.BytesIO(file_content))
            
            # Convert to RGB if necessary (for PNG with transparency)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Resize image while maintaining aspect ratio
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save optimized image
            output_buffer = io.BytesIO()
            image.save(output_buffer, format='JPEG', quality=85, optimize=True)
            output_buffer.seek(0)
            
            return output_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error optimizing image: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image file"
            )

    @staticmethod
    async def upload_avatar(file: UploadFile, user_id: int) -> str:
        """Upload user avatar to Cloudinary."""
        try:
            # Validate file
            CloudinaryService.validate_image_file(file)
            
            # Read file content
            file_content = await file.read()
            
            # Optimize image
            optimized_content = CloudinaryService.optimize_image(file_content)
            
            # Create public_id for the avatar
            public_id = f"avatars/user_{user_id}"
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                optimized_content,
                public_id=public_id,
                folder="contacts_app/avatars",
                transformation=[
                    {"width": 300, "height": 300, "crop": "fill", "gravity": "face"},
                    {"quality": "auto", "fetch_format": "auto"}
                ],
                overwrite=True,  # Overwrite existing avatar
                resource_type="image"
            )
            
            return result.get("secure_url")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading to Cloudinary: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload avatar"
            )

    @staticmethod
    def delete_avatar(avatar_url: str) -> bool:
        """Delete avatar from Cloudinary."""
        try:
            # Extract public_id from URL
            if "contacts_app/avatars/" in avatar_url:
                # Extract public_id from Cloudinary URL
                public_id = avatar_url.split("/")[-1].split(".")[0]
                public_id = f"contacts_app/avatars/{public_id}"
                
                # Delete from Cloudinary
                result = cloudinary.uploader.destroy(public_id)
                return result.get("result") == "ok"
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting avatar from Cloudinary: {e}")
            return False

    @staticmethod
    def get_default_avatar_url(user_id: int) -> str:
        """Generate default avatar URL using Cloudinary."""
        # Generate avatar using user_id as seed for consistent avatars
        return f"https://res.cloudinary.com/{settings.cloudinary_name}/image/upload/c_fill,g_face,h_300,w_300/v1/samples/avatar_placeholder.jpg"