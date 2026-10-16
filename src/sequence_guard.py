
class SequenceGuard:
    """Track sequence numbers separately for each synthetic sender."""

    def __init__(self):
        self.last_sequence = {}

    def check(self, sender_id, sequence):
        if not isinstance(sender_id, str) or not sender_id.strip():
            return {
                "accepted": False,
                "reason": "sender_id must be a non-empty string.",
            }

        if type(sequence) is not int or sequence < 0:
            return {
                "accepted": False,
                "reason": "sequence must be a non-negative integer.",
            }

        previous = self.last_sequence.get(sender_id)

        if previous is not None and sequence <= previous:
            return {
                "accepted": False,
                "reason": (
                    f"Replay or out-of-order message: sequence {sequence} "
                    f"is not greater than the last accepted sequence {previous}."
                ),
            }

        self.last_sequence[sender_id] = sequence

        return {
            "accepted": True,
            "reason": "Sequence accepted.",
        }
