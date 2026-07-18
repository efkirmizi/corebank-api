"""Repository layer: every hand-written SQL statement lives here.

Repositories receive an open connection (from the unit of work) and run
parameterized SQL against it. They never open connections, never commit, and
never import Flask. This is the only package in the app that contains SQL.
"""
