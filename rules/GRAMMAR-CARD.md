# iLang declaration notation (for reading a brain, not for writing the spec)

- `::NAME{k:v|k2:v2}` is one declaration block. NAME is upper case. Fields are separated by `|`, key and value by `:`.
- Blocks nest: `::CORE{ ::GENE{...} }`. Indentation is only for reading.
- `T:` one trait per line, meaning "I do it this way".
- `A:x⇒y` one anti-pattern per line, meaning "x leads to y, don't".
- `conf:tentative|confirmed` confidence; `scope:global|project` scope; `when:condition` applies only under that condition.
- `@NAME` in upper case is an entity: a person, a repo, a machine, a task.
- `::STATE{@X, k:v}` the state of an entity right now. `::FACT{key:k|value:v}` one fact.
  `::PROGRESS{done|next|unverified}` progress. `::DECIDED{what|why|context}` a decision.
  `::LEARNED{what|from:...}` a lesson. `::BOUNDARY{never:...|scope:...}` a hard boundary; it always wins.
- How to read: take keys and values literally; no runtime or dictionary is needed. An unknown block is a labelled note: read its body.
- Never say DNA, gene or mutation to the user; say "I noted that" or "you told me last time".
- The full spec is at github.com/ilang-ai/ilang-spec. Reading a brain does not need it.
