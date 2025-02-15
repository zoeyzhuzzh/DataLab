# coding=utf-8
# Copyright 2020 The TensorFlow datalab Authors and the HuggingFace datasets, DataLab Authors.
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

# Lint as: python3
"""Detecing which tweets showcase hate or racist remarks."""

import csv
import datalabs
from datalabs import get_task, TaskType


_DESCRIPTION = """\
The objective of this task is to detect hate speech in tweets. For the sake of simplicity, we say a tweet contains hate speech if it has a racist or sexist sentiment associated with it. So, the task is to classify racist or sexist tweets from other tweets.

Formally, given a training sample of tweets and labels, where label ‘1’ denotes the tweet is racist/sexist and label ‘0’ denotes the tweet is not racist/sexist, your objective is to predict the labels on the given test dataset.
"""

_CITATION = """\
@InProceedings{Z
Roshan Sharma:dataset,
title = {Sentimental Analysis of Tweets for Detecting Hate/Racist Speeches},
authors={Roshan Sharma},
year={2018}
}
"""

_TRAIN_DOWNLOAD_URL = (
    "https://raw.githubusercontent.com/sharmaroshan/Twitter-Sentiment-Analysis/master/train_tweet.csv"
)


class TweetsHateSpeechDetection(datalabs.GeneratorBasedBuilder):
    """Detecing which tweets showcase hate or racist remarks."""

    def _info(self):
        return datalabs.DatasetInfo(
            description=_DESCRIPTION,
            features=datalabs.Features(
                {
                    "label": datalabs.ClassLabel(names=["no-hate-speech", "hate-speech"]),
                    "text": datalabs.Value("string"),
                }
            ),
            homepage="https://github.com/sharmaroshan/Twitter-Sentiment-Analysis",
            citation=_CITATION,
            task_templates=[get_task(TaskType.hatespeech_identification)(text_column="text", label_column="label")],
        )

    def _split_generators(self, dl_manager):
        train_path = dl_manager.download_and_extract(_TRAIN_DOWNLOAD_URL)

        return [
            datalabs.SplitGenerator(name=datalabs.Split.TRAIN, gen_kwargs={"filepath": train_path}),
        ]

    def _generate_examples(self, filepath):
        """Generate Tweet examples."""
        textualize_label = {"0":"no-hate-speech",
                                 "1":"hate-speech",}
        with open(filepath, encoding="utf-8") as csv_file:
            csv_reader = csv.reader(
                csv_file, quotechar='"', delimiter=",", quoting=csv.QUOTE_ALL, skipinitialspace=True
            )
            next(csv_reader, None)
            for id_, row in enumerate(csv_reader):
                row = row[1:]
                (label, tweet) = row

                yield id_, {
                    "label": textualize_label[label],
                    "text": (tweet),
                }
