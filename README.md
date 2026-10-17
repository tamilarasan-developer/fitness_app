# NutriFit - Daily Nutrition & Fitness Macro Calculator

A full-featured **Django** fitness web application with a **mobile-first Pure Tailwind CSS UI** designed for tracking daily food nutrition intake levels, calculating energy expenditure (BMR & TDEE), comparing consumed vs needed nutrients, and monitoring hydration.

---

## 🌟 Key Features

1. **User Authentication & Biometric Profiling**:
   - Secure account registration and login.
   - User profile with Age, Gender, Height (cm), Weight (kg), Activity Level, and Fitness Goal (Fat Loss, Mild Loss, Maintenance, Lean Gain, Bulking).
   - Automatic scientific calculations via **Mifflin-St Jeor equation**:
     - **BMR** (Basal Metabolic Rate)
     - **TDEE** (Total Daily Energy Expenditure)
     - Target **Calories**, **Protein** (2.0g/kg), **Carbs**, **Fats**, **Fiber**, and **Water Intake**.

2. **Daily Intake Tracking & Calculation ("Needed vs Enough / Surplus / Deficit")**:
   - Compares consumed nutrients vs daily requirements in real-time.
   - Color-coded status badges:
     - 🟡 **Deficit / Needed**: e.g., `450 kcal needed`, `28g protein needed`
     - 🟢 **Optimal / Met Target**: `Target Met` or `On Track`
     - 🔴 **Surplus**: e.g., `220 kcal surplus`
   - **Smart Dietary Guidance**: AI/algorithmic advice suggesting rich protein, fiber, or hydration foods when targets are missing.

3. **Food Intake Logging**:
   - Grouped by meals: **Breakfast**, **Lunch**, **Dinner**, **Snacks**.
   - 58+ preloaded foods across grains, meat, poultry, seafood, dairy, fruits, veggies, nuts, legumes.
   - Interactive portion multiplier (0.5x, 1x, 1.5x, 2x, etc.) with **live macro calculation preview** before saving.
   - Support for **Custom Foods** creation.

4. **One-Tap Water Intake Tracker**:
   - Real-time hydration counter with quick `+250ml (1 Glass)`, `+500ml`, and `-250ml` buttons.

5. **History & Analytics**:
   - Interactive trend chart showing 14-day calorie intake against your daily target line.
   - Historical records table with status tags.

6. **Pure Tailwind CSS & Mobile-First UX**:
   - Dedicated **Mobile Bottom Navigation Bar** (Today, Food Library, Quick Add `+`, History, Profile).
   - High-contrast, clean dark fitness aesthetic.
   - Fully responsive for smartphones, tablets, and desktops.

---

## 📱 How to Access on Mobile

1. Make sure your phone and computer are on the **same Wi-Fi network**.
2. Find your computer's local IP address:
   ```bash
   # On Linux / macOS
   hostname -I
   # or
   ip route get 1.1.1.1 | awk '{print $7}'
   ```
3. Run the Django server listening on all network interfaces:
   ```bash
   .venv/bin/python manage.py runserver 0.0.0.0:8000
   ```
4. Open the browser on your mobile phone (Safari / Chrome) and go to:
   ```
   http://<YOUR_COMPUTER_IP>:8000/
   ```
   *(e.g., `http://192.168.1.15:8000/`)*
5. You can also tap **"Add to Home Screen"** in Safari / Chrome for a native app feel!

---

## 💻 Local Desktop Access

- Open your browser to: [http://localhost:8000/](http://localhost:8000/) or [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

## 🧪 Running Tests

To verify all calculations and views:
```bash
.venv/bin/python manage.py test
```

