"""Service layer: business logic and transaction boundaries.

Services compose repository calls inside a unit of work, enforce banking rules
(ownership, sufficient funds, valid state transitions), and raise the domain
exceptions in :mod:`app.services.exceptions`. Like repositories, services never
import Flask, so they can be unit-tested with fake repositories and no app.
"""
