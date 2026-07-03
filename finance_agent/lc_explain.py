from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda


@dataclass(frozen=True)
class ExplainArtifacts:
    negotiation_email: str
    questions_checklist: str


def _load_text(path: Path) -> str:
    """Load text content from a file.
    
    Args:
        path: Path to the file
        
    Returns:
        File content as string
    """
    return path.read_text(encoding="utf-8", errors="ignore")


def build_explain_chain(llm) -> tuple[object, object]:
    """Build LangChain chains for generating negotiation email and checklist.
    
    Returns two independent chains:
      - negotiation email generator
      - checklist generator
    
    Args:
        llm: LangChain language model instance
        
    Returns:
        Tuple of (email_chain, checklist_chain)
    """
    email_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a finance operations assistant. Be precise, practical, and concise. "
                "Do not invent facts. Only use the provided report content.",
            ),
            (
                "user",
                "Given this Fee Forensics report, draft an email to a bank "
                "relationship manager requesting a fee review.\n\n"
                "Constraints:\n"
                "- Keep it under 220 words\n"
                "- Use bullet points for key evidence\n"
                "- Ask for specific next steps\n"
                "- Professional tone\n\n"
                "REPORT:\n{report}\n",
            ),
        ]
    )

    checklist_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a finance operations assistant. Be precise, practical, and concise. "
                "Do not invent facts. Only use the provided report content.",
            ),
            (
                "user",
                "From this Fee Forensics report, create a checklist of questions "
                "to ask the bank.\n\n"
                "Constraints:\n"
                "- 10-14 bullets max\n"
                "- Group into 3 sections with headings\n"
                "- Questions must be directly actionable\n\n"
                "REPORT:\n{report}\n",
            ),
        ]
    )

    to_str = StrOutputParser()
    email_chain = email_prompt | llm | to_str
    checklist_chain = checklist_prompt | llm | to_str
    return email_chain, checklist_chain


def explain_from_report_markdown(report_path: str | Path, *, llm) -> ExplainArtifacts:
    """Generate negotiation email and questions checklist from a report.
    
    Args:
        report_path: Path to the Markdown report file
        llm: LangChain language model instance
        
    Returns:
        ExplainArtifacts containing email and checklist
        
    Raises:
        ValueError: If report is empty
    """
    p = Path(report_path)
    report_md = _load_text(p)

    # Keep a tiny bit of structure: ensure it's not empty, trim extremely large files.
    def sanitize(x: str) -> str:
        x = x.strip()
        if not x:
            raise ValueError("Report is empty")
        return x[:40_000]

    sanitizer = RunnableLambda(sanitize)
    email_chain, checklist_chain = build_explain_chain(llm)

    report_input = {"report": sanitizer.invoke(report_md)}
    negotiation_email = email_chain.invoke(report_input)
    questions_checklist = checklist_chain.invoke(report_input)

    return ExplainArtifacts(
        negotiation_email=negotiation_email, questions_checklist=questions_checklist
    )
