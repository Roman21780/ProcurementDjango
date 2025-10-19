from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse

from backend.models import (
    User, Shop, Category, Product, ProductInfo, Parameter,
    ProductParameter, Order, OrderItem, Contact, ConfirmEmailToken
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Панель управления пользователями
    """
    model = User

    fieldsets = (
        (None, {'fields': ('email', 'password', 'type')}),
        ('Личная информация', {'fields': ('first_name', 'last_name', 'company', 'position')}),
        ('Разрешения', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'type')
        }),
    )

    list_display = ('email', 'first_name', 'last_name', 'type', 'is_active', 'is_staff')
    list_filter = ('type', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'company')
    ordering = ('email',)


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ('name', 'user_email', 'state', 'product_links')
    list_filter = ('state',)
    search_fields = ('name', 'user__email')
    readonly_fields = ('user',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email владельца'

    def product_links(self, obj):
        count = obj.productinfo_set.count()
        url = (
            reverse('admin:backend_productinfo_changelist')
            + f'?shop__id__exact={obj.id}'
        )
        return format_html('<a href="{}">{}</a>', url, f'{count} товаров')
    product_links.short_description = 'Товары'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'shops_count')
    search_fields = ('name',)
    filter_horizontal = ('shops',)

    def shops_count(self, obj):
        return obj.shops.count()
    shops_count.short_description = 'Количество магазинов'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'productinfo_count')
    list_filter = ('category',)
    search_fields = ('name',)

    def productinfo_count(self, obj):
        count = obj.productinfo_set.count()
        url = (
            reverse('admin:backend_productinfo_changelist')
            + f'?product__id__exact={obj.id}'
        )
        return format_html('<a href="{}">{}</a>', url, f'{count} предложений')
    productinfo_count.short_description = 'Предложения'


class ProductParameterInline(admin.TabularInline):
    model = ProductParameter
    extra = 0


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'shop_name', 'model', 'price', 'quantity')
    list_filter = ('shop', 'product__category')
    search_fields = ('product__name', 'model')
    readonly_fields = ('external_id',)
    inlines = [ProductParameterInline]

    def product_name(self, obj):
        return obj.product.name
    product_name.short_description = 'Товар'

    def shop_name(self, obj):
        return obj.shop.name
    shop_name.short_description = 'Магазин'


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_amount_display',)

    def total_amount_display(self, obj):
        if obj.pk:
            return f"{obj.total_amount} руб."
        return "-"
    total_amount_display.short_description = 'Сумма'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_email', 'dt', 'state', 'total_sum_display', 'contact_info')
    list_filter = ('state', 'dt')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('dt', 'total_sum_display')
    inlines = [OrderItemInline]

    actions = ['mark_confirmed', 'mark_assembled', 'mark_sent', 'mark_delivered']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Покупатель'

    def contact_info(self, obj):
        if obj.contact:
            return f"{obj.contact.city}, {obj.contact.street}"
        return "-"
    contact_info.short_description = 'Адрес'

    def total_sum_display(self, obj):
        try:
            total = obj.total_sum if hasattr(obj, 'total_sum') else sum(
                item.quantity * item.product_info.price for item in obj.ordered_items.all()
            )
            return f"{total} руб."
        except Exception:
            return "-"
    total_sum_display.short_description = 'Общая сумма'

    def mark_confirmed(self, request, queryset):
        updated = queryset.update(state='confirmed')
        self.message_user(request, f"Отмечено как подтвержденные: {updated}")
    mark_confirmed.short_description = "Отметить как подтвержденные"

    def mark_assembled(self, request, queryset):
        updated = queryset.update(state='assembled')
        self.message_user(request, f"Отмечено как собранные: {updated}")
    mark_assembled.short_description = "Отметить как собранные"

    def mark_sent(self, request, queryset):
        updated = queryset.update(state='sent')
        self.message_user(request, f"Отмечено как отправленные: {updated}")
    mark_sent.short_description = "Отметить как отправленные"

    def mark_delivered(self, request, queryset):
        updated = queryset.update(state='delivered')
        self.message_user(request, f"Отмечено как доставленные: {updated}")
    mark_delivered.short_description = "Отметить как доставленные"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_info', 'quantity', 'total_amount_display')
    list_filter = ('order__state',)

    def total_amount_display(self, obj):
        return f"{obj.total_amount} руб."
    total_amount_display.short_description = 'Сумма'


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'city', 'street', 'phone', 'full_address')
    search_fields = ('user__email', 'city', 'street', 'phone')
    list_filter = ('city',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    def full_address(self, obj):
        parts = [obj.city, obj.street]
        if obj.house:
            parts.append(f"д.{obj.house}")
        if obj.apartment:
            parts.append(f"кв.{obj.apartment}")
        return ", ".join(parts)
    full_address.short_description = 'Полный адрес'


@admin.register(ConfirmEmailToken)
class ConfirmEmailTokenAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'key', 'created_at')
    readonly_fields = ('key', 'created_at')
    search_fields = ('user__email',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'


# Кастомизация заголовков админки
admin.site.site_header = "Procurement Platform Admin"
admin.site.site_title = "Procurement Admin"
admin.site.index_title = "Добро пожаловать в панель управления"
