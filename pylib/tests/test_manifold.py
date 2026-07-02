# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from tests.shared import getEmptyCol


def test_topic_graph():
    col = getEmptyCol()

    # Author three distinct skills under the elementary_algebra topic. The
    # blueprint expects six skills there, so coverage should be 3/6 = 0.5.
    for skill in ["alpha", "beta", "gamma"]:
        note = col.newNote()
        note["Front"] = f"elementary_algebra/{skill}"
        note.tags = [
            "mf::topic::elementary_algebra",
            f"mf::skill::{skill}",
            "mf::tier::relearn",
        ]
        col.addNote(note)

    nodes = col._backend.get_topic_graph().nodes
    by_id = {node.id: node for node in nodes}

    # Every blueprint topic is reported, in blueprint order.
    assert nodes[0].id == "elementary_algebra"

    ea = by_id["elementary_algebra"]
    assert ea.total == 3
    assert ea.mastered == 0
    assert abs(ea.coverage - 0.5) < 1e-6
    # A root topic with skills but nothing mastered is unlocked, not in progress.
    assert ea.lock_state == "unlocked"

    # precalc_functions depends on elementary_algebra, which is not yet mastered, so
    # it stays locked.
    assert by_id["precalc_functions"].lock_state == "locked"
    assert by_id["precalc_functions"].total == 0


def test_session_queue_gates_new_cards_by_lock_state():
    col = getEmptyCol()

    # elementary_algebra is a root topic (unlocked on a fresh collection);
    # precalc_functions depends on it, so it is locked and must contribute nothing.
    for skill in ["alpha", "beta", "gamma"]:
        note = col.newNote()
        note["Front"] = f"Elementary algebra {skill}"
        note.tags = [
            "mf::topic::elementary_algebra",
            f"mf::skill::{skill}",
            "mf::tier::relearn",
        ]
        col.addNote(note)
    for skill in ["delta", "epsilon"]:
        note = col.newNote()
        note["Front"] = f"Precalc {skill}"
        note.tags = [
            "mf::topic::precalc_functions",
            f"mf::skill::{skill}",
            "mf::tier::relearn",
        ]
        col.addNote(note)

    items = col._backend.build_session_queue()

    # Only the unlocked root's skills are served; the locked dependent's are not.
    assert len(items) == 3
    assert {item.topic_id for item in items} == {"elementary_algebra"}

    # Each item carries the identity the player renders plus the card to grade.
    first = items[0]
    assert first.card_id != 0
    assert first.skill_id in {"alpha", "beta", "gamma"}
    assert first.skill_name.startswith("Elementary algebra")
    assert first.topic_title == "Elementary algebra"
    assert first.tier == "relearn"

    # The builder only reads, so asking again returns the same plan.
    again = col._backend.build_session_queue()
    assert [item.card_id for item in again] == [item.card_id for item in items]
