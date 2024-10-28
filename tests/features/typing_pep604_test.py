from __future__ import annotations

import pytest

from pyupgrade._data import Settings
from pyupgrade._main import _fix_plugins


@pytest.mark.parametrize(
    ('s', 'version'),
    (
        pytest.param(
            'from typing import Union\n'
            'x: Union[int, str]\n',
            (3, 9),
            id='<3.10 Union',
        ),
        pytest.param(
            'from typing import Optional\n'
            'x: Optional[str]\n',
            (3, 9),
            id='<3.10 Optional',
        ),
        pytest.param(
            'from __future__ import annotations\n'
            'from typing import Union\n'
            'SomeAlias = Union[int, str]\n',
            (3, 9),
            id='<3.9 not in a type annotation context',
        ),
        # https://github.com/python/mypy/issues/9945
        pytest.param(
            'from __future__ import annotations\n'
            'from typing import Union\n'
            'SomeAlias = Union[int, str]\n',
            (3, 10),
            id='3.10+ not in a type annotation context',
        ),
        # https://github.com/python/mypy/issues/9998
        pytest.param(
            'from typing import Union\n'
            'def f() -> Union[()]: ...\n',
            (3, 10),
            id='3.10+ empty Union',
        ),
        # https://github.com/asottile/pyupgrade/issues/567
        pytest.param(
            'from typing import Optional\n'
            'def f() -> Optional["str"]: ...\n',
            (3, 10),
            id='3.10+ Optional of forward reference',
        ),
        pytest.param(
            'from typing import Union\n'
            'def f() -> Union[int, "str"]: ...\n',
            (3, 10),
            id='3.10+ Union of forward reference',
        ),
        pytest.param(
            'from typing import Union\n'
            'def f() -> Union[1:2]: ...\n',
            (3, 10),
            id='invalid Union slicing',
        ),
    ),
)
def test_fix_pep604_types_noop(s, version):
    assert _fix_plugins(s, settings=Settings(min_version=version)) == s


def test_noop_keep_runtime_typing():
    s = '''\
from __future__ import annotations
from typing import Union
def f(x: Union[int, str]) -> None: ...
'''
    assert _fix_plugins(s, settings=Settings(keep_runtime_typing=True)) == s


def test_keep_runtime_typing_ignored_in_py310():
    s = '''\
from __future__ import annotations
from typing import Union
def f(x: Union[int, str]) -> None: ...
'''
    expected = '''\
from __future__ import annotations
from typing import Union
def f(x: int | str) -> None: ...
'''
    settings = Settings(min_version=(3, 10), keep_runtime_typing=True)
    assert _fix_plugins(s, settings=settings) == expected


