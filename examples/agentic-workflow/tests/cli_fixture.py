"""OS process integration fixture; scripted model behavior stays in automated tests."""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import demo
from test_hitl_restart import StubAgentEngine

original_components = demo.get_components


def components(db_path: str, inquiry: str = ""):
    engine, store = original_components(db_path, inquiry, agent_engine=StubAgentEngine())
    boundary = os.environ.get("WORKFLOW_TEST_CRASH")
    if boundary == "claim":

        def claim(*args, **kwargs):
            # Process death before the atomic transaction leaves the request pending.
            os._exit(71)

        engine.store.commit_approval_transition = claim
    elif boundary == "effect":
        capability = engine.definition.steps["mutation_execution"].handler.__self__.capability
        original_execute = capability.execute

        async def execute(*args, **kwargs):
            await original_execute(*args, **kwargs)
            os._exit(71)

        capability.execute = execute
    elif boundary == "receipt":
        original_commit = engine.store.atomic_commit_mutation_and_approval

        def commit(*args, **kwargs):
            original_commit(*args, **kwargs)
            os._exit(71)

        engine.store.atomic_commit_mutation_and_approval = commit
    return engine, store


demo.get_components = components
demo.main()
