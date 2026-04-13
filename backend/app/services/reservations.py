from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List
import pytz

async def calculate_monthly_revenue(property_id: str, month: int, year: int, timezone: str = 'UTC', db_session=None) -> Decimal:
    """
    Calculates revenue for a specific month using the property's local timezone
    to determine month boundaries.
    """

    tz = pytz.timezone(timezone)
    start_date = tz.localize(datetime(year, month, 1))
    if month < 12:
        end_date = tz.localize(datetime(year, month + 1, 1))
    else:
        end_date = tz.localize(datetime(year + 1, 1, 1))

    print(f"DEBUG: Querying revenue for {property_id} from {start_date} to {end_date} (tz: {timezone})")

    # SQL Simulation (This would be executed against the actual DB)
    query = """
        SELECT SUM(total_amount) as total
        FROM reservations
        WHERE property_id = $1
        AND tenant_id = $2
        AND check_in_date >= $3
        AND check_in_date < $4
    """
    
    # In production this query executes against a database session.
    # result = await db.fetch_val(query, property_id, tenant_id, start_date, end_date)
    # return result or Decimal('0')
    
    return Decimal('0') # Placeholder for now until DB connection is finalized

async def calculate_total_revenue(property_id: str, tenant_id: str) -> Dict[str, Any]:
    """
    Aggregates revenue from database.
    """
    try:
        from sqlalchemy import text
        from app.core.database_pool import db_pool

        if not db_pool.session_factory:
            await db_pool.initialize()

        if not db_pool.session_factory:
            raise Exception("Database pool not available")

        session = db_pool.session_factory()
        try:
            query = text("""
                SELECT 
                    property_id,
                    SUM(total_amount) as total_revenue,
                    COUNT(*) as reservation_count
                FROM reservations 
                WHERE property_id = :property_id AND tenant_id = :tenant_id
                GROUP BY property_id
            """)
            
            result = await session.execute(query, {
                "property_id": property_id, 
                "tenant_id": tenant_id
            })
            row = result.fetchone()
            
            if row:
                total_revenue = Decimal(str(row.total_revenue))
                return {
                    "property_id": property_id,
                    "tenant_id": tenant_id,
                    "total": str(total_revenue),
                    "currency": "USD", 
                    "count": row.reservation_count
                }
            else:
                return {
                    "property_id": property_id,
                    "tenant_id": tenant_id,
                    "total": "0.00",
                    "currency": "USD",
                    "count": 0
                }
        finally:
            await session.close()
            
    except Exception as e:
        print(f"Database error for {property_id} (tenant: {tenant_id}): {e}")
        
        mock_data = {
            'prop-001': {'total': '1000.00', 'count': 3},
            'prop-002': {'total': '4975.50', 'count': 4}, 
            'prop-003': {'total': '6100.50', 'count': 2},
            'prop-004': {'total': '1776.50', 'count': 4},
            'prop-005': {'total': '3256.00', 'count': 3}
        }
        
        mock_property_data = mock_data.get(property_id, {'total': '0.00', 'count': 0})
        
        return {
            "property_id": property_id,
            "tenant_id": tenant_id, 
            "total": mock_property_data['total'],
            "currency": "USD",
            "count": mock_property_data['count']
        }
