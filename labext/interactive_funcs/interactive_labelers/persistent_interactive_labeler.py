import csv
import logging
import os
from typing import List, Dict, Tuple, Optional

from labext.interactive_funcs.interactive_labelers.interactive_labeler import InteractiveLabeler, Example


class PersistentInteractiveLabeler(InteractiveLabeler):
    logger = logging.getLogger("labext.interactive.persistent_labeler")

    def __init__(self, output_file: str, examples: List[Example], class_ids: List[str]):
        assert {l is not None and l != "" and l.strip() == l for l in class_ids}
        super().__init__()
        self.examples = examples
        self.class_ids = class_ids

        self.labeled_examples: Dict[str, str] = {}
        self.output_file = output_file

        if os.path.exists(output_file):
            self.logger.debug("Load output file...")
            with open(output_file, "r") as f:
                reader = csv.reader(f, delimiter='\t')
                n_changes = 0
                del_examples = set()
                set_class_ids = set(class_ids)

                for example_id, class_id in reader:
                    if class_id == "":
                        class_id = None
                    else:
                        assert class_id in set_class_ids

                    if example_id in self.labeled_examples:
                        n_changes += 1

                    self.labeled_examples[example_id] = class_id

                    if class_id is None:
                        del_examples.add(example_id)
                    elif example_id in del_examples:
                        del_examples.remove(example_id)

                for example_id in del_examples:
                    assert self.labeled_examples[example_id] is None
                    del self.labeled_examples[example_id]

            if len(self.labeled_examples) == 0 or n_changes / len(self.labeled_examples) > 0.2:
                # so many duplication, optimize the log
                self.logger.debug("Optimizing existing output file as it contains many duplications...")
                with open(output_file + ".tmp", "w") as f:
                    writer = csv.writer(f, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
                    for example_id, class_id in self.labeled_examples.items():
                        writer.writerow([example_id, class_id])

                os.rename(output_file + ".tmp", output_file)
            self.logger.debug("Finish loading output file...")

    def persist_changes(self, changes: List[Tuple[str, Optional[str]]]):
        """Persist changes to the disk
        Each change is a pair of (example_id and class_id), the class_id is None when the previous annotation is deleted
        """
        with open(self.output_file, "a") as f:
            writer = csv.writer(f, delimiter='\t', quoting=csv.QUOTE_MINIMAL)
            for example_id, class_id in changes:
                if class_id is None:
                    del self.labeled_examples[example_id]
                else:
                    self.labeled_examples[example_id] = class_id
                writer.writerow([example_id, class_id])

    def get_label(self, example_id) -> str:
        return self.labeled_examples[example_id]

    def has_label(self, example_id) -> bool:
        return example_id in self.labeled_examples