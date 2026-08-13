import pytest

from smallcoder.agent.schemas import (
    ActionParseError,
    EditFileArgs,
    ReadFileArgs,
    extract_json_object,
    parse_action,
)


def test_parse_valid_action():
    action, args = parse_action(
        '{"thought_summary": "look at auth", "action_type": "read_file",'
        ' "arguments": {"path": "src/auth.py", "start_line": 1, "end_line": 10}}'
    )
    assert action.action_type == "read_file"
    assert isinstance(args, ReadFileArgs)
    assert args.end_line == 10


def test_parse_tolerates_code_fences_and_prose():
    text = 'Sure! Here is my action:\n```json\n{"action_type": "finish", "arguments": {}}\n```'
    action, _ = parse_action(text)
    assert action.action_type == "finish"


def test_parse_edit_file_arguments():
    action, args = parse_action(
        '{"action_type": "edit_file", "arguments":'
        ' {"path": "a.py", "old_text": "x = 1", "new_text": "x = 2"}}'
    )
    assert isinstance(args, EditFileArgs)
    assert args.new_text == "x = 2"


def test_parse_rejects_unknown_action():
    with pytest.raises(ActionParseError, match="action_type"):
        parse_action('{"action_type": "delete_repo", "arguments": {}}')


def test_parse_rejects_missing_arguments():
    with pytest.raises(ActionParseError, match="read_file"):
        parse_action('{"action_type": "read_file", "arguments": {}}')


def test_parse_rejects_non_json():
    with pytest.raises(ActionParseError):
        parse_action("I think we should read the auth file first.")


def test_parse_rejects_unbalanced_json():
    with pytest.raises(ActionParseError):
        parse_action('{"action_type": "finish", "arguments": {')


def test_extract_json_ignores_braces_in_strings():
    raw = '{"action_type": "finish", "arguments": {"summary": "fixed {brace} case"}}'
    assert extract_json_object("noise " + raw + " trailing") == raw
