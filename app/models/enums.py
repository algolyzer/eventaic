from enum import Enum


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    COMPANY = "company"


class AdStatus(str, Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    REGENERATED = "regenerated"
    EVALUATED = "evaluated"
    PUBLISHED = "published"


class AdType(str, Enum):
    PRODUCT_GEN = "product_gen"
    REGEN = "regen"
    REGEN_IMAGE = "regen_image"
    EVALUATE = "evaluate"


class Platform(str, Enum):
    GOOGLE_ADS = "google_ads"
    META_ADS = "meta_ads"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
