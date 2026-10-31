from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from app.models.plan import Plan
from app.repositories.base import BaseRepository


class PlanRepository(BaseRepository):
    def add(self, plan: Plan) -> Plan:
        self.db.add(plan)
        self.db.flush()
        return plan

    def get(self, plan_id: int) -> Plan | None:
        return self.db.get(Plan, plan_id)

    def list(self) -> Sequence[Plan]:
        return list(self.db.scalars(select(Plan).order_by(Plan.id)))

    def save(self, plan: Plan) -> Plan:
        self.db.flush()
        return plan
