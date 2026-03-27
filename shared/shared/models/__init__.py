"""All domain models — imported here for Alembic autogenerate to detect all tables."""

from shared.models.base import Base, BaseModel
from shared.models.billing.allocation import Allocation
from shared.models.billing.charge import Charge

# Billing
from shared.models.billing.check import Check
from shared.models.billing.payment import Payment
from shared.models.catalog.allergen import Allergen
from shared.models.catalog.allergen_cross_reaction import AllergenCrossReaction
from shared.models.catalog.branch_product import BranchProduct

# Catalog
from shared.models.catalog.category import Category
from shared.models.catalog.dietary_profile import DietaryProfile
from shared.models.catalog.product import Product
from shared.models.catalog.product_allergen import ProductAllergen
from shared.models.catalog.product_badge import ProductBadge
from shared.models.catalog.product_cooking_method import ProductCookingMethod
from shared.models.catalog.product_dietary_profile import ProductDietaryProfile
from shared.models.catalog.product_ingredient import ProductIngredient
from shared.models.catalog.product_seal import ProductSeal
from shared.models.catalog.subcategory import Subcategory
from shared.models.core.branch import Branch

# Core
from shared.models.core.refresh_token import RefreshToken
from shared.models.core.tenant import Tenant
from shared.models.core.user import User
from shared.models.core.user_branch_role import UserBranchRole
from shared.models.ingredients.ingredient import Ingredient

# Ingredients
from shared.models.ingredients.ingredient_group import IngredientGroup
from shared.models.ingredients.sub_ingredient import SubIngredient
from shared.models.marketing.badge import Badge

# Marketing
from shared.models.marketing.promotion import Promotion
from shared.models.marketing.promotion_product import PromotionProduct
from shared.models.marketing.seal import Seal
from shared.models.orders.kitchen_ticket import KitchenTicket

# Orders
from shared.models.orders.round import Round
from shared.models.orders.round_item import RoundItem

# Profiles
from shared.models.profiles.cooking_method import CookingMethod
from shared.models.profiles.cuisine_type import CuisineType
from shared.models.profiles.flavor_profile import FlavorProfile
from shared.models.profiles.texture_profile import TextureProfile

# Recipes
from shared.models.recipes.recipe import Recipe
from shared.models.recipes.recipe_ingredient import RecipeIngredient
from shared.models.recipes.recipe_step import RecipeStep
from shared.models.room.diner import Diner

# Room
from shared.models.room.sector import Sector
from shared.models.room.table import Table
from shared.models.room.table_session import TableSession

# Services
from shared.models.services.service_call import ServiceCall
from shared.models.services.waiter_sector_assignment import WaiterSectorAssignment

__all__ = [
    # Base
    "Base",
    "BaseModel",
    # Core
    "Tenant",
    "Branch",
    "User",
    "UserBranchRole",
    "RefreshToken",
    # Catalog
    "Category",
    "Subcategory",
    "Product",
    "BranchProduct",
    "Allergen",
    "AllergenCrossReaction",
    "ProductAllergen",
    "DietaryProfile",
    "ProductDietaryProfile",
    "ProductCookingMethod",
    "ProductBadge",
    "ProductSeal",
    "ProductIngredient",
    # Profiles
    "CookingMethod",
    "FlavorProfile",
    "TextureProfile",
    "CuisineType",
    # Ingredients
    "IngredientGroup",
    "Ingredient",
    "SubIngredient",
    # Room
    "Sector",
    "Table",
    "TableSession",
    "Diner",
    # Orders
    "Round",
    "RoundItem",
    "KitchenTicket",
    # Billing
    "Check",
    "Charge",
    "Allocation",
    "Payment",
    # Services
    "ServiceCall",
    "WaiterSectorAssignment",
    # Marketing
    "Promotion",
    "PromotionProduct",
    "Badge",
    "Seal",
    # Recipes
    "Recipe",
    "RecipeIngredient",
    "RecipeStep",
]
