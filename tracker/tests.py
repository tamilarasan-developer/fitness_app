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


