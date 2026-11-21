"""Billing logic for customer scooter usage."""

from datetime import datetime, timedelta


class BillingService:
    def current_time(self):
        return datetime.utcnow()

    def calculate_cost(self, start_time, end_time, cost_per_minute):
        duration_seconds = (end_time - start_time).total_seconds()
        duration_minutes = max(1, int((duration_seconds + 59) // 60))
        return {
            "start_time": start_time,
            "end_time": end_time,
            "duration_minutes": duration_minutes,
            "total_cost": round(duration_minutes * cost_per_minute, 2),
        }

    def calculate_usage_limit(self, balance, cost_per_minute, unlock_time):
        max_usage_minutes = int(float(balance) // float(cost_per_minute))
        auto_lock_at = unlock_time + timedelta(minutes=max_usage_minutes)
        return {
            "unlock_time": unlock_time,
            "max_usage_minutes": max_usage_minutes,
            "auto_lock_at": auto_lock_at,
        }

    def apply_balance_cap(self, total_cost, balance, auto_lock_applied=False):
        numeric_total = float(total_cost)
        numeric_balance = float(balance)
        charged_amount = round(min(numeric_total, numeric_balance), 2)
        unpaid_amount = round(max(numeric_total - numeric_balance, 0), 2)

        if unpaid_amount > 0:
            payment_status = "Auto locked - partially charged" if auto_lock_applied else "Partially charged"
        else:
            payment_status = "Auto locked - paid" if auto_lock_applied else "Paid"

        return {
            "charged_amount": charged_amount,
            "unpaid_amount": unpaid_amount,
            "payment_status": payment_status,
        }
