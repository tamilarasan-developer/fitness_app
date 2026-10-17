import io
import datetime
import calendar
from django.db.models import Sum
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from .models import FoodLog, WaterLog
from .nutrition import evaluate_daily_intake

def generate_monthly_performance_excel(user, profile, year, month):
    """
    Generates a beautifully formatted, multi-tab Excel workbook
    analyzing the user's monthly nutritional performance.
    """
    targets = profile.get_daily_targets()
    month_name = calendar.month_name[month]
    num_days = calendar.monthrange(year, month)[1]
    start_date = datetime.date(year, month, 1)
    end_date = datetime.date(year, month, num_days)

    wb = Workbook()
    
    # -------------------------------------------------------------------------
    # STYLES & COLOR PALETTE
    # -------------------------------------------------------------------------
    header_fill = PatternFill(start_color="047857", end_color="047857", fill_type="solid") # Emerald 700
    subheader_fill = PatternFill(start_color="065F46", end_color="065F46", fill_type="solid") # Emerald 800
    kpi_title_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid") # Slate 800
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    
    status_optimal_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid") # Green 100
    status_deficit_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid") # Yellow 100
    status_surplus_fill = PatternFill(start_color="FFE4E6", end_color="FFE4E6", fill_type="solid") # Red 100

    font_title = Font(name="Calibri", size=16, bold=True, color="FFFFFF")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_bold = Font(name="Calibri", size=10, bold=True)
    font_regular = Font(name="Calibri", size=10)
    font_kpi_val = Font(name="Calibri", size=13, bold=True, color="047857")

    thin_border_side = Side(style='thin', color='CBD5E1')
    thin_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)

    # -------------------------------------------------------------------------
    # SHEET 1: Monthly Summary & Daily Performance
    # -------------------------------------------------------------------------
    ws1 = wb.active
    ws1.title = "Monthly Performance"
    ws1.views.sheetView[0].showGridLines = True

    # Title Block
    ws1.merge_cells("A1:M1")
    title_cell = ws1["A1"]
    title_cell.value = f"NutriFit — Monthly Performance Report: {month_name} {year}"
    title_cell.font = font_title
    title_cell.fill = header_fill
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[1].height = 36

    # User Profile & Biometrics Bar
    ws1.merge_cells("A2:M2")
    user_bar = ws1["A2"]
    user_bar.value = (
        f"Athlete: {user.username}  |  Weight: {profile.weight_kg}kg  |  Height: {profile.height_cm}cm  |  "
        f"Target Calories: {targets['calories']} kcal/day  |  Target Protein: {targets['protein']}g/day  |  "
        f"Goal: {profile.get_goal_display()}"
    )
    user_bar.font = Font(name="Calibri", size=10, italic=True, color="FFFFFF")
    user_bar.fill = subheader_fill
    user_bar.alignment = Alignment(horizontal="center", vertical="center")
    ws1.row_dimensions[2].height = 22

    # Query daily aggregates for month
    daily_aggregates = FoodLog.objects.filter(
        user=user,
        log_date__range=[start_date, end_date]
    ).values('log_date').annotate(
        total_calories=Sum('calories'),
        total_protein=Sum('protein'),
        total_carbs=Sum('carbs'),
        total_fat=Sum('fat'),
        total_fiber=Sum('fiber')
    ).order_by('log_date')

    daily_dict = {item['log_date']: item for item in daily_aggregates}

    water_logs = {
        wl.log_date: wl.amount_ml
        for wl in WaterLog.objects.filter(user=user, log_date__range=[start_date, end_date])
    }

    # Calculate overall KPIs
    days_logged = len(daily_dict)
    total_cal_sum = sum(d['total_calories'] for d in daily_dict.values()) if days_logged else 0
    total_prot_sum = sum(d['total_protein'] for d in daily_dict.values()) if days_logged else 0
    total_water_sum = sum(water_logs.values()) if water_logs else 0

    avg_cal = round(total_cal_sum / days_logged, 1) if days_logged else 0
    avg_prot = round(total_prot_sum / days_logged, 1) if days_logged else 0
    avg_water = round(total_water_sum / days_logged) if days_logged else 0

    protein_met_days = sum(1 for d in daily_dict.values() if d['total_protein'] >= (targets['protein'] - 5))

    # KPI Summary Cards Block (Rows 4-5)
    kpis = [
        ("Days Logged", f"{days_logged} of {num_days} days"),
        ("Avg Daily Calories", f"{avg_cal} kcal (Goal: {targets['calories']})"),
        ("Avg Daily Protein", f"{avg_prot}g (Goal: {targets['protein']}g)"),
        ("Protein Target Hit", f"{protein_met_days} days ({round(protein_met_days / max(1, days_logged) * 100)}%)"),
        ("Avg Hydration", f"{avg_water} ml/day"),
    ]

    ws1.cell(row=4, column=1, value="Monthly Performance Summary").font = Font(name="Calibri", size=11, bold=True)
    col_idx = 1
    for title, val in kpis:
        c_title = ws1.cell(row=5, column=col_idx, value=title)
        c_title.font = Font(name="Calibri", size=9, bold=True, color="64748B")
        c_val = ws1.cell(row=6, column=col_idx, value=val)
        c_val.font = font_kpi_val
        col_idx += 2

    # Data Table Headers (Row 8)
    headers = [
        "Date", "Calories (kcal)", "Target (kcal)", "Variance", "Calorie Status",
        "Protein (g)", "Target Protein", "Carbs (g)", "Fat (g)", "Fiber (g)",
        "Water (ml)", "Hydration %", "Compliance Score"
    ]

    row_num = 8
    ws1.row_dimensions[row_num].height = 24
    for col_idx, header in enumerate(headers, 1):
        cell = ws1.cell(row=row_num, column=col_idx, value=header)
        cell.font = font_header
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border

    # Populate all days of the month
    current_day = start_date
    row_num = 9

    while current_day <= end_date:
        data = daily_dict.get(current_day)
        water_ml = water_logs.get(current_day, 0.0)

        if data:
            c_cal = round(data['total_calories'], 1)
            c_prot = round(data['total_protein'], 1)
            c_carbs = round(data['total_carbs'], 1)
            c_fat = round(data['total_fat'], 1)
            c_fiber = round(data['total_fiber'], 1)
            variance = round(c_cal - targets['calories'])
            
            if variance < -150:
                cal_status = "Deficit"
                status_fill = status_deficit_fill
            elif abs(variance) <= 150:
                cal_status = "On Target"
                status_fill = status_optimal_fill
            else:
                cal_status = "Surplus"
                status_fill = status_surplus_fill

            # Calculate daily compliance score
            consumed_dict = {
                'calories': c_cal,
                'protein': c_prot,
                'carbs': c_carbs,
                'fat': c_fat,
                'fiber': c_fiber,
                'water_ml': water_ml
            }
            evaluation = evaluate_daily_intake(consumed_dict, targets)
            daily_score = f"{evaluation['nutrition_score']['value']}% ({evaluation['nutrition_score']['grade']})"
            water_pct = f"{evaluation['water']['actual_percentage']}%"

        else:
            c_cal = "-"
            variance = "-"
            cal_status = "No Log"
            status_fill = None
            c_prot = "-"
            c_carbs = "-"
            c_fat = "-"
            c_fiber = "-"
            daily_score = "-"
            water_pct = "-"

        row_values = [
            current_day.strftime("%Y-%m-%d (%a)"),
            c_cal,
            targets['calories'],
            variance if variance == "-" else f"{variance:+d}",
            cal_status,
            c_prot,
            targets['protein'],
            c_carbs,
            c_fat,
            c_fiber,
            round(water_ml) if water_ml > 0 else "-",
            water_pct,
            daily_score
        ]

        ws1.row_dimensions[row_num].height = 20
        is_zebra = (row_num % 2 == 0)

        for col_idx, val in enumerate(row_values, 1):
            cell = ws1.cell(row=row_num, column=col_idx, value=val)
            cell.font = font_regular
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center", vertical="center")

            if col_idx == 5 and status_fill:
                cell.fill = status_fill
                cell.font = font_bold
            elif is_zebra:
                cell.fill = zebra_fill

        current_day += datetime.timedelta(days=1)
        row_num += 1

    # -------------------------------------------------------------------------
    # SHEET 2: Detailed Meal-by-Meal Log
    # -------------------------------------------------------------------------
    ws2 = wb.create_sheet(title="Detailed Meals Log")
    ws2.views.sheetView[0].showGridLines = True

    # Title
    ws2.merge_cells("A1:J1")
    title_meals = ws2["A1"]
    title_meals.value = f"NutriFit — Complete Food Logs for {month_name} {year}"
    title_meals.font = font_title
    title_meals.fill = header_fill
    title_meals.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 36

    meal_headers = [
        "Date", "Meal Period", "Food Name", "Category", "Quantity",
        "Portion Weight (g)", "Calories (kcal)", "Protein (g)", "Carbs (g)", "Fat (g)"
    ]

    ws2.row_dimensions[3].height = 24
    for col_idx, header in enumerate(meal_headers, 1):
        cell = ws2.cell(row=3, column=col_idx, value=header)
        cell.font = font_header
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    food_logs = FoodLog.objects.filter(
        user=user,
        log_date__range=[start_date, end_date]
    ).select_related('food').order_by('log_date', 'meal_type')

    row_num = 4
    for log in food_logs:
        ws2.row_dimensions[row_num].height = 19
        is_zebra = (row_num % 2 == 0)

        row_vals = [
            log.log_date.strftime("%Y-%m-%d"),
            log.get_meal_type_display(),
            log.food.name,
            log.food.category,
            f"{log.quantity}x",
            log.serving_amount_g,
            log.calories,
            log.protein,
            log.carbs,
            log.fat
        ]

        for col_idx, val in enumerate(row_vals, 1):
            cell = ws2.cell(row=row_num, column=col_idx, value=val)
            cell.font = font_regular
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center" if col_idx in [1, 2, 4, 5] else ("left" if col_idx == 3 else "right"), vertical="center")
            if is_zebra:
                cell.fill = zebra_fill

        row_num += 1

    # Auto-adjust column widths for all sheets
    for sheet in [ws1, ws2]:
        for col in sheet.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                # ignore merged title cell length
                if cell.row in [1, 2] and col_letter in ['A', 'B', 'C']:
                    continue
                if cell.value:
                    val_str = str(cell.value)
                    max_len = max(max_len, len(val_str))
            sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # Save to BytesIO buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer

