"""Tests for the SanityLang variable and environment system."""
import pytest
from sanity.variables import Variable, Environment, Mood, Trait
from sanity.types import san_number, san_word, san_void, san_yep


class TestVariable:
    def test_creation(self):
        v = Variable(name="x", value=san_number(42), keyword="sure", decl_line=1)
        assert v.name == "x"
        assert v.value.value == 42
        assert v.keyword == "sure"

    def test_trust_default(self):
        v = Variable(name="x", value=san_number(0), keyword="sure", decl_line=1)
        assert v.trust == 100

    def test_doubt_default(self):
        v = Variable(name="x", value=san_number(0), keyword="maybe", decl_line=1)
        assert v.doubt == 0

    def test_mood_default(self):
        v = Variable(name="x", value=san_number(0), keyword="sure", decl_line=1)
        assert v.mood == Mood.NEUTRAL

    def test_age_default(self):
        v = Variable(name="x", value=san_number(0), keyword="sure", decl_line=1)
        assert v.age == 0

    def test_scar_management(self):
        v = Variable(name="x", value=san_number(0), keyword="sure", decl_line=1)
        v.add_scar()
        assert v.scars == 1
        v.add_scar()
        v.add_scar()
        assert v.scars == 3
        assert Trait.RESILIENT in v.traits

    def test_observation(self):
        v = Variable(name="x", value=san_number(0), keyword="sure", decl_line=1)
        assert v.observed is False
        v.observed = True
        assert v.observed is True

    def test_doubt_increment(self):
        v = Variable(name="x", value=san_number(0), keyword="maybe", decl_line=1)
        v.doubt += 1
        assert v.doubt == 1

    def test_trust_loss(self):
        v = Variable(name="x", value=san_number(0), keyword="sure", decl_line=1)
        v.lose_trust(50)
        assert v.trust == 50

    def test_trust_loss_angry(self):
        v = Variable(name="x", value=san_number(0), keyword="sure", decl_line=1)
        v.lose_trust(60)  # Trust goes to 40, below 50 -> ANGRY
        assert v.trust == 40
        assert v.mood == Mood.ANGRY

    def test_trust_loss_paranoid(self):
        v = Variable(name="x", value=san_number(0), keyword="sure", decl_line=1)
        v.lose_trust(80)  # Trust goes to 20, below 30 -> PARANOID
        assert Trait.PARANOID in v.traits

    def test_trust_floor_zero(self):
        v = Variable(name="x", value=san_number(0), keyword="sure", decl_line=1)
        v.lose_trust(200)
        assert v.trust == 0

    def test_history_tracked(self):
        v = Variable(name="x", value=san_number(0), keyword="maybe", decl_line=1)
        v.history.append(san_number(1))
        v.history.append(san_number(2))
        assert len(v.history) == 2

    def test_mood_set(self):
        v = Variable(name="x", value=san_number(0), keyword="sure", decl_line=1)
        v.mood = Mood.EXCITED
        assert v.mood == Mood.EXCITED

    def test_record_access_tired(self):
        v = Variable(name="x", value=san_number(0), keyword="sure", decl_line=1)
        for i in range(200):
            v.record_access(i)
        assert Trait.TIRED in v.traits

    def test_record_access_happy_at_7(self):
        v = Variable(name="x", value=san_number(0), keyword="sure", decl_line=1)
        for i in range(7):
            v.record_access(i)
        assert v.mood == Mood.HAPPY

    def test_mood_apply_number_happy(self):
        v = Variable(name="x", value=san_number(0), keyword="sure", decl_line=1)
        v.mood = Mood.HAPPY
        assert v.apply_mood_to_number(10) == 11

    def test_mood_apply_number_sad(self):
        v = Variable(name="x", value=san_number(0), keyword="sure", decl_line=1)
        v.mood = Mood.SAD
        assert v.apply_mood_to_number(10) == 9

    def test_mood_apply_word_happy(self):
        v = Variable(name="x", value=san_word("hi"), keyword="sure", decl_line=1)
        v.mood = Mood.HAPPY
        assert v.apply_mood_to_word("hello") == "hello!"

    def test_mood_apply_word_sad(self):
        v = Variable(name="x", value=san_word("hi"), keyword="sure", decl_line=1)
        v.mood = Mood.SAD
        assert v.apply_mood_to_word("hello") == "hell"

    def test_elder_immune_to_mood(self):
        v = Variable(name="x", value=san_number(0), keyword="sure", decl_line=1)
        v.traits.add(Trait.ELDER)
        v.mood = Mood.HAPPY
        assert v.apply_mood_to_number(10) == 10

    def test_has_trait(self):
        v = Variable(name="x", value=san_number(0), keyword="sure", decl_line=1)
        assert v.has_trait(Trait.LUCKY) is False
        v.traits.add(Trait.LUCKY)
        assert v.has_trait(Trait.LUCKY) is True


