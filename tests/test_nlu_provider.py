from controller import decide_candidate
from nlu_provider import ClarificationContext, NluRequest, RuleProvider, recognize_days
from schemas import validate_nlu


def test_c06_inherits_only_the_current_question_window():
    provider = RuleProvider()
    assert (
        decide_candidate(validate_nlu(provider.predict(NluRequest(3, "有幾天")), 3))
        == 1
    )
    assert (
        decide_candidate(
            validate_nlu(provider.predict(NluRequest(3, "只限上星期有幾天")), 3)
        )
        is None
    )
    assert (
        decide_candidate(
            validate_nlu(
                provider.predict(NluRequest(3, "有幾天", question_timeframe="missing")),
                3,
            )
        )
        is None
    )


def test_c06_observed_days_are_not_a_phq8_candidate():
    context = ClarificationContext(3, "frequency_in_past_14_days")
    response = NluRequest(3, "Around five days", clarification=context)
    duration = recognize_days(response)
    assert duration.count == 5 and duration.approximate
    assert RuleProvider().predict(response)["frequency_candidate"] is None
    assert recognize_days(NluRequest(4, response.text, clarification=context)) is None
    assert recognize_days(NluRequest(3, response.text)) is None
    assert (
        recognize_days(NluRequest(3, "Around 15 days", clarification=context)) is None
    )
    assert (
        recognize_days(
            NluRequest(3, "Around five days last week", clarification=context)
        )
        is None
    )
