from mars.memory import MemoryFormation, MemoryManager, SQLiteMemoryStore


def test_memory_persists_and_can_be_recalled() -> None:
    store = SQLiteMemoryStore(":memory:")
    memory = MemoryManager(store)

    saved = memory.remember(
        "User wants MARS to be a general personal AI.",
        category="project",
    )

    results = memory.recall("general personal AI")

    assert saved.id is not None
    assert len(results) == 1
    assert results[0].content == saved.content
    assert results[0].category == "project"


def test_empty_memory_is_rejected() -> None:
    store = SQLiteMemoryStore(":memory:")

    try:
        store.add("   ")
    except ValueError as error:
        assert str(error) == "Memory content cannot be empty."
    else:
        raise AssertionError("Expected empty memory to be rejected.")


def test_recent_memories_are_newest_first() -> None:
    store = SQLiteMemoryStore(":memory:")
    memory = MemoryManager(store)

    memory.remember("first")
    memory.remember("second")

    assert [item.content for item in memory.recent()] == ["second", "first"]


def test_duplicate_memories_are_not_saved_twice() -> None:
    memory = MemoryManager(SQLiteMemoryStore(":memory:"))

    first = memory.remember("MARS is a personal AI.", category="project")
    second = memory.remember("  mars is a personal ai.  ", category="general")

    assert first.id == second.id
    assert len(memory.recent()) == 1
    assert memory.recent()[0].category == "project"


def test_memory_can_be_forgotten() -> None:
    memory = MemoryManager(SQLiteMemoryStore(":memory:"))
    saved = memory.remember("MARS should remember this.")

    forgotten = memory.forget("remember this")

    assert [item.id for item in forgotten] == [saved.id]
    assert memory.recall("remember this") == []


def test_explicit_memory_request_is_extracted() -> None:
    formation = MemoryFormation()

    candidate = formation.extract("Remember that Thesis is my future.")

    assert candidate is not None
    assert candidate.content == "Thesis is my future."
    assert candidate.category == "explicit"


def test_normal_message_is_not_extracted() -> None:
    formation = MemoryFormation()

    assert formation.extract("Let's work on the MARS memory system.") is None


def test_explicit_memory_is_saved() -> None:
    memory = MemoryManager(SQLiteMemoryStore(":memory:"))

    saved = memory.remember_if_explicit(
        "Remember that MARS should use Trade-Oracle for trading."
    )

    assert saved is not None
    assert saved.content == "MARS should use Trade-Oracle for trading."
    assert saved.category == "explicit"
