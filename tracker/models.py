from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    ACTIVITY_CHOICES = [
        ('sedentary', 'Sedentary (desk job, little/no exercise)'),
        ('light', 'Lightly Active (light exercise 1-3 days/wk)'),
        ('moderate', 'Moderately Active (exercise 3-5 days/wk)'),
        ('active', 'Very Active (hard exercise 6-7 days/wk)'),
        ('very_active', 'Extra Active (physical job or athlete)'),
    ]

    GOAL_CHOICES = [
        ('lose_fast', 'Aggressive Fat Loss (-500 kcal)'),
        ('lose_mild', 'Steady Fat Loss (-250 kcal)'),
        ('maintain', 'Maintain Current Weight'),
        ('gain_lean', 'Lean Muscle Gain (+250 kcal)'),
        ('gain_bulk', 'Muscle Bulking (+500 kcal)'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    age = models.PositiveIntegerField(default=25)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')
    height_cm = models.FloatField(default=170.0, help_text="Height in cm")
    weight_kg = models.FloatField(default=70.0, help_text="Weight in kg")
    activity_level = models.CharField(max_length=20, choices=ACTIVITY_CHOICES, default='moderate')
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES, default='maintain')

    # Custom override fields
    custom_calories = models.FloatField(null=True, blank=True)
    custom_protein = models.FloatField(null=True, blank=True)
    custom_carbs = models.FloatField(null=True, blank=True)
    custom_fat = models.FloatField(null=True, blank=True)
    custom_fiber = models.FloatField(null=True, blank=True)
    custom_water_ml = models.FloatField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_bmr(self):
        """Mifflin-St Jeor Equation"""
        if self.gender == 'female':
            return round((10 * self.weight_kg) + (6.25 * self.height_cm) - (5 * self.age) - 161)
        return round((10 * self.weight_kg) + (6.25 * self.height_cm) - (5 * self.age) + 5)

    def get_tdee(self):
        """Total Daily Energy Expenditure"""
        multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'very_active': 1.9,
        }
        multiplier = multipliers.get(self.activity_level, 1.55)
        return round(self.get_bmr() * multiplier)

    def get_daily_targets(self):
        """Calculate recommended daily calorie and macro goals"""
        bmr = self.get_bmr()
        tdee = self.get_tdee()

        # If custom targets are explicitly set
        if self.custom_calories and self.custom_calories > 0:
            return {
                'bmr': bmr,
                'tdee': tdee,
                'calories': round(self.custom_calories),
                'protein': round(self.custom_protein or (self.weight_kg * 2.0)),
                'carbs': round(self.custom_carbs or 200),
                'fat': round(self.custom_fat or 60),
                'fiber': round(self.custom_fiber or 30),
                'water_ml': round(self.custom_water_ml or (self.weight_kg * 35)),
            }

        goal_adjustments = {
            'lose_fast': -500,
            'lose_mild': -250,
            'maintain': 0,
            'gain_lean': +250,
            'gain_bulk': +500,
        }
        adjustment = goal_adjustments.get(self.goal, 0)
        target_calories = max(1200, tdee + adjustment)

        # Standard optimal sports nutrition ratio:
        # Protein: 2.0g per kg of body weight
        # Fat: ~25% of total energy
        # Carbs: Remainder of calories
        target_protein = round(self.weight_kg * 2.0, 1)
        protein_kcal = target_protein * 4

        fat_kcal = target_calories * 0.25
        target_fat = round(fat_kcal / 9.0, 1)

        remaining_kcal = max(0, target_calories - protein_kcal - fat_kcal)
        target_carbs = round(remaining_kcal / 4.0, 1)

        # Fiber: ~14g per 1000 kcal
        target_fiber = round((target_calories / 1000.0) * 14.0, 1)

        # Water: ~35ml per kg body weight
        target_water_ml = round(self.weight_kg * 35)

        return {
            'bmr': bmr,
            'tdee': tdee,
            'calories': round(target_calories),
            'protein': round(target_protein),
            'carbs': round(target_carbs),
            'fat': round(target_fat),
            'fiber': round(target_fiber),
            'water_ml': target_water_ml,
        }


class Food(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE, related_name='custom_foods',
                            help_text="Null for global system foods, user set for custom foods")
    name = models.CharField(max_length=150)
    category = models.CharField(max_length=50, default='General')
    serving_size_g = models.FloatField(default=100.0, help_text="Weight of serving in grams")
    serving_unit = models.CharField(max_length=50, default='100g')
    calories = models.FloatField(help_text="Calories (kcal)")
    protein = models.FloatField(help_text="Protein in grams")
    carbs = models.FloatField(help_text="Carbohydrates in grams")
    fat = models.FloatField(help_text="Fats in grams")
    fiber = models.FloatField(default=0.0, help_text="Dietary fiber in grams")

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.calories} kcal / {self.serving_unit})"


class FoodLog(models.Model):
    MEAL_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snacks & Others'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='food_logs')
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    log_date = models.DateField(default=timezone.now)
    meal_type = models.CharField(max_length=20, choices=MEAL_CHOICES, default='breakfast')
    quantity = models.FloatField(default=1.0, help_text="Multiplier of serving unit")
    serving_amount_g = models.FloatField()
    calories = models.FloatField()
    protein = models.FloatField()
    carbs = models.FloatField()
    fat = models.FloatField()
    fiber = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def get_portion_display(self):
        unit = (self.food.serving_unit or '').lower()
        if 'ml' in unit:
            return f"{round(self.serving_amount_g)} ml"
        elif any(k in unit for k in ['piece', 'pc', 'slice', 'egg', 'item', 'biscuit', 'roti', 'idli', 'dosa']):
            qty = int(self.quantity) if self.quantity.is_integer() else self.quantity
            unit_name = 'piece' if qty == 1 else 'pieces'
            if 'slice' in unit:
                unit_name = 'slice' if qty == 1 else 'slices'
            elif 'egg' in unit:
                unit_name = 'egg' if qty == 1 else 'eggs'
            elif 'roti' in unit:
                unit_name = 'roti' if qty == 1 else 'rotis'
            elif 'idli' in unit:
                unit_name = 'idli' if qty == 1 else 'idlis'
            return f"{qty} {unit_name}"
        elif 'cup' in unit:
            qty = int(self.quantity) if self.quantity.is_integer() else self.quantity
            return f"{qty} cup{'s' if qty != 1 else ''}"
        elif 'glass' in unit:
            qty = int(self.quantity) if self.quantity.is_integer() else self.quantity
            return f"{qty} glass{'es' if qty != 1 else ''}"
        elif 'scoop' in unit:
            qty = int(self.quantity) if self.quantity.is_integer() else self.quantity
            return f"{qty} scoop{'s' if qty != 1 else ''}"
        else:
            return f"{round(self.serving_amount_g)}g"

    def __str__(self):
        return f"{self.user.username} - {self.meal_type}: {self.food.name} ({self.calories} kcal)"


class WaterLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='water_logs')
    log_date = models.DateField(default=timezone.now)
    amount_ml = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'log_date')

    def __str__(self):
        return f"{self.user.username} - {self.log_date}: {self.amount_ml} ml"
