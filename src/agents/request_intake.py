"""Request intake agent for parsing user messages and extracting entities."""

import json
import logging

from src.utils import RequestInfo, SOCWorkflowState
from src.utils.agent_loop import format_history
from src.utils.config import get_settings
from src.utils.llm import create_llm

logger = logging.getLogger(__name__)


def extract_json_from_response(response_content) -> str:
    """Extract JSON string from LLM response content.

    Handles both string and list response formats from various LLM APIs.

    Args:
        response_content: Response content from LLM (str or list)

    Returns:
        JSON string, stripped and ready for parsing

    Raises:
        ValueError: If content is empty or cannot be converted to string
    """
    # Handle list of content blocks (Gemini sometimes returns this)
    if isinstance(response_content, list):
        content = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in response_content
        )
    else:
        content = response_content

    # Ensure content is a string
    if not isinstance(content, str):
        content = str(content)

    # Strip whitespace
    content = content.strip()
    if not content:
        raise ValueError("Empty response from LLM")

    return content


EXTRACTION_PROMPT = """You are a security operations center (SOC) assistant. Your task is to analyze an analyst's natural language request and extract structured information.

You will receive a user message from a security analyst and should:
1. Identify the request_type(s) - what security workflow(s) are being requested
2. Extract relevant entities (username, IP address, device ID, alert ID, incident ID, severity, time range, etc.)
3. Identify any missing required fields based on the request type
4. Provide a confidence score (0.0-1.0) for your extraction

Valid request_type values:
- alert_search: Search and analyze security alerts
- identity_check: Check user login history, activity, or account status
- endpoint_check: Review endpoint/device status and health
- incident_create: Create a new security incident
- incident_escalate: Escalate an existing incident
- reporting: Generate security reports
- ip_investigation: Investigate a suspicious IP address
- unknown: Could not determine the intent

For multi-action requests where the analyst asks for 2+ things, include multiple request_types.

CARRYING CONTEXT BETWEEN TURNS
The analyst is continuing an ongoing conversation. If the current request leaves out an
entity that was already established earlier - a username, device ID, incident ID, alert
ID - carry that value forward into entities, and do NOT list it in missing_fields.
For example, after "activity of jsmith@company.com", a follow-up of "reset password"
still refers to jsmith@company.com.
Only carry forward a value the analyst actually supplied earlier; never invent one. If
the current message names its own entity, that one wins.

CONVERSATION SO FAR (oldest first):
{conversation}

IMPORTANT: Return ONLY valid JSON on a single line. Do not add any text before or after the JSON.
Return this exact structure:
{{"request_type": ["type1"], "entities": {{"key": "value"}}, "missing_fields": [], "confidence": 0.9}}

Current request: {user_message}
"""

def extract_request_info(
    user_message: str,
    conversation_history: list[dict] | None = None
) -> RequestInfo:
    """Parse user message and extract structured RequestInfo.

    Args:
        user_message: The analyst's natural language request
        conversation_history: Prior messages, used to resolve follow-up requests that
            omit an entity named in an earlier turn (optional)

    Returns:
        RequestInfo dict with request_type, entities, missing_fields, confidence

    Raises:
        ValueError: If GOOGLE_API_KEY is not configured in settings
    """
    if not user_message or not user_message.strip():
        return {
            "request_type": ["unknown"],
            "entities": {},
            "missing_fields": [],
            "confidence": 0.1,
        }

    settings = get_settings()

    try:
        llm = create_llm(settings)
        prompt = EXTRACTION_PROMPT.format(
            user_message=user_message,
            conversation=format_history(conversation_history),
        )
        response = llm.invoke(prompt)

        content = extract_json_from_response(response.content)
        extracted = json.loads(content)

        confidence = extracted.get("confidence", 1.0)
        try:
            confidence = float(confidence)
        except (ValueError, TypeError):
            confidence = 1.0
        confidence = min(1.0, max(0.0, confidence))

        request_info: RequestInfo = {
            "request_type": extracted.get("request_type", ["unknown"]),
            "entities": extracted.get("entities", {}),
            "missing_fields": extracted.get("missing_fields", []),
            "confidence": confidence,
        }

        if not isinstance(request_info["request_type"], list):
            request_info["request_type"] = [str(request_info["request_type"])]

        if not isinstance(request_info["entities"], dict):
            request_info["entities"] = {}

        if not isinstance(request_info["missing_fields"], list):
            request_info["missing_fields"] = []

        return request_info

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in request extraction: {e}", exc_info=True)
        return {
            "request_type": ["unknown"],
            "entities": {},
            "missing_fields": [],
            "confidence": 0.3,
        }
    except Exception as e:
        logger.error(f"Unexpected error in request extraction: {e}", exc_info=True)
        return {
            "request_type": ["unknown"],
            "entities": {},
            "missing_fields": [],
            "confidence": 0.0,
        }


def request_intake_agent_node(state: SOCWorkflowState) -> dict:
    """Parse user message and extract request information.

    Calls extract_request_info() and updates conversation history with extraction metadata.
    Updates completed_actions to track this agent's execution.

    Args:
        state: Current SOCWorkflowState

    Returns:
        Updated dict with request_info, conversation_history, completed_actions
    """
    user_message = state.get("user_message", "")
    conversation_history = state.get("conversation_history") or []
    completed_actions = state.get("completed_actions") or []

    request_info = extract_request_info(user_message, conversation_history)

    new_history = conversation_history + [
        {
            "role": "system",
            "content": f"Extracted request types: {request_info['request_type']}, "
                      f"entities: {request_info['entities']}, "
                      f"confidence: {request_info['confidence']}"
        }
    ]
    new_completed_actions = completed_actions + ["request_intake"]

    return {
        "request_info": request_info,
        "conversation_history": new_history,
        "completed_actions": new_completed_actions,
    }
