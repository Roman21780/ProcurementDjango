from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

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
    list_display = ('name', 'user', 'state', 'url')
    list_filter = ('state',)
    search_fields = ('name', 'user__email')
    readonly_fields = ('user',)


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
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name',)


class ProductParameterInline(admin.TabularInline):
    model = ProductParameter
    extra = 0


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = ('product', 'shop', 'model', 'price', 'quantity')
    list_filter = ('shop', 'product__category')
    search_fields = ('product__name', 'model')
    readonly_fields = ('external_id',)
    inlines = [ProductParameterInline]


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('total_amount',)

    def total_amount(self, obj):
        if obj.pk:
            return f"{obj.total_amount} руб."
        return "-"
    total_amount.short_description = 'Сумма'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'dt', 'state', 'total_sum_display', 'contact')
    list_filter = ('state', 'dt')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('dt', 'total_sum_display')
    inlines = [OrderItemInline]

    actions = ['mark_confirmed', 'mark_assembled', 'mark_sent', 'mark_delivered']

    def total_sum_display(self, obj):
        return f"{obj.total_sum} руб."
    total_sum_display.short_description = 'Общая сумма'

    def mark_confirmed(self, request, queryset):
        queryset.update(state='confirmed')
        self.message_user(request, f"Заказы отмечены как подтвержденные")
    mark_confirmed.short_description = "Отметить как подтвержденные"

    def mark_assembled(self, request, queryset):
        queryset.update(state='assembled')
        self.message_user(request, f"Заказы отмечены как собранные")
    mark_assembled.short_description = "Отметить как собранные"

    def mark_sent(self, request, queryset):
        queryset.update(state='sent')
        self.message_user(request, f"Заказы отмечены как отправленные")
    mark_sent.short_description = "Отметить как отправленные"

    def mark_delivered(self, request, queryset):
        queryset.update(state='delivered')
        self.message_user(request, f"Заказы отмечены как доставленные")
    mark_delivered.short_description = "Отметить как доставленные"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_info', 'quantity', 'total_amount')
    list_filter = ('order__state',)

    def total_amount(self, obj):
        return f"{obj.total_amount} руб."
    total_amount.short_description = 'Сумма'


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'street', 'phone')
    search_fields = ('user__email', 'city', 'street', 'phone')
    list_filter = ('city',)


@admin.register(ConfirmEmailToken)
class ConfirmEmailTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'created_at')
    readonly_fields = ('key', 'created_at')
    search_fields = ('user__email',)
