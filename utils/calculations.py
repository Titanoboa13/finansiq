import numpy as np
from datetime import datetime

# --- ENFLASYON DÜZELTMELİ HEDEF HESAPLAMA ---

INFLATION_RATES = {
    "konut": 0.45,
    "araç": 0.40,
    "eğitim": 0.50,
    "emeklilik": 0.35,
    "seyahat": 0.30,
    "diğer": 0.35,
}

def get_inflation_rate_for_goal(goal_type: str) -> float:
    goal_lower = goal_type.lower()
    for key in INFLATION_RATES:
        if key in goal_lower:
            return INFLATION_RATES[key]
    return INFLATION_RATES["diğer"]

def calculate_real_goal_amount(current_amount: float, goal_type: str, years: int) -> dict:
    rate = get_inflation_rate_for_goal(goal_type)
    future_amount = current_amount * ((1 + rate) ** years)
    return {
        "current_amount": current_amount,
        "future_amount": round(future_amount, 2),
        "inflation_rate": rate,
        "years": years,
        "goal_type": goal_type,
        "multiplier": round(future_amount / current_amount, 2)
    }

# --- PORTFÖy DAĞILIMI ---

PORTFOLIO_TEMPLATES = {
    "Muhafazakâr": {
        "Altın": 0.30,
        "Dolar/Euro": 0.25,
        "Devlet Tahvili": 0.25,
        "Mevduat": 0.15,
        "BIST Hisseleri": 0.05,
    },
    "Dengeli": {
        "Altın": 0.25,
        "Dolar/Euro": 0.20,
        "BIST Hisseleri": 0.25,
        "Devlet Tahvili": 0.15,
        "Mevduat": 0.15,
    },
    "Agresif": {
        "BIST Hisseleri": 0.40,
        "Dolar/Euro": 0.20,
        "Altın": 0.20,
        "Devlet Tahvili": 0.10,
        "Mevduat": 0.10,
    },
}

EXPECTED_RETURNS = {
    "Altın": 0.35,
    "Dolar/Euro": 0.25,
    "BIST Hisseleri": 0.45,
    "Devlet Tahvili": 0.40,
    "Mevduat": 0.38,
}

def get_portfolio_for_profile(risk_profile: str) -> dict:
    return PORTFOLIO_TEMPLATES.get(risk_profile, PORTFOLIO_TEMPLATES["Dengeli"])

def calculate_portfolio_return(portfolio: dict) -> float:
    total_return = 0
    for asset, weight in portfolio.items():
        expected = EXPECTED_RETURNS.get(asset, 0.30)
        total_return += weight * expected
    return round(total_return, 4)

# --- PROJEKSİYON HESAPLAMA ---

def calculate_projection(
    initial_savings: float,
    monthly_contribution: float,
    annual_return: float,
    years: int
) -> dict:
    monthly_return = annual_return / 12
    projection_by_year = []
    current_value = initial_savings

    for year in range(1, years + 1):
        for month in range(12):
            current_value = current_value * (1 + monthly_return) + monthly_contribution
        projection_by_year.append({
            "year": datetime.now().year + year,
            "value": round(current_value, 2)
        })

    return {
        "final_value": round(current_value, 2),
        "projection_by_year": projection_by_year,
        "annual_return": annual_return,
        "total_contributed": round(monthly_contribution * 12 * years, 2)
    }

# --- HEDEFE ULAŞMA OLASILIĞI ---

