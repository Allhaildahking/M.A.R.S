from types import SimpleNamespace

from mars.architecture import build_architecture_context


class FakePermission:
    value = "read"


def test_architecture_context_uses_runtime_provider_tools_and_permissions() -> None:
    registry = SimpleNamespace(
        list_specs=lambda: [
            SimpleNamespace(name="web_search", permission=FakePermission()),
            SimpleNamespace(name="create_task_plan", permission=FakePermission()),
        ]
    )
    mars = SimpleNamespace(
        provider=SimpleNamespace(model="gemini-test-model"),
        tools=registry,
        memory=None,
        conversations=SimpleNamespace(),
    )

    result = build_architecture_context(
        mars=mars,
        provider_name="gemini",
        api_entrypoint="api/index.py",
        allowed_permissions={FakePermission()},
    )

    assert "Provider adapter: SimpleNamespace" in result
    assert "Provider selection label: gemini" in result
    assert "Configured model identifier: gemini-test-model" in result
    assert "web_search: permission=read" in result
    assert "create_task_plan: permission=read" in result
    assert "MemoryManager attached to this running Mars instance: no" in result
    assert "Permissions granted to this request: read" in result
    assert "api/index.py" in result


def test_architecture_context_does_not_invent_model_or_tools() -> None:
    mars = SimpleNamespace(
        provider=object(),
        tools=SimpleNamespace(list_specs=lambda: []),
        memory=None,
        conversations=None,
    )

    result = build_architecture_context(
        mars=mars,
        provider_name="echo",
        api_entrypoint="api/index.py",
        allowed_permissions=set(),
    )

    assert "Configured model identifier: not exposed" in result
    assert "No tools are registered." in result
    assert "Permissions granted to this request: none" in result
    assert "MemoryManager attached to this running Mars instance: no" in result
