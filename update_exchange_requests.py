# create a script update_exchange_requests.py

from app import create_app, db
from app.models import ExchangeRequest
from datetime import datetime, timezone

app = create_app()
with app.app_context():
    exchanges = ExchangeRequest.query.filter(ExchangeRequest.updated_at == None).all()
    for exchange in exchanges:
        # Set updated_at to the time the exchange was accepted or current time
        exchange.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    print(f"Updated {len(exchanges)} exchange records.")