@pytest.mark.parametrize(
    ('s', 'expected'),
    (
        pytest.param(
            'from typing import Union\n'
            'x: Union[int, str]\n',

            'from typing import Union\n'
            'x: int | str\n',

            id='Union rewrite',
        ),
        pytest.param(
            'x: typing.Union[int]\n',

            'x: int\n',

            id='Union of only one value',
        ),
        pytest.param(
            'x: typing.Union[Foo[str, int], str]\n',

            'x: Foo[str, int] | str\n',

            id='Union containing a value with brackets',
        ),
        pytest.param(
            'x: typing.Union[typing.List[str], str]\n',

            'x: list[str] | str\n',

            id='Union containing pep585 rewritten type',
        ),
        pytest.param(
            'x: typing.Union[int, str,]\n',

            'x: int | str\n',

            id='Union trailing comma',
        ),
        pytest.param(
            'x: typing.Union[(int, str)]\n',

            'x: int | str\n',

            id='Union, parenthesized tuple',
        ),
        pytest.param(
            'x: typing.Union[\n'
            '    int,\n'
            '    str\n'
            ']\n',

            'x: (\n'
            '    int |\n'
            '    str\n'
            ')\n',

            id='Union multiple lines',
        ),
        pytest.param(
            'x: typing.Union[\n'
            '    int,\n'
            '    str,\n'
            ']\n',

            'x: (\n'
            '    int |\n'
            '    str\n'
            ')\n',

            id='Union multiple lines with trailing commas',
        ),
        pytest.param(
            'from typing import Optional\n'
            'x: Optional[str]\n',

            'from typing import Optional\n'
            'x: str | None\n',

            id='Optional rewrite',
        ),
        pytest.param(
            'x: typing.Optional[\n'
            '    ComplicatedLongType[int]\n'
            ']\n',

            'x: None | (\n'
            '    ComplicatedLongType[int]\n'
            ')\n',

            id='Optional rewrite multi-line',
        ),
        pytest.param(
            'from __future__ import annotations\n'
            'from typing import Optional\n'
            'x: Optional["str"]\n',

            'from __future__ import annotations\n'
            'from typing import Optional\n'
            'x: str | None\n',

            id='Optional rewrite with forward reference',
        ),
        pytest.param(
            'from typing import Union, Sequence\n'
            'def f(x: Union[Union[A, B], Sequence[Union[C, D]]]): pass\n',

            'from typing import Union\n'
            'from collections.abc import Sequence\n'
            'def f(x: A | B | Sequence[C | D]): pass\n',

            id='nested unions',
        ),
        pytest.param(
            'from typing import Annotated, Union\n'
            'x: Union[str, Annotated[int, f"{x})"]]\n',

            'from typing import Annotated, Union\n'
            'x: str | Annotated[int, f"{x})"]\n',

            id='union, 3.12: ignore close brace in fstring',
        ),
        pytest.param(
            'from typing import Annotated, Union\n'
            'x: Union[str, Annotated[int, f"{x}("]]\n',

            'from typing import Annotated, Union\n'
            'x: str | Annotated[int, f"{x}("]\n',

            id='union, 3.12: ignore open brace in fstring',
        ),
        pytest.param(
            'from typing import Annotated, Optional\n'
            'x: Optional[Annotated[int, f"{x}("]]\n',

            'from typing import Annotated, Optional\n'
            'x: Annotated[int, f"{x}("] | None\n',

            id='optional, 3.12: ignore open brace in fstring',
        ),
        pytest.param(
            'from typing import Annotated, Optional\n'
            'x: Optional[Annotated[int, f"{x})"]]\n',

            'from typing import Annotated, Optional\n'
            'x: Annotated[int, f"{x})"] | None\n',

            id='optional, 3.12: ignore close brace in fstring',
        ),
        pytest.param(
            'from typing import Optional, Union\n'
            'def f(x: Optional[Union[int, None]]): pass\n'
            'def g(x: Union[Optional[int], None]): pass\n',

            'from typing import Optional, Union\n'
            'def f(x: int | None): pass\n'
            'def g(x: int | None): pass\n',

            id='nested unions and optionals',
        ),
        # pytest.param(
        #     'from typing import Optional, Union\n'
        #     'def f(x: Optional[Union[int, None]]): pass\n'
        #     'def g(x: Union[Union[int, None], None]): pass\n'
        #     'def h(x: Union[int, int, None]): pass\n'
        #     'def i(x: Union[Union[int, None], int]): pass\n'
        #     'def j(x: Union[Union[int, None], int]): pass\n # comment',

        #     'from typing import Optional, Union\n'
        #     'def f(x: int | None): pass\n'
        #     'def g(x: int | None): pass\n'
        #     'def h(x: int | None): pass\n'
        #     'def i(x: int | None): pass\n'
        #     'def j(x: int | None): pass # comment\n',

        #     id='cnested unions or optionals with duplicated types',
        # ),
        pytest.param(
            'from typing import Union\n'
            'def k(x: Union[a.b | a.c, a.b, list[str], str]): pass\n',

            'from typing import Union\n'
            'def k(x: a.b | a.c | list[str] | str): pass\n',

            id='complex',
        ),
        pytest.param(
            'from typing import Union\n'
            'def kk(x: Union[list[int, str], list[Union[str, int]]]):\n'
            '    pass\n',

            'from typing import Union\n'
            'def kk(x: list[int, str]):\n'
            '    pass\n',

            id='nested types',
            marks=pytest.mark.skip(
                reason='TODO: requires more complex typing consolidation',
            ),
        ),
        pytest.param(
            'from typing import Union\n'
            'def k(x: Union[Union[Union[Union[a, b], a], c], a]): pass\n',

            'from typing import Union\n'
            'def k(x: a | b | c): pass\n',

            id='deep nested unions with duplicated types',
        ),
    ),
)
def test_fix_pep604_types(s, expected):
    assert _fix_plugins(s, settings=Settings(min_version=(3, 10))) == expected


@pytest.mark.parametrize(
    ('s', 'expected'),
    (
        pytest.param(
            'from __future__ import annotations\n'
            'from typing import Union\n'
            'x: Union[int, str]\n',

            'from __future__ import annotations\n'
            'from typing import Union\n'
            'x: int | str\n',

            id='variable annotations',
        ),
        pytest.param(
            'from __future__ import annotations\n'
            'from typing import Union\n'
            'def f(x: Union[int, str]) -> None: ...\n',

            'from __future__ import annotations\n'
            'from typing import Union\n'
            'def f(x: int | str) -> None: ...\n',

            id='argument annotations',
        ),
        pytest.param(
            'from __future__ import annotations\n'
            'from typing import Union\n'
            'def f() -> Union[int, str]: ...\n',

            'from __future__ import annotations\n'
            'from typing import Union\n'
            'def f() -> int | str: ...\n',

            id='return annotations',
        ),
    ),
)
def test_fix_generic_types_future_annotations(s, expected):
    assert _fix_plugins(s, settings=Settings()) == expected


# TODO: test multi-line as well
