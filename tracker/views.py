from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Q
import datetime

from .models import UserProfile, Food, FoodLog, WaterLog
from .nutrition import evaluate_daily_intake

def get_or_create_profile(user):
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        age = int(request.POST.get('age', 25) or 25)
        gender = request.POST.get('gender', 'male')
        height_cm = float(request.POST.get('height_cm', 170.0) or 170.0)
        weight_kg = float(request.POST.get('weight_kg', 70.0) or 70.0)
        activity_level = request.POST.get('activity_level', 'moderate')
        goal = request.POST.get('goal', 'maintain')

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, 'register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken. Please pick another.")
            return render(request, 'register.html')

        if email and User.objects.filter(email=email).exists():
            messages.error(request, "Email is already registered. Please log in.")
            return render(request, 'register.html')

        user = User.objects.create_user(username=username, email=email, password=password)
        UserProfile.objects.create(
            user=user,
            age=age,
            gender=gender,
            height_cm=height_cm,
            weight_kg=weight_kg,
            activity_level=activity_level,
            goal=goal
        )
        login(request, user)
        messages.success(request, f"Welcome to NutriFit, {user.username}! Your daily nutrition targets are ready.")
        return redirect('dashboard')

    return render(request, 'register.html')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        # Support login by username or email
        user = authenticate(request, username=username, password=password)
        if user is None:
            # Try finding user by email
            try:
                user_obj = User.objects.get(email=username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password. Please try again.")

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@login_required
def profile_view(request):
    profile = get_or_create_profile(request.user)

    if request.method == 'POST':
        profile.age = int(request.POST.get('age', profile.age) or profile.age)
        profile.gender = request.POST.get('gender', profile.gender)
        profile.height_cm = float(request.POST.get('height_cm', profile.height_cm) or profile.height_cm)
        profile.weight_kg = float(request.POST.get('weight_kg', profile.weight_kg) or profile.weight_kg)
        profile.activity_level = request.POST.get('activity_level', profile.activity_level)
        profile.goal = request.POST.get('goal', profile.goal)

        enable_custom = request.POST.get('enable_custom') == '1'
        if enable_custom:
            profile.custom_calories = float(request.POST.get('custom_calories') or 0) or None
            profile.custom_protein = float(request.POST.get('custom_protein') or 0) or None
            profile.custom_carbs = float(request.POST.get('custom_carbs') or 0) or None
            profile.custom_fat = float(request.POST.get('custom_fat') or 0) or None
            profile.custom_fiber = float(request.POST.get('custom_fiber') or 0) or None
            profile.custom_water_ml = float(request.POST.get('custom_water_ml') or 0) or None
        else:
            profile.custom_calories = None
            profile.custom_protein = None
            profile.custom_carbs = None
            profile.custom_fat = None
            profile.custom_fiber = None
            profile.custom_water_ml = None

        profile.save()
        messages.success(request, "Your profile and fitness nutrition goals have been updated!")
        return redirect('profile')

    targets = profile.get_daily_targets()
    return render(request, 'profile.html', {
        'profile': profile,
        'targets': targets,
        'active_tab': 'profile'
    })

@login_required
def dashboard_view(request):
    profile = get_or_create_profile(request.user)
    date_str = request.GET.get('date')

    if date_str:
        try:
            current_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            current_date = timezone.now().date()
    else:
        current_date = timezone.now().date()

    prev_date = (current_date - datetime.timedelta(days=1)).isoformat()
    next_date = (current_date + datetime.timedelta(days=1)).isoformat()
    is_today = (current_date == timezone.now().date())

    targets = profile.get_daily_targets()

    # Query logged foods for current_date
    logs = FoodLog.objects.filter(user=request.user, log_date=current_date).select_related('food')

    meals = {
        'breakfast': [],
        'lunch': [],
        'dinner': [],
        'snack': []
    }
    meal_totals = {
        'breakfast': {'calories': 0.0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0},
        'lunch': {'calories': 0.0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0},
        'dinner': {'calories': 0.0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0},
        'snack': {'calories': 0.0, 'protein': 0.0, 'carbs': 0.0, 'fat': 0.0},
    }
    consumed = {
        'calories': 0.0,
        'protein': 0.0,
        'carbs': 0.0,
        'fat': 0.0,
        'fiber': 0.0,
        'water_ml': 0.0,
    }

    for log in logs:
        m = log.meal_type
        if m in meals:
            meals[m].append(log)
            meal_totals[m]['calories'] += log.calories
            meal_totals[m]['protein'] += log.protein
            meal_totals[m]['carbs'] += log.carbs
            meal_totals[m]['fat'] += log.fat

        consumed['calories'] += log.calories
        consumed['protein'] += log.protein
        consumed['carbs'] += log.carbs
        consumed['fat'] += log.fat
        consumed['fiber'] += log.fiber

    # Round meal totals
    for m in meal_totals:
        for k in meal_totals[m]:
            meal_totals[m][k] = round(meal_totals[m][k], 1)

    # Water intake for date
    water_log = WaterLog.objects.filter(user=request.user, log_date=current_date).first()
    if water_log:
        consumed['water_ml'] = water_log.amount_ml

    # Analysis of intake status (deficit vs surplus vs target met)
    analysis = evaluate_daily_intake(consumed, targets)

    # All foods for logging selector
    available_foods = Food.objects.filter(Q(user__isnull=True) | Q(user=request.user)).order_by('category', 'name')

    return render(request, 'dashboard.html', {
        'current_date': current_date.isoformat(),
        'prev_date': prev_date,
        'next_date': next_date,
        'is_today': is_today,
        'meals': meals,
        'meal_totals': meal_totals,
        'targets': targets,
        'consumed': consumed,
        'analysis': analysis,
        'available_foods': available_foods,
        'active_tab': 'dashboard',
    })

@login_required
def log_food_view(request):
    if request.method == 'POST':
        entry_mode = request.POST.get('entry_mode', 'select')
        meal_type = request.POST.get('meal_type', 'breakfast')
        quantity = float(request.POST.get('quantity', 1.0) or 1.0)
        date_str = request.POST.get('log_date', timezone.now().date().isoformat())

        try:
            log_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            log_date = timezone.now().date()

        if entry_mode == 'manual':
            food_name = request.POST.get('manual_food_name', '').strip()
            if not food_name:
                messages.error(request, "Please enter a food name for manual logging.")
                return redirect(f"{reverse('dashboard')}?date={date_str}")

            calories = float(request.POST.get('manual_calories', 0.0) or 0.0)
            protein = float(request.POST.get('manual_protein', 0.0) or 0.0)
            carbs = float(request.POST.get('manual_carbs', 0.0) or 0.0)
            fat = float(request.POST.get('manual_fat', 0.0) or 0.0)
            fiber = float(request.POST.get('manual_fiber', 0.0) or 0.0)
            serving_size_g = float(request.POST.get('manual_serving_size_g', 100.0) or 100.0)
            serving_unit = request.POST.get('manual_serving_unit', '').strip()
            unit_type = request.POST.get('manual_unit_type', 'g')
            if not serving_unit:
                if unit_type == 'piece':
                    serving_unit = '1 piece'
                elif unit_type == 'ml':
                    serving_unit = f"{int(serving_size_g)}ml"
                else:
                    serving_unit = f"{int(serving_size_g)}g"

            # Always link to a Food item: look up existing user custom food or create one
            food = Food.objects.filter(user=request.user, name__iexact=food_name).first()
            if not food:
                food = Food.objects.create(
                    user=request.user,
                    name=food_name,
                    category='Custom / Manual',
                    serving_size_g=serving_size_g,
                    serving_unit=serving_unit,
                    calories=calories,
                    protein=protein,
                    carbs=carbs,
                    fat=fat,
                    fiber=fiber
                )
        else:
            food_id = request.POST.get('food_id')
            if not food_id:
                messages.error(request, "Please select a food from the library.")
                return redirect(f"{reverse('dashboard')}?date={date_str}")
            food = get_object_or_404(Food, Q(user__isnull=True) | Q(user=request.user), id=food_id)

        serving_amount_g = round(food.serving_size_g * quantity, 1)
        calories = round(food.calories * quantity, 1)
        protein = round(food.protein * quantity, 1)
        carbs = round(food.carbs * quantity, 1)
        fat = round(food.fat * quantity, 1)
        fiber = round(food.fiber * quantity, 1)

        FoodLog.objects.create(
            user=request.user,
            food=food,
            log_date=log_date,
            meal_type=meal_type,
            quantity=quantity,
            serving_amount_g=serving_amount_g,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            fiber=fiber
        )
        messages.success(request, f"Logged {quantity}x {food.name} ({calories} kcal) to {meal_type.title()}!")
        return redirect(f"{reverse('dashboard')}?date={date_str}")

    return redirect('dashboard')

@login_required
def delete_food_log_view(request, log_id):
    if request.method == 'POST':
        log_entry = get_object_or_404(FoodLog, id=log_id, user=request.user)
        date_str = log_entry.log_date.isoformat()
        food_name = log_entry.food.name
        log_entry.delete()
        messages.info(request, f"Removed {food_name} from your food log.")
        return redirect(f"{reverse('dashboard')}?date={date_str}")
    return redirect('dashboard')

@login_required
def update_water_view(request):
    if request.method == 'POST':
        date_str = request.POST.get('log_date', timezone.now().date().isoformat())
        delta_ml = float(request.POST.get('delta_ml', 250))

        try:
            log_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            log_date = timezone.now().date()

        water_log, created = WaterLog.objects.get_or_create(user=request.user, log_date=log_date)
        water_log.amount_ml = max(0.0, water_log.amount_ml + delta_ml)
        water_log.save()

        return redirect(f"{reverse('dashboard')}?date={date_str}")
    return redirect('dashboard')

@login_required
def foods_list_view(request):
    search_query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()

    qs = Food.objects.filter(Q(user__isnull=True) | Q(user=request.user))

    if search_query:
        qs = qs.filter(name__icontains=search_query)

    if category and category != 'All':
        qs = qs.filter(category=category)

    categories = Food.objects.values_list('category', flat=True).distinct().order_by('category')

    return render(request, 'foods.html', {
        'foods': qs,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category,
        'active_tab': 'foods',
    })

@login_required
def add_custom_food_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', 'Custom').strip() or 'Custom'
        unit_type = request.POST.get('unit_type', 'g')
        serving_unit = request.POST.get('serving_unit', '').strip()
        serving_size_g = float(request.POST.get('serving_size_g', 100.0) or 100.0)
        calories = float(request.POST.get('calories', 0.0) or 0.0)
        protein = float(request.POST.get('protein', 0.0) or 0.0)
        carbs = float(request.POST.get('carbs', 0.0) or 0.0)
        fat = float(request.POST.get('fat', 0.0) or 0.0)
        fiber = float(request.POST.get('fiber', 0.0) or 0.0)

        if not serving_unit:
            if unit_type == 'piece':
                serving_unit = '1 piece'
            elif unit_type == 'ml':
                serving_unit = f"{int(serving_size_g)}ml"
            else:
                serving_unit = f"{int(serving_size_g)}g"

        if not name:
            messages.error(request, "Food name is required.")
            return redirect('foods_list')

        Food.objects.create(
            user=request.user,
            name=name,
            category=category,
            serving_size_g=serving_size_g,
            serving_unit=serving_unit,
            calories=calories,
            protein=protein,
            carbs=carbs,
            fat=fat,
            fiber=fiber
        )
        messages.success(request, f"Added custom food '{name}' ({serving_unit}) to your library!")
        return redirect('foods_list')

    return redirect('foods_list')

@login_required
def edit_custom_food_view(request, food_id):
    food = get_object_or_404(Food, id=food_id, user=request.user)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category = request.POST.get('category', 'Custom').strip() or 'Custom'
        unit_type = request.POST.get('unit_type', 'g')
        serving_unit = request.POST.get('serving_unit', '').strip()
        serving_size_g = float(request.POST.get('serving_size_g', 100.0) or 100.0)
        calories = float(request.POST.get('calories', 0.0) or 0.0)
        protein = float(request.POST.get('protein', 0.0) or 0.0)
        carbs = float(request.POST.get('carbs', 0.0) or 0.0)
        fat = float(request.POST.get('fat', 0.0) or 0.0)
        fiber = float(request.POST.get('fiber', 0.0) or 0.0)

        if not serving_unit:
            if unit_type == 'piece':
                serving_unit = '1 piece'
            elif unit_type == 'ml':
                serving_unit = f"{int(serving_size_g)}ml"
            else:
                serving_unit = f"{int(serving_size_g)}g"

        if not name:
            messages.error(request, "Food name is required.")
            return redirect('foods_list')

        food.name = name
        food.category = category
        food.serving_unit = serving_unit
        food.serving_size_g = serving_size_g
        food.calories = calories
        food.protein = protein
        food.carbs = carbs
        food.fat = fat
        food.fiber = fiber
        food.save()

        messages.success(request, f"Updated custom food '{name}' successfully!")
        return redirect('foods_list')

    return redirect('foods_list')

@login_required
def delete_custom_food_view(request, food_id):
    food = get_object_or_404(Food, id=food_id, user=request.user)
    if request.method == 'POST':
        name = food.name
        food.delete()
        messages.success(request, f"Deleted custom food '{name}'.")
        return redirect('foods_list')
    return redirect('foods_list')

@login_required
def history_view(request):
    profile = get_or_create_profile(request.user)
    targets = profile.get_daily_targets()

    # Aggregate last 14 days
    today = timezone.now().date()
    start_date = today - datetime.timedelta(days=13)

    daily_logs = FoodLog.objects.filter(
        user=request.user,
        log_date__range=[start_date, today]
    ).values('log_date').annotate(
        total_calories=Sum('calories'),
        total_protein=Sum('protein'),
        total_carbs=Sum('carbs'),
        total_fat=Sum('fat'),
        total_fiber=Sum('fiber')
    ).order_by('-log_date')

    # Water map
    water_logs = {
        wl.log_date: wl.amount_ml
        for wl in WaterLog.objects.filter(user=request.user, log_date__range=[start_date, today])
    }

    history_records = []
    for item in daily_logs:
        d = item['log_date']
        w = water_logs.get(d, 0)
        history_records.append({
            'date': d,
            'calories': round(item['total_calories'] or 0, 1),
            'protein': round(item['total_protein'] or 0, 1),
            'carbs': round(item['total_carbs'] or 0, 1),
            'fat': round(item['total_fat'] or 0, 1),
            'fiber': round(item['total_fiber'] or 0, 1),
            'water_ml': round(w),
            'cal_status': 'Surplus' if (item['total_calories'] or 0) > targets['calories'] + 150 else ('Deficit' if (item['total_calories'] or 0) < targets['calories'] - 150 else 'Optimal')
        })

    # Prepare chart arrays (ordered chronologically)
    sorted_records = sorted(history_records, key=lambda x: x['date'])
    chart_dates = [r['date'].strftime('%b %d') for r in sorted_records]
    chart_calories = [r['calories'] for r in sorted_records]
    chart_protein = [r['protein'] for r in sorted_records]

    return render(request, 'history.html', {
        'history_records': history_records,
        'targets': targets,
        'chart_dates': chart_dates,
        'chart_calories': chart_calories,
        'chart_protein': chart_protein,
        'active_tab': 'history',
    })

@login_required
def api_food_detail(request, food_id):
    food = get_object_or_404(Food, Q(user__isnull=True) | Q(user=request.user), id=food_id)
    return JsonResponse({
        'id': food.id,
        'name': food.name,
        'category': food.category,
        'serving_size_g': food.serving_size_g,
        'serving_unit': food.serving_unit,
        'calories': food.calories,
        'protein': food.protein,
        'carbs': food.carbs,
        'fat': food.fat,
        'fiber': food.fiber,
    })

@login_required
def export_monthly_excel_view(request):
    from django.http import HttpResponse
    from .excel_export import generate_monthly_performance_excel
    import datetime

    today = timezone.now().date()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
        if month < 1 or month > 12:
            month = today.month
    except (ValueError, TypeError):
        year = today.year
        month = today.month

    profile = get_or_create_profile(request.user)
    excel_buffer = generate_monthly_performance_excel(request.user, profile, year, month)

    filename = f"NutriFit_Performance_{year}_{month:02d}.xlsx"
    response = HttpResponse(
        excel_buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
