from pydantic import BaseModel

from src.utils.object_to_formatted_text import object_to_formatted_text


class TestObjectChild(BaseModel):
    c: int


class TestObject(BaseModel):
    a: int
    b: int
    c: TestObjectChild
    d: list[TestObjectChild]
    e: dict[str, TestObjectChild]


def test_primitive_types():
    assert object_to_formatted_text(123) == "123"
    assert object_to_formatted_text("hello") == "hello"
    assert object_to_formatted_text(True) == "True"
    assert object_to_formatted_text(None) == "None"


def test_empty_collections():
    assert object_to_formatted_text({}) == ""
    assert object_to_formatted_text([]) == ""


def test_simple_dict():
    obj = {"a": 1, "b": 2, "c": "hello"}
    expected = "a: 1\nb: 2\nc: hello"
    assert object_to_formatted_text(obj) == expected


def test_simple_list():
    obj = [1, 2, "hello"]
    expected = "- 1\n- 2\n- hello"
    assert object_to_formatted_text(obj) == expected


def test_nested_dict():
    obj = {"a": 1, "b": {"c": 2, "d": 3}}
    expected = "a: 1\nb:\n    c: 2\n    d: 3"
    assert object_to_formatted_text(obj) == expected


def test_nested_list():
    obj = [1, [2, 3], 4]
    expected = "- 1\n- \n  - 2\n  - 3\n- 4"
    assert object_to_formatted_text(obj) == expected


def test_complex_nested_structure():
    obj = {"a": 1, "b": [2, 3, {"c": 4}], "d": {"e": [5, 6]}}
    expected = "a: 1\nb:\n    - 2\n    - 3\n    - \n      c: 4\nd:\n    e:\n        - 5\n        - 6"
    assert object_to_formatted_text(obj) == expected


def test_pydantic_models():
    child = TestObjectChild(c=42)
    obj = TestObject(
        a=1,
        b=2,
        c=child,
        d=[TestObjectChild(c=3), TestObjectChild(c=4)],
        e={"x": TestObjectChild(c=5), "y": TestObjectChild(c=6)},
    )

    # Convert to dict first as that's how Pydantic models would typically be processed
    result = object_to_formatted_text(obj.model_dump())

    expected = (
        "a: 1\n"
        "b: 2\n"
        "c:\n"
        "    c: 42\n"
        "d:\n"
        "    - \n"
        "      c: 3\n"
        "    - \n"
        "      c: 4\n"
        "e:\n"
        "    x:\n"
        "        c: 5\n"
        "    y:\n"
        "        c: 6"
    )

    assert result == expected


def test_indentation_level():
    obj = {"a": 1, "b": 2}
    expected = "        a: 1\n        b: 2"
    assert object_to_formatted_text(obj, indent_level=2) == expected
