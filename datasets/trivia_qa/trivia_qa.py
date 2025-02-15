# coding=utf-8
# Copyright 2022 The HuggingFace datasets Authors, DataLab Authors and the current dataset script contributor.
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
"""The Trivia datalab"""



import glob
import json
import os
import datalabs
from datalabs import get_task, TaskType

logger = datalabs.logging.get_logger(__name__)

_CITATION = """
@article{2017arXivtriviaqa,
       author = {{Joshi}, Mandar and {Choi}, Eunsol and {Weld},
                 Daniel and {Zettlemoyer}, Luke},
        title = "{triviaqa: A Large Scale Distantly Supervised Challenge Dataset for Reading Comprehension}",
      journal = {arXiv e-prints},
         year = 2017,
          eid = {arXiv:1705.03551},
        pages = {arXiv:1705.03551},
archivePrefix = {arXiv},
       eprint = {1705.03551},
}
"""
_DOWNLOAD_URL_TMPL = "http://nlp.cs.washington.edu/triviaqa/data/triviaqa-{}.tar.gz"
_WEB_EVIDENCE_DIR = "evidence/web"
_WIKI_EVIDENCE_DIR = "evidence/wikipedia"

_DESCRIPTION = """\
TriviaqQA is a reading comprehension dataset containing over 650K
question-answer-evidence triples. TriviaqQA includes 95K question-answer
pairs authored by trivia enthusiasts and independently gathered evidence
documents, six per question on average, that provide high quality distant
supervision for answering the questions.
"""

_RC_DESCRIPTION = """\
Question-answer pairs where all documents for a given question contain the
answer string(s).
"""

_UNFILTERED_DESCRIPTION = """\
110k question-answer pairs for open domain QA where not all documents for a
given question contain the answer string(s). This makes the unfiltered dataset
more appropriate for IR-style QA.
"""

_CONTEXT_ADDENDUM = "Includes context from Wikipedia and search results."


def _web_evidence_dir(tmp_dir):
    return sorted(glob.glob(os.path.join(tmp_dir, _WEB_EVIDENCE_DIR)))


def _wiki_evidence_dir(tmp_dir):
    return sorted(glob.glob(os.path.join(tmp_dir, _WIKI_EVIDENCE_DIR)))


def _qa_files(file_paths, sources, split, unfiltered):
    qa_dir = (
        os.path.join(file_paths["unfiltered"], "triviaqa-unfiltered")
        if unfiltered
        else os.path.join(file_paths["rc"], "qa")
    )

    suffix_mapping = {
        datalabs.Split.TRAIN: "train.json",
        datalabs.Split.VALIDATION: "dev.json",
        datalabs.Split.TEST: "test-without-answers.json",
    }
    suffix = suffix_mapping[split]

    filenames = [f"unfiltered-web-{suffix}"] if unfiltered else [f"{source}-{suffix}" for source in sources]

    filenames = [os.path.join(qa_dir, filename) for filename in filenames]

    return sorted(filenames)


class TriviaQaConfig(datalabs.BuilderConfig):
    """BuilderConfig for TriviaQA."""

    def __init__(self, source="all", unfiltered=False, exclude_context=False, **kwargs):
        """BuilderConfig for TriviaQA.
        Args:
          unfiltered: bool, whether to use the unfiltered version of the dataset,
            intended for open-domain QA.
          exclude_context: bool, whether to exclude Wikipedia and search context for
            reduced size.
          **kwargs: keyword arguments forwarded to super.
        """
        name = "unfiltered" if unfiltered else "rc"

        assert source in ["all", "web", "wikipedia"]

        # there is no unfiltered version for the wikipedia subset
        # --> unfiltered subset for source="all" is the same as for source="web"
        # --> only accept source="all" if unfiltered is True
        assert not unfiltered or source == "all"

        if source != "all":
            name += f".{source}"

        if exclude_context:
            name += ".nocontext"
        description = _UNFILTERED_DESCRIPTION if unfiltered else _RC_DESCRIPTION
        if not exclude_context:
            description += _CONTEXT_ADDENDUM
        super(TriviaQaConfig, self).__init__(
            name=name, description=description, version=datalabs.Version("1.0.0"), **kwargs
        )

        self.sources = ["web", "wikipedia"] if source == "all" else [source]
        self.unfiltered = unfiltered
        self.exclude_context = exclude_context


