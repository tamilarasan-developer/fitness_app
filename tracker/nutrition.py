"""
Nutrition intake calculator and status evaluator
"""

def evaluate_daily_intake(consumed, targets):
    """
    Compares consumed nutrients with targets.
    Produces metric cards, differences, completion percentages, badges, macro ratios,
    daily nutrition score (0-100), and smart recommendations.
    """
    def build_metric(val, target, unit='g'):
        val = round(val, 1)
        target = round(target, 1)
        diff = round(val - target, 1)
        pct = round((val / target * 100), 1) if target > 0 else 0

        if diff < -5:
            status = 'deficit'
            badge = f"{abs(diff)}{unit} needed"
            badge_class = 'bg-amber-500/20 text-amber-300 border-amber-500/40'
            color = 'amber'
        elif abs(diff) <= 5:
            status = 'optimal'
            badge = "Target Met"
            badge_class = 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
            color = 'emerald'
        else:
            status = 'surplus'
            badge = f"{diff}{unit} surplus"
            badge_class = 'bg-rose-500/20 text-rose-300 border-rose-500/40' if diff > 20 else 'bg-blue-500/20 text-blue-300 border-blue-500/40'
            color = 'rose' if diff > 20 else 'blue'

        return {
            'consumed': val,
            'target': target,
            'difference': diff,
            'percentage': min(pct, 120), # for UI progress bar width
            'actual_percentage': pct,
            'status': status,
            'badge': badge,
            'badge_class': badge_class,
            'color': color,
            'unit': unit,
        }

    # Caloric status
    c_cal = round(consumed.get('calories', 0))
    t_cal = round(targets.get('calories', 2000))
    cal_diff = round(c_cal - t_cal)
    cal_pct = round((c_cal / t_cal * 100), 1) if t_cal > 0 else 0

    remaining_calories = max(0, t_cal - c_cal)
    over_calories = max(0, c_cal - t_cal)

    if cal_diff < -150:
        cal_status = 'deficit'
        cal_badge = f"{abs(cal_diff)} kcal needed"
        cal_badge_class = 'bg-amber-500/20 text-amber-300 border-amber-500/40'
        cal_color = 'amber'
    elif abs(cal_diff) <= 150:
        cal_status = 'optimal'
        cal_badge = "On Target"
        cal_badge_class = 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
        cal_color = 'emerald'
    else:
        cal_status = 'surplus'
        cal_badge = f"{cal_diff} kcal surplus"
        cal_badge_class = 'bg-rose-500/20 text-rose-300 border-rose-500/40'
        cal_color = 'rose'

    calories_stat = {
        'consumed': c_cal,
        'target': t_cal,
        'remaining': remaining_calories,
        'over': over_calories,
        'difference': cal_diff,
        'percentage': min(cal_pct, 120),
        'actual_percentage': cal_pct,
        'status': cal_status,
        'badge': cal_badge,
        'badge_class': cal_badge_class,
        'color': cal_color,
        'unit': 'kcal',
    }

    protein_stat = build_metric(consumed.get('protein', 0), targets.get('protein', 140))
    carbs_stat = build_metric(consumed.get('carbs', 0), targets.get('carbs', 220))
    fat_stat = build_metric(consumed.get('fat', 0), targets.get('fat', 60))
    fiber_stat = build_metric(consumed.get('fiber', 0), targets.get('fiber', 30))

    # Water status
    c_water = round(consumed.get('water_ml', 0))
    t_water = round(targets.get('water_ml', 2500))
    water_diff = round(c_water - t_water)
    water_pct = round((c_water / t_water * 100), 1) if t_water > 0 else 0

    water_stat = {
        'consumed': c_water,
        'target': t_water,
        'difference': water_diff,
        'percentage': min(water_pct, 100),
        'actual_percentage': water_pct,
        'glasses': round(c_water / 250, 1),
        'target_glasses': round(t_water / 250, 1),
        'badge': f"{abs(water_diff)}ml to go" if water_diff < 0 else "Hydrated!",
        'badge_class': 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40' if water_diff >= 0 else 'bg-sky-500/20 text-sky-300 border-sky-500/40',
        'unit': 'ml',
    }

    # Macro Energy Percentage Ratios (Protein 4kcal/g, Carbs 4kcal/g, Fat 9kcal/g)
    total_macro_kcal = (protein_stat['consumed'] * 4) + (carbs_stat['consumed'] * 4) + (fat_stat['consumed'] * 9)
    if total_macro_kcal > 0:
        prot_ratio = round((protein_stat['consumed'] * 4 / total_macro_kcal) * 100)
        carbs_ratio = round((carbs_stat['consumed'] * 4 / total_macro_kcal) * 100)
        fat_ratio = max(0, 100 - prot_ratio - carbs_ratio)
    else:
        prot_ratio, carbs_ratio, fat_ratio = 0, 0, 0

    macro_ratios = {
        'protein': prot_ratio,
        'carbs': carbs_ratio,
        'fat': fat_ratio,
    }

    # Daily Nutrition Compliance Score (0 - 100)
    # Calorie precision (40%), Protein achievement (35%), Water intake (15%), Fiber (10%)
    cal_score = max(0, 40 * (1 - (abs(cal_diff) / max(1, t_cal))))
    prot_score = min(35, 35 * (protein_stat['consumed'] / max(1, protein_stat['target'])))
    water_score = min(15, 15 * (c_water / max(1, t_water)))
    fiber_score = min(10, 10 * (fiber_stat['consumed'] / max(1, fiber_stat['target'])))
    
    total_score = round(cal_score + prot_score + water_score + fiber_score)
    if total_score >= 88:
        score_grade = "Elite"
        score_class = "text-emerald-400 border-emerald-500/40 bg-emerald-500/10"
    elif total_score >= 70:
        score_grade = "Great"
        score_class = "text-cyan-400 border-cyan-500/40 bg-cyan-500/10"
    elif total_score >= 50:
        score_grade = "Good"
        score_class = "text-amber-400 border-amber-500/40 bg-amber-500/10"
    else:
        score_grade = "Building Up"
        score_class = "text-indigo-400 border-indigo-500/40 bg-indigo-500/10"

    nutrition_score = {
        'value': total_score,
        'grade': score_grade,
        'badge_class': score_class,
    }

    # Smart nutritional suggestions
    insights = []
    if cal_diff < -300:
        insights.append({
            'type': 'warning',
            'border': 'border-amber-500',
            'icon': 'fa-triangle-exclamation text-amber-400',
            'title': f'{abs(cal_diff)} kcal needed today',
            'msg': f"You have {remaining_calories} kcal remaining. Fuel up with nutrient-dense foods (oats, brown rice, whole eggs, nuts) to support muscle recovery and metabolism."
        })
    elif cal_diff > 300:
        insights.append({
            'type': 'danger',
            'border': 'border-rose-500',
            'icon': 'fa-circle-exclamation text-rose-400',
            'title': f'{cal_diff} kcal caloric surplus',
            'msg': f"You're currently {cal_diff} kcal above maintenance. Keep remainder meals light with leafy vegetables and lean protein."
        })
    else:
        insights.append({
            'type': 'success',
            'border': 'border-emerald-500',
            'icon': 'fa-circle-check text-emerald-400',
            'title': 'Caloric Target on Point',
            'msg': "Your energy intake is perfectly calibrated with your fitness target today!"
        })

    if protein_stat['difference'] < -20:
        insights.append({
            'type': 'warning',
            'border': 'border-amber-500',
            'icon': 'fa-drumstick-bite text-amber-400',
            'title': f"Need {abs(protein_stat['difference'])}g more protein",
            'msg': f"Add chicken breast, egg whites, Greek yogurt, paneer, tofu, or a scoop of whey protein to fulfill muscle repair."
        })
    elif protein_stat['difference'] >= 0:
        insights.append({
            'type': 'success',
            'border': 'border-emerald-500',
            'icon': 'fa-award text-emerald-400',
            'title': 'Protein Target Crushed!',
            'msg': f"You've consumed {protein_stat['consumed']}g of protein, providing ideal amino acid availability."
        })

    if fiber_stat['difference'] < -10:
        insights.append({
            'type': 'info',
            'border': 'border-indigo-500',
            'icon': 'fa-seedling text-indigo-400',
            'title': f"Fiber deficit: {abs(fiber_stat['difference'])}g needed",
            'msg': "Consider adding an apple, chia seeds, broccoli, or rolled oats for optimal glycemic index & gut health."
        })

    if water_diff < -750:
        insights.append({
            'type': 'info',
            'border': 'border-cyan-500',
            'icon': 'fa-droplet text-cyan-400',
            'title': f"Hydration: {abs(water_diff)}ml remaining",
            'msg': f"You're at {water_pct}% of your daily water intake. Drink 2-3 more glasses to keep metabolism active."
        })

    return {
        'calories': calories_stat,
        'protein': protein_stat,
        'carbs': carbs_stat,
        'fat': fat_stat,
        'fiber': fiber_stat,
        'water': water_stat,
        'macro_ratios': macro_ratios,
        'nutrition_score': nutrition_score,
        'insights': insights,
    }
