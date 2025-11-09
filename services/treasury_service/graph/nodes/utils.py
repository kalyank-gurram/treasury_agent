"""Common utilities for Treasury Agent graph nodes."""

from ...tools.mock_bank_api import MockBankAPI

# Shared API instance to avoid recreating connections
api = MockBankAPI()