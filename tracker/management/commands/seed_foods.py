from django.core.management.base import BaseCommand
from tracker.models import Food

class Command(BaseCommand):
    help = "Seeds common nutritional foods into the database"

    def handle(self, *args, **options):
        foods_data = [
            # Grains & Staples
            ("Cooked White Rice", "Grains", 100, "100g", 130, 2.7, 28.2, 0.3, 0.4),
            ("Cooked Brown Rice", "Grains", 100, "100g", 112, 2.6, 23.5, 0.9, 1.8),
            ("Roti / Chapati (Whole Wheat)", "Grains", 40, "1 piece (40g)", 104, 3.1, 20.0, 1.2, 2.8),
            ("Oatmeal (Cooked)", "Grains", 100, "100g", 71, 2.5, 12.0, 1.5, 1.7),
            ("Rolled Oats (Raw)", "Grains", 40, "40g (1/2 cup)", 150, 5.3, 27.0, 2.6, 4.0),
            ("Whole Wheat Bread", "Grains", 40, "1 slice (40g)", 95, 4.0, 18.0, 1.1, 2.3),
            ("White Bread", "Grains", 30, "1 slice (30g)", 80, 2.7, 15.0, 1.0, 0.8),
            ("Cooked Pasta", "Grains", 100, "100g", 158, 5.8, 30.9, 0.9, 1.8),
            ("Cooked Quinoa", "Grains", 100, "100g", 120, 4.4, 21.3, 1.9, 2.8),
            ("Idli", "Grains", 50, "1 medium idli (50g)", 65, 2.0, 12.0, 0.4, 0.8),
            ("Plain Dosa", "Grains", 80, "1 medium dosa (80g)", 165, 3.9, 29.0, 3.7, 1.5),

            # Poultry, Meat & Seafood
            ("Chicken Breast (Boneless, Cooked)", "Poultry", 100, "100g", 165, 31.0, 0.0, 3.6, 0.0),
            ("Chicken Thigh (Cooked)", "Poultry", 100, "100g", 209, 26.0, 0.0, 10.9, 0.0),
            ("Whole Boiled Egg", "Eggs", 50, "1 large egg (50g)", 74, 6.3, 0.4, 5.0, 0.0),
            ("Egg White (Boiled)", "Eggs", 33, "1 egg white (33g)", 17, 3.6, 0.2, 0.1, 0.0),
            ("Salmon (Grilled)", "Seafood", 100, "100g", 206, 22.0, 0.0, 12.3, 0.0),
            ("Tuna (Canned in Water)", "Seafood", 100, "100g", 116, 25.5, 0.0, 0.8, 0.0),
            ("White Fish (Cod/Tilapia)", "Seafood", 100, "100g", 105, 22.0, 0.0, 1.5, 0.0),
            ("Lean Beef (Cooked)", "Meat", 100, "100g", 215, 26.0, 0.0, 12.0, 0.0),

            # Vegetarian, Dairy & Plant Proteins
            ("Paneer (Indian Cottage Cheese)", "Dairy", 100, "100g", 265, 18.3, 3.4, 20.8, 0.0),
            ("Tofu (Firm)", "Legumes", 100, "100g", 83, 10.0, 2.3, 5.3, 1.0),
            ("Cooked Yellow Dal (Lentils)", "Legumes", 150, "1 cup/bowl (150g)", 140, 9.0, 20.0, 2.5, 4.5),
            ("Cooked Chickpeas (Chole)", "Legumes", 100, "100g", 164, 8.9, 27.4, 2.6, 7.6),
            ("Cooked Rajma (Kidney Beans)", "Legumes", 100, "100g", 127, 8.7, 22.8, 0.5, 6.4),
            ("Cooked Black Beans", "Legumes", 100, "100g", 132, 8.9, 23.7, 0.5, 8.7),
            ("Soya Chunks (Dry)", "Legumes", 50, "50g", 172, 26.0, 16.5, 0.5, 6.5),
            ("Whey Protein Powder", "Supplements", 30, "1 scoop (30g)", 120, 24.0, 3.0, 1.5, 0.5),

            # Dairy & Milks
            ("Cow Milk (Whole)", "Dairy", 240, "1 cup (240ml)", 149, 7.7, 11.7, 7.9, 0.0),
            ("Cow Milk (Skim / Toned)", "Dairy", 240, "1 cup (240ml)", 83, 8.3, 12.2, 0.2, 0.0),
            ("Greek Yogurt (Low Fat)", "Dairy", 150, "150g", 100, 15.0, 6.0, 1.0, 0.0),
            ("Curd / Dahi (Plain)", "Dairy", 100, "100g", 61, 3.5, 4.7, 3.3, 0.0),
            ("Cheddar Cheese", "Dairy", 28, "1 slice (28g)", 113, 7.0, 0.4, 9.3, 0.0),
            ("Almond Milk (Unsweetened)", "Dairy", 240, "1 cup (240ml)", 30, 1.0, 1.0, 2.5, 1.0),

            # Fruits
            ("Banana", "Fruits", 118, "1 medium banana (118g)", 105, 1.3, 27.0, 0.3, 3.1),
            ("Apple", "Fruits", 182, "1 medium apple (182g)", 95, 0.5, 25.0, 0.3, 4.4),
            ("Orange", "Fruits", 131, "1 medium orange (131g)", 62, 1.2, 15.4, 0.2, 3.1),
            ("Strawberries", "Fruits", 100, "100g", 32, 0.7, 7.7, 0.3, 2.0),
            ("Blueberries", "Fruits", 100, "100g", 57, 0.7, 14.5, 0.3, 2.4),
            ("Watermelon", "Fruits", 100, "100g", 30, 0.6, 7.6, 0.2, 0.4),
            ("Papaya", "Fruits", 100, "100g", 43, 0.5, 10.8, 0.3, 1.7),
            ("Avocado", "Fruits", 100, "100g", 160, 2.0, 8.5, 14.7, 6.7),

            # Vegetables & Greens
            ("Broccoli (Cooked)", "Vegetables", 100, "100g", 35, 2.4, 7.2, 0.4, 3.3),
            ("Spinach (Raw / Palak)", "Vegetables", 100, "100g", 23, 2.9, 3.6, 0.4, 2.2),
            ("Cucumber", "Vegetables", 100, "100g", 15, 0.7, 3.6, 0.1, 0.5),
            ("Tomato", "Vegetables", 100, "100g", 18, 0.9, 3.9, 0.2, 1.2),
            ("Carrot", "Vegetables", 100, "100g", 41, 0.9, 9.6, 0.2, 2.8),
            ("Boiled Potato", "Vegetables", 100, "100g", 87, 1.9, 20.1, 0.1, 1.8),
            ("Sweet Potato (Baked)", "Vegetables", 100, "100g", 90, 2.0, 20.7, 0.2, 3.3),

            # Healthy Fats, Nuts & Seeds
            ("Almonds (Raw)", "Nuts & Seeds", 28, "1 handful (28g)", 164, 6.0, 6.1, 14.2, 3.5),
            ("Walnuts", "Nuts & Seeds", 28, "1 handful (28g)", 185, 4.3, 3.9, 18.5, 1.9),
            ("Peanut Butter", "Nuts & Seeds", 32, "2 tbsp (32g)", 188, 8.0, 6.3, 16.0, 1.9),
            ("Chia Seeds", "Nuts & Seeds", 15, "1 tbsp (15g)", 73, 2.5, 6.3, 4.6, 5.1),
            ("Olive Oil", "Oils", 14, "1 tbsp (14g)", 119, 0.0, 0.0, 13.5, 0.0),
            ("Ghee (Clarified Butter)", "Oils", 14, "1 tbsp (14g)", 123, 0.0, 0.0, 13.9, 0.0),

            # Beverages & Snacks
            ("Black Coffee", "Beverages", 240, "1 cup (240ml)", 2, 0.3, 0.0, 0.0, 0.0),
            ("Green Tea", "Beverages", 240, "1 cup (240ml)", 2, 0.2, 0.0, 0.0, 0.0),
            ("Coconut Water", "Beverages", 240, "1 cup (240ml)", 45, 1.7, 8.9, 0.5, 2.6),
            ("Dark Chocolate 70%", "Snacks", 30, "30g", 180, 2.3, 13.0, 12.8, 3.3),
        ]

        count = 0
        for name, cat, s_g, s_unit, cal, p, c, f, fib in foods_data:
            obj, created = Food.objects.get_or_create(
                user=None,
                name=name,
                defaults={
                    'category': cat,
                    'serving_size_g': s_g,
                    'serving_unit': s_unit,
                    'calories': cal,
                    'protein': p,
                    'carbs': c,
                    'fat': f,
                    'fiber': fib,
                }
            )
            if created:
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} foods into database!"))

