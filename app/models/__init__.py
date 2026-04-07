from app.models.audit import AdminActivityLog
from app.models.catalog import Category, CategoryMeta, Product, ProductCustomizationRule, ProductImage, ProductMeta, ProductRelation, ProductReview, ProductSpecification, ProductTag, ProductVariant, product_category_link, product_tag_link
from app.models.checkout import Cart, CartItem, Coupon, CouponProduct, Order, OrderAddress, OrderItem, OrderShipment, OrderStatusHistory, SavedItem
from app.models.media import MediaAsset, UploadedCustomerFile
from app.models.operations import InventoryMovement, RedirectRule, ShippingMethod, ShippingRateRule, TaxRule
from app.models.payment import Payment, PaymentGateway, PaymentGatewayConfig, PaymentMethod, PaymentMethodDetails, PaymentRefund, PaymentRoutingRule, PaymentStatus, PaymentTransaction, PaymentType
from app.models.settings import Banner, Campaign, NewsletterSubscriber, StoreSetting
from app.models.user import Address, PasswordResetToken, Permission, RefreshToken, Role, RolePermission, User, UserRole, Wishlist

all_models = [
    User,
    Role,
    Permission,
    RolePermission,
    UserRole,
    RefreshToken,
    PasswordResetToken,
    Address,
    Wishlist,
    Category,
    CategoryMeta,
    Product,
    ProductMeta,
    ProductImage,
    ProductVariant,
    ProductSpecification,
    ProductTag,
    ProductCustomizationRule,
    ProductRelation,
    ProductReview,
    Cart,
    CartItem,
    SavedItem,
    Coupon,
    CouponProduct,
    Order,
    OrderItem,
    OrderAddress,
    OrderShipment,
    OrderStatusHistory,
    Payment,
    PaymentTransaction,
    PaymentRefund,
    PaymentMethodDetails,
    PaymentGatewayConfig,
    PaymentRoutingRule,
    MediaAsset,
    UploadedCustomerFile,
    ShippingMethod,
    ShippingRateRule,
    TaxRule,
    InventoryMovement,
    RedirectRule,
    NewsletterSubscriber,
    Banner,
    Campaign,
    StoreSetting,
    AdminActivityLog,
]
