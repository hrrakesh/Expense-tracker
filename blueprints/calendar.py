from datetime import date
from flask import Blueprint, request, jsonify, current_app
import database

calendar_bp = Blueprint('calendar', __name__, url_prefix='/api/calendar')

@calendar_bp.route('/month', methods=['GET'])
def get_calendar_month():
    """Retrieve monthly calendar summary with locking and boundary rules."""
    start_year = current_app.config.get('START_YEAR', 2026)
    start_month = current_app.config.get('START_MONTH', 10)
    today = date.today()
    try:
        year = int(request.args.get('year', today.year))
        month = int(request.args.get('month', today.month))
    except ValueError:
        year, month = today.year, today.month

    # RULE: Calendar starts strictly at Oct 2026, no previous months allowed
    if year < start_year or (year == start_year and month < start_month):
        year, month = start_year, start_month

    # RULE: Cannot see future months; unlocks next month only when that month arrives
    if year > today.year or (year == today.year and month > today.month):
        year, month = today.year, today.month

    summaries = database.get_monthly_day_summaries(year, month)
    
    # Calculate month grand totals
    total_credit = sum(day['credit'] for day in summaries.values())
    total_debit = sum(day['debit'] for day in summaries.values())

    can_go_prev = not (year == start_year and month == start_month)
    can_go_next = not (year == today.year and month == today.month)

    return jsonify({
        'year': year,
        'month': month,
        'today': today.isoformat(),
        'start_year': start_year,
        'start_month': start_month,
        'can_go_prev': can_go_prev,
        'can_go_next': can_go_next,
        'summaries': summaries,
        'month_total_credit': total_credit,
        'month_total_debit': total_debit,
        'month_net': total_credit - total_debit
    })
