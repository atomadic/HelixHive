from agent import Agent

def test_agent_creation():
    a = Agent(role="test", prompt="hello")
    assert a.role == "test"
    assert a.hd_vec is not None
    assert a.e8_vec.shape == (8,)
    assert a.leech_vec.shape == (24,)

def test_agent_mutation():
    a = Agent(role="test", prompt="hello")
    old_traits = a.traits.copy()
    a.mutate(0.1)
    assert a.traits != old_traits  # likely changed
