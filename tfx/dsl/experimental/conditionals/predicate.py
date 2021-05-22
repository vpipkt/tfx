# Copyright 2021 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Predicate for Conditional channels."""

import enum

from typing import Any, Dict, Optional, Union
from tfx.utils import json_utils

# To resolve circular dependency caused by type annotations.
ph = Any  # tfx/dsl/placeholder/placeholder.py imports this module.


class CompareOp(enum.Enum):
  EQUAL = '__eq__'
  NOT_EQUAL = '__ne__'
  LESS_THAN = '__lt__'
  LESS_THAN_OR_EQUAL = '__le__'
  GREATER_THAN = '__gt__'
  GREATER_THAN_OR_EQUAL = '__ge__'


class LogicalOp(enum.Enum):
  NOT = 'not'
  AND = 'and'
  OR = 'or'


class _Comparison:
  """Represents a comparison between two placeholders."""

  def __init__(self, compare_op: CompareOp, left: 'ph.Placeholder',
               right: Union[int, float, str, 'ph.Placeholder']):
    self.compare_op = compare_op
    self.left = left
    self.right = right

  def to_json_dict(self):
    return {
        'cmp_op':
            str(self.compare_op),
        'left':
            self.left.encode(),
        'right': (self.right.encode() if hasattr(self.right, 'encode') and
                  not isinstance(self.right, str) else self.right),
    }


class _LogicalExpression:
  """Represents a boolean logical expression."""

  def __init__(self,
               logical_op: LogicalOp,
               left: Union[_Comparison, '_LogicalExpression'],
               right: Optional[Union[_Comparison,
                                     '_LogicalExpression']] = None):
    self.logical_op = logical_op
    self.left = left
    self.right = right

  def to_json_dict(self):
    return {
        'logical_op': str(self.logical_op),
        'left': self.left.to_json_dict(),
        'right': self.right.to_json_dict() if self.right else None,
    }


class Predicate(json_utils.Jsonable):
  """Experimental Predicate object.

  Note that we don't overwrite the default implementation of `from_json_dict`,
  because it is not used, so it doesn't matter.
  """

  def __init__(self, value: Union[_Comparison, _LogicalExpression]):
    self.value = value

  @classmethod
  def from_comparison(
      cls, cmp_op: CompareOp, left: 'ph.Placeholder',
      right: Union[int, str, float, 'ph.Placeholder']) -> 'Predicate':
    return Predicate(_Comparison(cmp_op, left, right))

  def negated(self) -> 'Predicate':
    """Applies a NOT operation to the Predicate."""
    return Predicate(_LogicalExpression(LogicalOp.NOT, self.value))

  def logical_and(self, other: 'Predicate') -> 'Predicate':
    """Applies an AND operation."""
    return Predicate(_LogicalExpression(LogicalOp.AND, self.value, other.value))

  def logical_or(self, other: 'Predicate') -> 'Predicate':
    """Applies an OR operation."""
    return Predicate(_LogicalExpression(LogicalOp.OR, self.value, other.value))

  def to_json_dict(self) -> Dict[str, Any]:
    return self.value.to_json_dict()
