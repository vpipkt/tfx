# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for tfx.utils.channel."""

import tensorflow as tf
from tfx.dsl.placeholder import placeholder
from tfx.types.artifact import Artifact
from tfx.types.artifact import Property
from tfx.types.artifact import PropertyType
from tfx.types.channel import Channel

from ml_metadata.proto import metadata_store_pb2


class _MyType(Artifact):
  TYPE_NAME = 'MyTypeName'
  PROPERTIES = {
      'string_value': Property(PropertyType.STRING),
  }


class _AnotherType(Artifact):
  TYPE_NAME = 'AnotherTypeName'


class ChannelTest(tf.test.TestCase):

  def testValidChannel(self):
    instance_a = _MyType()
    instance_b = _MyType()
    chnl = Channel(_MyType).set_artifacts([instance_a, instance_b])
    self.assertEqual(chnl.type_name, 'MyTypeName')
    self.assertCountEqual(chnl.get(), [instance_a, instance_b])

  def testInvalidChannelType(self):
    instance_a = _MyType()
    instance_b = _MyType()
    with self.assertRaises(ValueError):
      Channel(_AnotherType).set_artifacts([instance_a, instance_b])

  def testStringTypeNameNotAllowed(self):
    with self.assertRaises(ValueError):
      Channel('StringTypeName')

  def testJsonRoundTrip(self):
    channel = Channel(
        type=_MyType,
        additional_properties={
            'string_value': metadata_store_pb2.Value(string_value='forty-two')
        },
        additional_custom_properties={
            'int_value': metadata_store_pb2.Value(int_value=42)
        })
    serialized = channel.to_json_dict()
    rehydrated = Channel.from_json_dict(serialized)
    self.assertIs(channel.type, rehydrated.type)
    self.assertEqual(channel.type_name, rehydrated.type_name)
    self.assertEqual(channel.additional_properties,
                     rehydrated.additional_properties)
    self.assertEqual(channel.additional_custom_properties,
                     rehydrated.additional_custom_properties)

  def testJsonRoundTripUnknownArtifactClass(self):
    channel = Channel(type=_MyType)

    serialized = channel.to_json_dict()
    serialized['type']['name'] = 'UnknownTypeName'

    rehydrated = Channel.from_json_dict(serialized)
    self.assertEqual('UnknownTypeName', rehydrated.type_name)
    self.assertEqual(channel.type._get_artifact_type().properties,
                     rehydrated.type._get_artifact_type().properties)
    self.assertTrue(rehydrated.type._AUTOGENERATED)

  def testFutureProducesPlaceholder(self):
    channel = Channel(type=_MyType)
    future = channel.future()
    self.assertIsInstance(future, placeholder.ChannelWrappedPlaceholder)
    self.assertIs(future.channel, channel)
    self.assertIsInstance(future[0], placeholder.ChannelWrappedPlaceholder)
    self.assertIsInstance(future.value, placeholder.ChannelWrappedPlaceholder)


if __name__ == '__main__':
  tf.test.main()
