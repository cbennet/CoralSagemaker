"""
Usage:
  # From tensorflow/models/
  # Create train data:
  python generate_tfrecord.py --input_csv=data/train_labels.csv  --output_tfrecord=train.record

  # Create test data:
  python generate_tfrecord.py --input_csv=data/test_labels.csv  --output_tfrecord=test.record
"""
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import os
import io
import pandas as pd
import tensorflow as tf
import json
from parse_meta import get_labels

from PIL import Image
from object_detection.utils import dataset_util
from collections import namedtuple, OrderedDict
import argparse


def class_text_to_int(label, labels):
    return labels.index(label)


def split(df, group):
    data = namedtuple('data', ['filename', 'object'])
    gb = df.groupby(group)
    return [data(filename, gb.get_group(x)) for filename, x in zip(gb.groups.keys(), gb.groups)]


def create_tf_example(group, path, labels):
    with tf.gfile.GFile(os.path.join(path, '{}'.format(group.filename)), 'rb') as fid:
        encoded_jpg = fid.read()
    encoded_jpg_io = io.BytesIO(encoded_jpg)
    image = Image.open(encoded_jpg_io)
    width, height = image.size

    filename = group.filename.encode('utf8')
    image_format = b'jpg'
    xmins = []
    xmaxs = []
    ymins = []
    ymaxs = []
    classes_text = []
    classes = []

    for index, row in group.object.iterrows():
        xmins.append(row['xmin'] / width)
        xmaxs.append(row['xmax'] / width)
        ymins.append(row['ymin'] / height)
        ymaxs.append(row['ymax'] / height)
        classes_text.append(row['class'].encode('utf8'))
        classes.append(class_text_to_int(row['class'], labels))
    tf_example = tf.train.Example(features=tf.train.Features(feature={
        'image/height': dataset_util.int64_feature(height),
        'image/width': dataset_util.int64_feature(width),
        'image/filename': dataset_util.bytes_feature(filename),
        'image/source_id': dataset_util.bytes_feature(filename),
        'image/encoded': dataset_util.bytes_feature(encoded_jpg),
        'image/format': dataset_util.bytes_feature(image_format),
        'image/object/bbox/xmin': dataset_util.float_list_feature(xmins),
        'image/object/bbox/xmax': dataset_util.float_list_feature(xmaxs),
        'image/object/bbox/ymin': dataset_util.float_list_feature(ymins),
        'image/object/bbox/ymax': dataset_util.float_list_feature(ymaxs),
        'image/object/class/text': dataset_util.bytes_list_feature(classes_text),
        'image/object/class/label': dataset_util.int64_list_feature(classes),
        }))
    return tf_example


def main(_):

     # Taking command line arguments from users
    parser = argparse.ArgumentParser()
    parser.add_argument('-in', '--input_csv', help='define the input xml file', type=str, required=True)
    parser.add_argument('-out', '--output_tfrecord', help='define the output file ', type=str, required=True)
    args = parser.parse_args()
    writer = tf.python_io.TFRecordWriter(args.output_tfrecord)
    path = os.getcwd()
    examples = pd.read_csv(args.input_csv)
    grouped = split(examples, 'filename')
    labels = get_labels()
    for group in grouped:
        tf_example = create_tf_example(group, path, labels)
        writer.write(tf_example.SerializeToString())

    writer.close()
    output_path = os.path.join(os.getcwd(), args.output_tfrecord)
    print('Successfully created the TFRecords: {}'.format(output_path))
    import sys
    sys.exit()



if __name__ == '__main__':
    tf.app.run()
