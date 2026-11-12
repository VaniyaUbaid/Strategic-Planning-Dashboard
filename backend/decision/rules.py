import re
from typing import Optional


_INTENTS = (
    ("cross_summary", (
        r"\binstitutional performance\b",
        r"\boverall (?:performance )?summary\b",
        r"\binstitutional summary\b",
    )),
    ("cross_weak_departments", (r"\bweak performance\b", r"\bweak across\b", r"\bmultiple modules\b")),
    ("cross_compare", (r"\bcompare\b.*\b(student|risk|financial|finance)\b", r"\bstudent risk\b.*\bfinancial\b")),
    ("cross_priorities", (r"\btop\s+(?:three|3)\s+priorit(?:y|ies)\b",)),
    ("cross_attention", (
        r"\bmost attention\b",
        r"\brequire(s)? (the )?most attention\b",
        r"\bdepartment(s)?\b.*\battention\b",
        r"\bareas?\b.*\b(?:immediate )?attention\b",
        r"\bimmediate attention\b",
    )),
    ("student_average_gpa", (r"\baverage\b.*\bgpa\b", r"\bmean\b.*\bgpa\b")),
    ("student_average_probability", (r"\baverage\b.*\b(dropout )?(risk )?probability\b", r"\baverage predicted risk\b")),
    ("student_predictors", (
        r"\bpredict(or|ors|ive|ion|ions)\b",
        r"\bfeatures?\b.*\bdropout\b",
        r"\b(?:contributing|contributory|major|main)\s+factors?\b.*\b(?:dropout|drop out|risk)\b",
        r"\bwhat\b.*\bfactors?\b.*\b(?:dropout|drop out|risk)\b",
    )),
    ("student_distribution", (r"\brisk distribution\b", r"\bdistribution\b.*\b(high|medium|low) risk\b")),
    ("student_department_risk", (r"\bdepartment(s)?\b.*\b(risk percentage|risk percent|risk rate|highest risk)\b", r"\bhighest\b.*\b(dropout|student) risk\b", r"\bhighest\b.*\brisk percentage\b")),
    ("student_high_risk_students", (
        r"\bwhich students?\b.*\b(?:high[- ]risk|at risk)\b",
        r"\blist\b.*\bhigh[- ]risk students?\b",
    )),
    ("student_high_risk", (
        r"\bhow many\b.*\bhigh[- ]risk\b",
        r"\bhigh[- ]risk students?\b",
        r"\bnumber of\b.*\bhigh[- ]risk\b",
        r"\bwhat percentage\b.*\bhigh[- ]risk\b",
        r"\bstudents?\b.*\b(?:are|classified|at)\b.*\bhigh[- ]risk\b",
        r"\bstudents?\b.*\bat high risk\b.*\b(?:dropout|dropping out)\b",
    )),
    ("finance_overrun", (r"\bexceed(ed|ing)?\b.*\bbudgets?\b", r"\boverrun(s)?\b", r"\bover budget\b")),
    ("finance_expenditure", (
        r"\btotal expenditure\b",
        r"\btotal expenses?\b",
        r"\bhow much\b.*\b(?:spent|expenditure)\b",
    )),
    ("finance_pressure", (r"\bfinancial pressure\b", r"\bfinancial stress\b", r"\bpressure\b.*\bfinancial\b")),
    ("finance_outstanding", (
        r"\boutstanding\b.*\bfees?\b",
        r"\bfees?\b.*\boutstanding\b",
        r"\boutstanding fee revenue\b",
        r"\btotal pending fees?\b",
    )),
    ("finance_collection", (r"\bcollection rate\b", r"\bfee collection\b")),
    ("finance_utilization", (r"\bbudget utilization\b", r"\bbudget utilization\b.*\bdepartments?\b", r"\bcompare\b.*\bbudget\b")),
    ("research_department_average", (
        r"\bdepartment(s)?\b.*\b(highest|most)\b.*\baverage\b.*\bpublications?\b",
        r"\bhighest\b.*\baverage\b.*\bpublications?\b",
        r"\bmost productive department\b.*\baverage\b",
        r"\baverage\b.*\bpublications?\b.*\bper faculty\b.*\bdepartment",
    )),
    ("research_total_publications", (
        r"\btotal\b.*\bfaculty publications?\b",
        r"\btotal faculty publication count\b",
        r"\bpublication count\b.*\bfaculty\b",
    )),
    ("research_trends", (r"\bpublication trends?\b", r"\btrends?\b.*\bpublications?\b", r"\bacross academic years\b")),
    ("research_top_faculty", (r"\bfaculty\b.*\b(highest|top|most)\b.*\bpublications?\b", r"\btop faculty\b")),
    ("research_average", (r"\baverage\b.*\bpublications?\b.*\bfaculty\b", r"\bpublications?\b.*\bper faculty\b")),
    ("research_faculty_count", (
        r"\bhow many\b.*\bactive faculty\b",
        r"\bnumber of\b.*\bactive faculty\b",
        r"\bactive faculty members?\b",
        r"\btotal faculty members?\b",
    )),
    ("research_department_publications", (r"\bdepartment(s)?\b.*\b(highest|most)\b.*\bpublications?\b", r"\bpublications?\b.*\bby department\b")),
    ("research_participation", (r"\bresearch participation\b", r"\bparticipation\b.*\bdepartment")),
    ("student", (r"\bstudent(s)?\b", r"\bdropout\b", r"\bgpa\b", r"\bbacklogs?\b", r"\brisk\b")),
    ("finance", (r"\bfinance\b", r"\bbudget\b", r"\bfees?\b", r"\bexpense(s)?\b", r"\brevenue\b")),
    ("research", (r"\bresearch\b", r"\bpublication(s)?\b", r"\bfaculty\b", r"\bcitation(s)?\b", r"\bgrant(s)?\b")),
)


def classify_query(query: str) -> Optional[str]:
    normalized = re.sub(r"\s+", " ", query.casefold()).strip()
    for intent, patterns in _INTENTS:
        if any(re.search(pattern, normalized) for pattern in patterns):
            return intent
    return None