class TriviaQa(datalabs.GeneratorBasedBuilder):
    """TriviaQA is a reading comprehension dataset.
    It containss over 650K question-answer-evidence triples.
    """

    BUILDER_CONFIGS = [
        TriviaQaConfig(source="all", unfiltered=False, exclude_context=False),  # rc
        TriviaQaConfig(source="all", unfiltered=False, exclude_context=True),  # rc.nocontext
        TriviaQaConfig(source="all", unfiltered=True, exclude_context=False),  # unfiltered
        TriviaQaConfig(source="all", unfiltered=True, exclude_context=True),  # unfilered.nocontext
        TriviaQaConfig(source="web", unfiltered=False, exclude_context=False),  # rc
        TriviaQaConfig(source="web", unfiltered=False, exclude_context=True),  # rc.nocontext
        TriviaQaConfig(source="wikipedia", unfiltered=False, exclude_context=False),  # rc
        TriviaQaConfig(source="wikipedia", unfiltered=False, exclude_context=True),  # rc.nocontext
    ]
    DEFAULT_WRITER_BATCH_SIZE = 1000  # examples are quite big, so set this value to save some RAM

    def _info(self):
        return datalabs.DatasetInfo(
            description=_DESCRIPTION,
            features=datalabs.Features(
                {
                    "question": datalabs.Value("string"),
                    "question_id": datalabs.Value("string"),
                    "question_source": datalabs.Value("string"),
                    "entity_pages": datalabs.features.Sequence(
                        {
                            "doc_source": datalabs.Value("string"),
                            "filename": datalabs.Value("string"),
                            "title": datalabs.Value("string"),
                            "wiki_context": datalabs.Value("string"),
                        }
                    ),
                    "search_results": datalabs.features.Sequence(
                        {
                            "description": datalabs.Value("string"),
                            "filename": datalabs.Value("string"),
                            "rank": datalabs.Value("int32"),
                            "title": datalabs.Value("string"),
                            "url": datalabs.Value("string"),
                            "search_context": datalabs.Value("string"),
                        }
                    ),
                    "answer": dict(
                        {
                            "aliases": datalabs.features.Sequence(datalabs.Value("string")),
                            "normalized_aliases": datalabs.features.Sequence(datalabs.Value("string")),
                            "matched_wiki_entity_name": datalabs.Value("string"),
                            "normalized_matched_wiki_entity_name": datalabs.Value("string"),
                            "normalized_value": datalabs.Value("string"),
                            "type": datalabs.Value("string"),
                            "value": datalabs.Value("string"),
                        }
                    ),
                }
            ),
            supervised_keys=None,
            homepage="http://nlp.cs.washington.edu/triviaqa/",
            citation=_CITATION,
            task_templates = [get_task(TaskType.qa_extractive)(
                question_column='question',
                context_column='search_results',
                answers_column='answer'
            )]
        )

    def _split_generators(self, dl_manager):
        """Returns SplitGenerators."""
        cfg = self.config
        download_urls = dict()
        if not (cfg.unfiltered and cfg.exclude_context):
            download_urls["rc"] = _DOWNLOAD_URL_TMPL.format("rc")
        if cfg.unfiltered:
            download_urls["unfiltered"] = _DOWNLOAD_URL_TMPL.format("unfiltered")
        file_paths = dl_manager.download_and_extract(download_urls)

        if cfg.exclude_context:
            web_evidence_dir = None
            wiki_evidence_dir = None
        else:
            web_evidence_dir = os.path.join(file_paths["rc"], _WEB_EVIDENCE_DIR)
            wiki_evidence_dir = os.path.join(file_paths["rc"], _WIKI_EVIDENCE_DIR)

        return [
            datalabs.SplitGenerator(
                name=name,
                gen_kwargs={
                    "files": _qa_files(file_paths, cfg.sources, name, cfg.unfiltered),
                    "web_dir": web_evidence_dir,
                    "wiki_dir": wiki_evidence_dir,
                },
            )
            for name in [datalabs.Split.TRAIN, datalabs.Split.VALIDATION, datalabs.Split.TEST]
        ]

    def _generate_examples(self, files, web_dir, wiki_dir):
        """This function returns the examples."""

        def parse_example(article):
            """Return a single example from an article JSON record."""

            def _strip(collection):
                return [item.strip() for item in collection]

            if "Answer" in article:
                answer = article["Answer"]
                answer_dict = {
                    "aliases": _strip(answer["Aliases"]),
                    "normalized_aliases": _strip(answer["NormalizedAliases"]),
                    "matched_wiki_entity_name": answer.get("MatchedWikiEntryName", "").strip(),
                    "normalized_matched_wiki_entity_name": answer.get("NormalizedMatchedWikiEntryName", "").strip(),
                    "normalized_value": answer["NormalizedValue"].strip(),
                    "type": answer["Type"].strip(),
                    "value": answer["Value"].strip(),
                }
            else:
                answer_dict = {
                    "aliases": [],
                    "normalized_aliases": [],
                    "matched_wiki_entity_name": "<unk>",
                    "normalized_matched_wiki_entity_name": "<unk>",
                    "normalized_value": "<unk>",
                    "type": "",
                    "value": "<unk>",
                }

            if self.config.exclude_context:
                article["SearchResults"] = []
                article["EntityPages"] = []

            def _add_context(collection, context_field, file_dir):
                """Adds context from file, or skips if file does not exist."""
                new_items = []
                for item in collection:
                    if "Filename" not in item:
                        logger.info("Missing context 'Filename', skipping.")
                        continue

                    new_item = item.copy()
                    fname = item["Filename"]
                    try:
                        with open(os.path.join(file_dir, fname), encoding="utf-8") as f:
                            new_item[context_field] = f.read()
                    except (IOError, FileNotFoundError):
                        logger.info("File does not exist, skipping: %s", fname)
                        continue
                    new_items.append(new_item)
                return new_items

            def _strip_if_str(v):
                return v.strip() if isinstance(v, str) else v

            def _transpose_and_strip_dicts(dicts, field_names):
                return {
                    datalabs.naming.camelcase_to_snakecase(k): [_strip_if_str(d[k]) for d in dicts]
                    for k in field_names
                }

            search_results = _transpose_and_strip_dicts(
                _add_context(article.get("SearchResults", []), "SearchContext", web_dir),
                ["Description", "Filename", "Rank", "Title", "Url", "SearchContext"],
            )

            entity_pages = _transpose_and_strip_dicts(
                _add_context(article.get("EntityPages", []), "WikiContext", wiki_dir),
                ["DocSource", "Filename", "Title", "WikiContext"],
            )

            question = article["Question"].strip()
            question_id = article["QuestionId"]
            question_source = article["QuestionSource"].strip()

            return {
                "entity_pages": entity_pages,
                "search_results": search_results,
                "question": question,
                "question_id": question_id,
                "question_source": question_source,
                "answer": answer_dict,
            }

        for filepath in files:
            logger.info("generating examples from = %s", filepath)
            fname = os.path.basename(filepath)

            with open(filepath, encoding="utf-8") as f:
                current_record = ""
                for line in f:
                    if line == "        {\n":
                        current_record = line
                    elif line.startswith("        }"):  # Handles final record as well.
                        article = json.loads(current_record + "}")
                        current_record = ""
                        example = parse_example(article)
                        yield "%s_%s" % (fname, example["question_id"]), example
                    else:
                        current_record += line