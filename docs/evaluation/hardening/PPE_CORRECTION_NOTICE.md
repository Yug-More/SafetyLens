# PPE semantic-label correction — November 8, 2026

Historical predictions and reports remain unchanged. Their equipment ground-truth names assumed numeric mirror labels retained publisher order. This was false: the mirror renumbered original numeric classes in lexical order. Person was unaffected; helmet/vest and other equipment semantics were wrong. The original equipment AP/precision/recall values are withdrawn and must not be reused as model accuracy.

Independent original publisher annotations matched all 1,172 boxes across the current fixed 100 images with maximum coordinate error of two pixels and no unmatched boxes. The mapping was established without predictions. See [PPE_EVALUATION.md](../../PPE_EVALUATION.md), `../research/verified-label-mapping.json` and corrected replay of the original 24-image predictions under `../research/ppe24-corrected-*.json`. Detection/fall metrics are unaffected. Licensing and wearer-validation limitations remain.
