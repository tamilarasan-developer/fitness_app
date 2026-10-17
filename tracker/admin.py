from django.contrib import admin
from .models import UserProfile, Food, FoodLog, WaterLog

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'age', 'gender', 'weight_kg', 'height_cm', 'activity_level', 'goal')
    search_fields = ('user__username', 'user__email')

@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'serving_unit', 'calories', 'protein', 'carbs', 'fat', 'fiber', 'user')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(FoodLog)
class FoodLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'log_date', 'meal_type', 'food', 'quantity', 'calories', 'protein', 'created_at')
    list_filter = ('meal_type', 'log_date')
    search_fields = ('user__username', 'food__name')

@admin.register(WaterLog)
class WaterLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'log_date', 'amount_ml')
    list_filter = ('log_date',)
