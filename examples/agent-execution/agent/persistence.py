"""SQLite customer transactions with action-keyed, atomic domain receipts."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Iterator

from .domain import Account, Customer, InMemoryCustomerStore


class SQLiteCustomerStore(InMemoryCustomerStore):
    """Local durable domain adapter; receipt and account update share one transaction."""

    def __init__(self, db_path: str) -> None:
        super().__init__()
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS customers (id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS accounts (id TEXT PRIMARY KEY, payload TEXT NOT NULL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS domain_actions (id TEXT PRIMARY KEY, operation TEXT NOT NULL)"
            )
            for key, customer in self._customers.items():
                conn.execute(
                    "INSERT OR IGNORE INTO customers VALUES (?, ?)",
                    (key, json.dumps(asdict(customer))),
                )
                conn.execute(
                    "INSERT OR IGNORE INTO accounts VALUES (?, ?)",
                    (key, json.dumps(asdict(self._accounts[key]))),
                )

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, timeout=10)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def get_customer(self, customer_id: str) -> Customer | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT payload FROM customers WHERE id=?", (customer_id,)
            ).fetchone()
            return Customer(**json.loads(row[0])) if row else None

    def get_account(self, customer_id: str) -> Account | None:
        with self._connection() as conn:
            row = conn.execute("SELECT payload FROM accounts WHERE id=?", (customer_id,)).fetchone()
            return Account(**json.loads(row[0])) if row else None

    def set_customer_status(self, customer_id: str, status: str) -> None:
        customer = self.get_customer(customer_id)
        if not customer or status not in {"active", "frozen"}:
            raise ValueError("Unknown customer or status")
        customer.status = status
        with self._connection() as conn:
            conn.execute(
                "UPDATE customers SET payload=? WHERE id=?",
                (json.dumps(asdict(customer)), customer_id),
            )

    def action_status(self, action_id: str) -> str:
        with self._connection() as conn:
            row = conn.execute("SELECT 1 FROM domain_actions WHERE id=?", (action_id,)).fetchone()
            return "executed" if row else "not_executed"

    def _mutate(
        self, customer_id: str, action_id: str, kind: str, value: str, amount: int = 0
    ) -> bool:
        if not action_id:
            raise ValueError("Durable mutations require action_id")
        operation = json.dumps([customer_id, kind, value, amount], separators=(",", ":"))
        with self._connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            prior = conn.execute(
                "SELECT operation FROM domain_actions WHERE id=?", (action_id,)
            ).fetchone()
            if prior:
                if prior[0] != operation:
                    raise ValueError("Action ID reused for a different operation")
                return True
            row = conn.execute("SELECT payload FROM accounts WHERE id=?", (customer_id,)).fetchone()
            if not row:
                return False
            account = Account(**json.loads(row[0]))
            if kind == "credit":
                if amount <= 0:
                    raise ValueError("Credit amount must be positive")
                account.balance_cents += amount
                account.credits_applied_cents += amount
                account.activity_log.append(
                    f"Credit applied: +${amount / 100:.2f} (Reason: {value})"
                )
            else:
                if not value.strip():
                    raise ValueError("Note cannot be empty")
                account.notes.append(value.strip())
                account.activity_log.append(f"Note added: {value.strip()}")
            conn.execute(
                "UPDATE accounts SET payload=? WHERE id=?",
                (json.dumps(asdict(account)), customer_id),
            )
            conn.execute("INSERT INTO domain_actions VALUES (?, ?)", (action_id, operation))
            return True

    def apply_credit(
        self, customer_id: str, amount_cents: int, reason: str, action_id: str = ""
    ) -> bool:
        return self._mutate(customer_id, action_id, "credit", reason, amount_cents)

    def add_note(self, customer_id: str, note: str, action_id: str = "") -> bool:
        return self._mutate(customer_id, action_id, "note", note)
