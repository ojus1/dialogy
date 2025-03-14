"""
Slot Filling
============

While we describe :ref:`slots <Slot>` in the linked doc. The slot filling is part of an :ref:`intent's<Intent>`
role. This plugin orchestrates the execution of slot filling via methods available on intents.

#. We eagerly apply slot placeholders using the :ref:`apply<ApplySlot>` method. 
#. Once entities are found, we check if the slots can fill them using the :ref:`fill<FillSlot>` method.
#. If no slots were filled, we remove the placeholders using :ref:`cleanup<CleanupSlot>` method.
"""
from typing import List, Union, Set

from dialogy.base import Guard, Input, Output, Plugin
from dialogy.types import BaseEntity
from dialogy.types.intent import Intent
from dialogy.types.slots import Rule


class RuleBasedSlotFillerPlugin(Plugin):
    """
    A utility :ref:`plugin <AbstractPlugin>` for
    `slot filling <https://nlpprogress.com/english/intent_detection_slot_filling.html>`._
    An :ref:`Intent <intent>` may have a few slots that need to be filled.

    This plugin can assist filling pertaining to certain intent:entity:slot-name association rules.

    :ref:`Schema for rules<ApplySlot>`

    Let's run through a practical example. We will create a workflow and preset the output to have expected intent and
    entities.

    .. _RuleBasedSlotFillerPlugin:

    :param rules: A mapping that defines relationship between an intent, its slots and the entities that fill them.
    :type rules: Rule
    :param fill_multiple: More than one item be allowed to fill a single slot.
    :type fill_multiple: bool
    :param access: Signature for workflow access is :code:`access(workflow) -> (Intent, List[BaseEntity])`
    :type access: Optional[PluginFn]
    :param mutate: Not needed, pass :code:`None`.
    :type mutate: Optional[PluginFn]

    Irrespective of the entities that are found, only the listed type in the slot shall be present in `values`.
    """

    def __init__(
        self,
        rules: Rule,
        dest: Union[str, None] = None,
        guards: Union[List[Guard], None] = None,
        replace_output: bool = True,
        fill_multiple: bool = True,
        sort_by_score: bool = True,
        debug: bool = False,
    ) -> None:
        """
        constructor
        """
        # rules
        #
        # A `Dict` where each key is an intent name, and each value is another `Dict`,
        # in which, each key is an entity and value contains the `slot_name` and `entity_type.`
        #
        # example:
        # ```
        # rules = {"intent": {"slot_name": "entity_type"}}
        # ```
        super().__init__(
            dest=dest, guards=guards, debug=debug, replace_output=replace_output
        )
        self.rules: Rule = rules or {}

        # fill_multiple
        # A boolean value that commands the slot filler to add multiple values of the
        # same entity type within a slot.
        self.fill_multiple = fill_multiple

        # sort_by_score
        # Flag which enables to sort the slots in descending order of score, by default set to True,
        # if required, can be set to False which would then enable sorting by `alternative_index`.
        self.sort_by_score = sort_by_score

    def fill(
        self,
        intents: List[Intent],
        entities: List[BaseEntity],
        expected_slots: Union[Set[str], None] = None,
    ) -> List[Intent]:
        if not intents:
            return intents

        intent, *rest = intents

        intent.apply(self.rules)
        if self.sort_by_score:
            entities = sorted(
                entities, key=lambda parse: parse.score or 0, reverse=True
            )
        else:
            entities = sorted(entities, key=lambda parse: parse.alternative_index or 0)
        for entity in entities:
            intent.fill_slot(
                entity, fill_multiple=self.fill_multiple, expected_slots=expected_slots
            )
        intent.cleanup()
        return [intent, *rest]

    def utility(self, input_: Input, output: Output) -> List[Intent]:
        return self.fill(output.intents, output.entities, set(input_.expected_slots))