class TestEnvironment:
    def test_define_and_get(self):
        env = Environment(scope_id=1)
        env.define("x", Variable(name="x", value=san_number(42), keyword="sure", decl_line=1))
        var = env.get("x")
        assert var.value.value == 42

    def test_get_undefined(self):
        env = Environment(scope_id=1)
        var = env.get("nonexistent")
        assert var is None

    def test_nested_scope_resolution(self):
        parent = Environment(scope_id=1)
        parent.define("x", Variable(name="x", value=san_number(42), keyword="sure", decl_line=1))
        child = Environment(parent=parent, scope_id=2)
        var = child.get("x")
        assert var is not None
        assert var.value.value == 42

    def test_shadow_in_child(self):
        parent = Environment(scope_id=1)
        parent.define("x", Variable(name="x", value=san_number(42), keyword="sure", decl_line=1))
        child = Environment(parent=parent, scope_id=2)
        child.define("x", Variable(name="x", value=san_number(99), keyword="maybe", decl_line=2))
        assert child.get("x").value.value == 99
        assert parent.get("x").value.value == 42

    def test_set_value_existing(self):
        env = Environment(scope_id=1)
        env.define("x", Variable(name="x", value=san_number(1), keyword="maybe", decl_line=1))
        env.set_value("x", san_number(2))
        assert env.get("x").value.value == 2

    def test_set_value_in_parent(self):
        parent = Environment(scope_id=1)
        parent.define("x", Variable(name="x", value=san_number(1), keyword="maybe", decl_line=1))
        child = Environment(parent=parent, scope_id=2)
        child.set_value("x", san_number(99))
        assert parent.get("x").value.value == 99

    def test_scope_id(self):
        env = Environment(scope_id=42)
        assert env.scope_id == 42

    def test_all_variables(self):
        env = Environment(scope_id=1)
        env.define("a", Variable(name="a", value=san_number(1), keyword="sure", decl_line=1))
        env.define("b", Variable(name="b", value=san_number(2), keyword="sure", decl_line=2))
        all_vars = env.all_variables()
        assert "a" in all_vars
        assert "b" in all_vars

    def test_has(self):
        env = Environment(scope_id=1)
        env.define("x", Variable(name="x", value=san_number(1), keyword="sure", decl_line=1))
        assert env.has("x") is True
        assert env.has("y") is False

    def test_has_local(self):
        parent = Environment(scope_id=1)
        parent.define("x", Variable(name="x", value=san_number(1), keyword="sure", decl_line=1))
        child = Environment(parent=parent, scope_id=2)
        assert child.has_local("x") is False
        assert child.has("x") is True


class TestBonds:
    def test_detect_bonds_same_type_close(self):
        env = Environment(scope_id=1)
        env.define("x", Variable(name="x", value=san_number(1), keyword="sure", decl_line=1))
        env.define("y", Variable(name="y", value=san_number(2), keyword="sure", decl_line=2))
        bonds = env.detect_bonds()
        assert len(bonds) == 1
        assert ("x", "y") in bonds

    def test_detect_bonds_different_type(self):
        env = Environment(scope_id=1)
        env.define("x", Variable(name="x", value=san_number(1), keyword="sure", decl_line=1))
        env.define("y", Variable(name="y", value=san_word("hi"), keyword="sure", decl_line=2))
        bonds = env.detect_bonds()
        assert len(bonds) == 0

    def test_detect_bonds_far_apart(self):
        env = Environment(scope_id=1)
        env.define("x", Variable(name="x", value=san_number(1), keyword="sure", decl_line=1))
        env.define("y", Variable(name="y", value=san_number(2), keyword="sure", decl_line=20))
        bonds = env.detect_bonds()
        assert len(bonds) == 0


class TestMoodEnum:
    def test_all_moods_exist(self):
        for mood_name in ["NEUTRAL", "HAPPY", "SAD", "ANGRY", "AFRAID", "EXCITED", "JEALOUS"]:
            assert hasattr(Mood, mood_name)


class TestTraitEnum:
    def test_all_traits_exist(self):
        for trait_name in ["ELDER", "RESILIENT", "TIRED", "LUCKY", "UNLUCKY",
                          "PARANOID", "POPULAR", "LONELY", "CURSED", "BLESSED", "VOLATILE"]:
            assert hasattr(Trait, trait_name)
