# Copyright: Ankitects Pty Ltd and contributors
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

from anki import manifold_pb2
from anki.consts import CARD_TYPE_REV, QUEUE_TYPE_REV
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

    items = col._backend.build_session_queue(
        manifold_pb2.SessionQueueRequest(interleave=True)
    )

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
    again = col._backend.build_session_queue(
        manifold_pb2.SessionQueueRequest(interleave=True)
    )
    assert [item.card_id for item in again] == [item.card_id for item in items]


def _make_due_review(col, card_id):
    """Turns a manifold skill card into a review card due now, mirroring the
    Rust test helper. No FSRS memory state, so the engine treats it as fully at
    risk (weakness 1.0) — enough to order it by points-at-stake."""
    card = col.get_card(card_id)
    card.type = CARD_TYPE_REV
    card.queue = QUEUE_TYPE_REV
    card.due = col.sched.today - 1
    card.flush()


def test_session_queue_interleave_toggle():
    # The WS5 study-feature flag crosses the RPC boundary and actually reorders
    # the queue. elementary_algebra (weight 3) outranks trigonometry (weight 2),
    # so it leads; with two due cards it is the topic interleaving must spread.
    col = getEmptyCol()

    card_ids = {}
    for topic, weight_skills in {
        "elementary_algebra": ["ea1", "ea2"],
        "trigonometry": ["tr1"],
    }.items():
        for skill in weight_skills:
            note = col.newNote()
            note["Front"] = f"{topic} {skill}"
            note.tags = [
                f"mf::topic::{topic}",
                f"mf::skill::{skill}",
                "mf::tier::relearn",
            ]
            col.addNote(note)
            card_ids[skill] = note.cards()[0].id

    # All three are due (due cards are served regardless of lock), so both modes
    # draw from the identical set and differ only in order.
    for card_id in card_ids.values():
        _make_due_review(col, card_id)

    interleaved = col._backend.build_session_queue(
        manifold_pb2.SessionQueueRequest(interleave=True)
    )
    blocked = col._backend.build_session_queue(
        manifold_pb2.SessionQueueRequest(interleave=False)
    )

    # Same cards either way — the toggle only reorders, never drops or invents.
    assert {item.card_id for item in interleaved} == set(card_ids.values())
    assert {item.card_id for item in blocked} == set(card_ids.values())

    # Interleaving ON spreads the two elementary_algebra cards apart; OFF serves
    # them back-to-back (blocked), one topic drained before the next.
    assert [item.topic_id for item in interleaved] == [
        "elementary_algebra",
        "trigonometry",
        "elementary_algebra",
    ]
    assert [item.topic_id for item in blocked] == [
        "elementary_algebra",
        "elementary_algebra",
        "trigonometry",
    ]