def calculate_goal_probability(
    projected_value: float,
    real_goal_amount: float,
    annual_return: float,
    years: int
) -> dict:
    if projected_value >= real_goal_amount:
        base_prob = min(95, 70 + (projected_value / real_goal_amount - 1) * 50)
    else:
        ratio = projected_value / real_goal_amount
        base_prob = max(5, ratio * 70)

    volatility_penalty = {"BIST": 5, "Altın": 3, "Döviz": 2}.get("Altın", 2)
    final_prob = max(5, min(95, base_prob - volatility_penalty))

    shortage = max(0, real_goal_amount - projected_value)
    monthly_extra_needed = 0
    if shortage > 0 and years > 0:
        monthly_rate = annual_return / 12
        months = years * 12
        if monthly_rate > 0:
            monthly_extra_needed = shortage / (((1 + monthly_rate) ** months - 1) / monthly_rate)
        else:
            monthly_extra_needed = shortage / months

    return {
        "probability": round(final_prob, 1),
        "projected_value": round(projected_value, 2),
        "real_goal_amount": round(real_goal_amount, 2),
        "shortage": round(shortage, 2),
        "monthly_extra_needed": round(monthly_extra_needed, 2),
        "on_track": projected_value >= real_goal_amount
    }

# --- SENARYO ANALİZİ ---

def apply_scenario(
    base_portfolio: dict,
    scenario_type: str,
    scenario_value: float,
    initial_savings: float,
    years: int
) -> dict:
    modified_returns = EXPECTED_RETURNS.copy()

    if scenario_type == "usd_increase":
        modified_returns["Dolar/Euro"] = modified_returns["Dolar/Euro"] + scenario_value / 100
    elif scenario_type == "bist_crash":
        modified_returns["BIST Hisseleri"] = modified_returns["BIST Hisseleri"] - scenario_value / 100
    elif scenario_type == "inflation_drop":
        for key in modified_returns:
            modified_returns[key] = max(0.05, modified_returns[key] - scenario_value / 200)
    elif scenario_type == "extra_monthly":
        pass
    elif scenario_type == "gold_increase":
        modified_returns["Altın"] = modified_returns["Altın"] + scenario_value / 100

    scenario_return = sum(
        base_portfolio.get(asset, 0) * modified_returns.get(asset, 0.30)
        for asset in base_portfolio
    )

    projection = calculate_projection(
        initial_savings=initial_savings,
        monthly_contribution=scenario_value if scenario_type == "extra_monthly" else 0,
        annual_return=scenario_return,
        years=years
    )

    return {
        "scenario_type": scenario_type,
        "scenario_value": scenario_value,
        "modified_annual_return": round(scenario_return, 4),
        "final_value": projection["final_value"],
        "projection_by_year": projection["projection_by_year"]
    }

# --- HARCAMA ANALİZİ ---

EXPENSE_THRESHOLDS = {
    "Market ve Gıda": 0.25,
    "Kira ve Konut": 0.35,
    "Faturalar ve Abonelikler": 0.10,
    "Ulaşım": 0.10,
    "Eğlence": 0.10,
    "Sağlık": 0.08,
    "Eğitim": 0.10,
    "Diğer": 0.10,
}

def analyze_expenses(expenses: list, monthly_income: float) -> dict:
    category_totals = {}
    total_spent = 0

    for exp in expenses:
        cat = exp.get("category", "Diğer")
        amount = exp.get("amount", 0)
        category_totals[cat] = category_totals.get(cat, 0) + amount
        total_spent += amount

    warnings = []
    savings_potential = 0

    for cat, total in category_totals.items():
        threshold = EXPENSE_THRESHOLDS.get(cat, 0.10)
        if monthly_income > 0:
            ratio = total / monthly_income
            if ratio > threshold:
                excess = total - (threshold * monthly_income)
                warnings.append({
                    "category": cat,
                    "spent": round(total, 2),
                    "recommended_max": round(threshold * monthly_income, 2),
                    "excess": round(excess, 2),
                    "ratio_percent": round(ratio * 100, 1)
                })
                savings_potential += excess

    return {
        "category_totals": {k: round(v, 2) for k, v in category_totals.items()},
        "total_spent": round(total_spent, 2),
        "savings_rate": round((monthly_income - total_spent) / monthly_income * 100, 1) if monthly_income > 0 else 0,
        "warnings": warnings,
        "annual_savings_potential": round(savings_potential * 12, 2),
        "monthly_savings_potential": round(savings_potential, 2)
    }

def format_currency(amount: float) -> str:
    return f"{amount:,.0f} ₺".replace(",", ".")