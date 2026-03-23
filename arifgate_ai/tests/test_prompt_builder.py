import pytest
from app.schemas import Role
from app.services.prompt_builder import get_system_prompt


@pytest.mark.parametrize("role", [
    Role.student,
    Role.instructor,
    Role.freelancer,
    Role.client,
    Role.admin,
])
def test_get_system_prompt_returns_non_empty_string(role):
    """Each valid Role enum value should return a non-empty string prompt."""
    prompt = get_system_prompt(role)
    assert isinstance(prompt, str)
    assert len(prompt) > 0


def test_get_system_prompt_invalid_role_raises_value_error():
    """An unknown/invalid role value should raise ValueError."""
    with pytest.raises(ValueError):
        get_system_prompt("unknown_role")
