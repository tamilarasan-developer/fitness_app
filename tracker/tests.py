from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from tracker.models import UserProfile, Food, FoodLog, WaterLog
from tracker.nutrition import evaluate_daily_intake
import datetime

class FitnessNutritionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testfitness',
            email='test@fit.com',
            password='testpassword123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            age=25,
            gender='male',
            height_cm=175.0,
            weight_kg=75.0,
            activity_level='moderate',
            goal='maintain'
        )
        self.food = Food.objects.create(
            name='Test Chicken Breast',
            category='Poultry',
            serving_size_g=100.0,
            serving_unit='100g',
            calories=165.0,
            protein=31.0,
            carbs=0.0,
            fat=3.6,
            fiber=0.0
        )
        self.client = Client()

    def test_bmr_and_targets_calculation(self):
        # Men: (10 * 75) + (6.25 * 175) - (5 * 25) + 5 = 750 + 1093.75 - 125 + 5 = 1723.75 -> round to 1724
        bmr = self.profile.get_bmr()
        self.assertAlmostEqual(bmr, 1724, delta=2)

        tdee = self.profile.get_tdee()
        self.assertGreater(tdee, bmr)

        targets = self.profile.get_daily_targets()
        self.assertIn('calories', targets)
        self.assertIn('protein', targets)
        self.assertIn('carbs', targets)
        self.assertIn('fat', targets)
        self.assertEqual(targets['protein'], 150.0) # 75kg * 2.0g = 150g

    def test_evaluate_daily_intake_status(self):
        targets = {'calories': 2000, 'protein': 150, 'carbs': 200, 'fat': 60, 'fiber': 30, 'water_ml': 2500}
        
        # Test Deficit scenario
        consumed_deficit = {'calories': 1400, 'protein': 80, 'carbs': 150, 'fat': 40, 'fiber': 15, 'water_ml': 1200}
        analysis = evaluate_daily_intake(consumed_deficit, targets)
        self.assertEqual(analysis['calories']['status'], 'deficit')
        self.assertIn('needed', analysis['calories']['badge'])
        self.assertEqual(analysis['protein']['status'], 'deficit')
        self.assertIn('needed', analysis['protein']['badge'])

        # Test Optimal / Met scenario
        consumed_optimal = {'calories': 2010, 'protein': 152, 'carbs': 198, 'fat': 61, 'fiber': 31, 'water_ml': 2600}
        analysis_opt = evaluate_daily_intake(consumed_optimal, targets)
        self.assertEqual(analysis_opt['calories']['status'], 'optimal')
        self.assertEqual(analysis_opt['protein']['status'], 'optimal')

    def test_food_logging_and_portion_multiplier(self):
        self.client.login(username='testfitness', password='testpassword123')
        today_str = datetime.date.today().isoformat()
        
        # Log 2 servings (2x 100g = 200g, 330 kcal, 62g protein)
        response = self.client.post(reverse('log_food'), {
            'food_id': self.food.id,
            'meal_type': 'lunch',
            'quantity': 2.0,
            'log_date': today_str
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        log = FoodLog.objects.filter(user=self.user, meal_type='lunch').first()
        self.assertIsNotNone(log)
        self.assertEqual(log.quantity, 2.0)
        self.assertEqual(log.calories, 330.0)
        self.assertEqual(log.protein, 62.0)

    def test_water_logging(self):
        self.client.login(username='testfitness', password='testpassword123')
        today_str = datetime.date.today().isoformat()

        response = self.client.post(reverse('update_water'), {
            'log_date': today_str,
            'delta_ml': 500
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        water_log = WaterLog.objects.filter(user=self.user).first()
        self.assertIsNotNone(water_log)
        self.assertEqual(water_log.amount_ml, 500.0)

    def test_excel_monthly_export(self):
        self.client.login(username='testfitness', password='testpassword123')
        today = datetime.date.today()
        # Log a meal
        FoodLog.objects.create(
            user=self.user,
            food=self.food,
            meal_type='breakfast',
            quantity=1.5,
            serving_amount_g=150.0,
            calories=247.5,
            protein=46.5,
            carbs=0.0,
            fat=5.4,
            fiber=0.0,
            log_date=today
        )
        response = self.client.get(reverse('export_monthly_excel'), {'year': today.year, 'month': today.month})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('attachment; filename=', response['Content-Disposition'])
        self.assertGreater(len(response.content), 1000)

    def test_manual_food_logging(self):
        self.client.login(username='testfitness', password='testpassword123')
        today_str = datetime.date.today().isoformat()

        response = self.client.post(reverse('log_food'), {
            'entry_mode': 'manual',
            'manual_food_name': 'Homemade Masala Dosa',
            'manual_calories': 240,
            'manual_protein': 6.0,
            'manual_carbs': 38.0,
            'manual_fat': 7.0,
            'manual_fiber': 3.0,
            'manual_serving_size_g': 150.0,
            'manual_serving_unit': '1 plate',
            'quantity': 2.0,
            'meal_type': 'dinner',
            'log_date': today_str
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        # Check custom food was created
        custom_food = Food.objects.filter(user=self.user, name='Homemade Masala Dosa').first()
        self.assertIsNotNone(custom_food)
        self.assertEqual(custom_food.calories, 240.0)

        # Check FoodLog entry was created with 2x multiplier
        log = FoodLog.objects.filter(user=self.user, meal_type='dinner', food=custom_food).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.quantity, 2.0)
        self.assertEqual(log.calories, 480.0)
        self.assertEqual(log.protein, 12.0)
        self.assertEqual(log.carbs, 76.0)

    def test_piece_and_ml_measurements(self):
        self.client.login(username='testfitness', password='testpassword123')
        today_str = datetime.date.today().isoformat()

        # 1. Test logging 3 pieces of Fish
        res_fish = self.client.post(reverse('log_food'), {
            'entry_mode': 'manual',
            'manual_food_name': 'Fried Fish Pieces',
            'manual_unit_type': 'piece',
            'manual_serving_unit': '1 piece',
            'manual_serving_size_g': 50.0,
            'manual_calories': 70.0,
            'manual_protein': 12.0,
            'manual_carbs': 1.0,
            'manual_fat': 2.0,
            'quantity': 3.0,
            'meal_type': 'snack',
            'log_date': today_str
        }, follow=True)
        self.assertEqual(res_fish.status_code, 200)

        fish_log = FoodLog.objects.filter(user=self.user, food__name='Fried Fish Pieces').first()
        self.assertIsNotNone(fish_log)
        self.assertEqual(fish_log.quantity, 3.0)
        self.assertEqual(fish_log.calories, 210.0)
        self.assertEqual(fish_log.get_portion_display(), '3 pieces')

        # 2. Test logging 250ml Milk (2.5x 100ml)
        res_milk = self.client.post(reverse('log_food'), {
            'entry_mode': 'manual',
            'manual_food_name': 'Full Cream Milk',
            'manual_unit_type': 'ml',
            'manual_serving_unit': '100ml',
            'manual_serving_size_g': 100.0,
            'manual_calories': 62.0,
            'manual_protein': 3.2,
            'manual_carbs': 4.8,
            'manual_fat': 3.5,
            'quantity': 2.5,
            'meal_type': 'breakfast',
            'log_date': today_str
        }, follow=True)
        self.assertEqual(res_milk.status_code, 200)

        milk_log = FoodLog.objects.filter(user=self.user, food__name='Full Cream Milk').first()
        self.assertIsNotNone(milk_log)
        self.assertEqual(milk_log.calories, 155.0)
        self.assertEqual(milk_log.get_portion_display(), '250 ml')

        # 3. Test add_custom_food view with ml
        res_custom = self.client.post(reverse('add_custom_food'), {
            'name': 'Almond Milk',
            'category': 'Dairy',
            'unit_type': 'ml',
            'serving_size_g': 200,
            'calories': 35,
            'protein': 1.0,
            'carbs': 1.5,
            'fat': 2.5
        }, follow=True)
        self.assertEqual(res_custom.status_code, 200)
        almond = Food.objects.filter(user=self.user, name='Almond Milk').first()
        self.assertIsNotNone(almond)
        self.assertEqual(almond.serving_unit, '200ml')




