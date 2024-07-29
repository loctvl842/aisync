In the Marvel Cinematic Universe, Tony Stark, also known as Iron Man, named his various suits with different designations. Some of the notable suit names include:

- **Mark I** - This was Tony Stark's first Iron Man suit, which he built while in captivity.
- **Mark II** - A prototype suit that led to the development of the Iron Man armor.
- **Mark III** - The first fully operational Iron Man suit that Stark used in combat.
- **Mark XLII** (Mark 42) - This suit featured in "Iron Man 3" and had the ability to autonomously fly to Tony Stark and attach itself to him.
- **Hulkbuster** - A specialized suit designed specifically to combat the Hulk, as seen in "Avengers: Age of Ultron."
- **Mark L (Mark 50)** - Featured in "Avengers: Infinity War" and "Avengers: Endgame," this suit had nanotechnology, allowing it to materialize around Tony Stark's body.

There are many more suits, each with its own unique capabilities and designations. Stark's naming convention typically involves the prefix "Mark," followed by a number.

### 3 key components of a suit:
- `Hooks`: this is used to configure various part of your AI product (llm, embedder, prompts, etc.)
- `Tools`: those are the functions that your LLM can be equipped with to conquer tasks that require a predefined set of instructions to obtain accurate output.
- `Node`: this is a fundamental unit of operation in AISync. One node corresponds to one prompt + LLM to complete a task

### Currently available `hooks` in AISync:
- `build_prompt_tool_calling`: configure prompt to use your prompt for using tools.
  - Make sure you have the following 3 parameters in your prompt: `{query}`, `{tools}`, `{allowed_tools}`.
  -  (Or you can just use the default prompt)
- `build_prompt_prefix`: configure prompt prefix for node_core
- `build_prompt_suffix`: configure prompt suffix for node_core 
  - You have access to the following parameters `{buffer_memory}`, `{document_memory}`, `{persist_memory}` , `{tool_output}`
- `customized_input`: by default, AISync only handles your query in the input payload. To make your input more diverse, use this hook to customize it.
- `embed_input`: used to define which part of your input payload to be embedded for usage with VectorDB.
- `embed_output`: embed your output, currently only support raw text output.
- `get_path_to_doc`: Specify your path in to read documents from.
- `set_document_similarity_search_metric`: set the distance metric for similarity search with documents
  - 4 distance metric options:
    - l2_distance
    - l1_distance
    - max_inner_product
    - cosine_distance
- `set_greeting_message`: configure the starting message for the suit
- `set_max_token`: set max token to be used for buffer memory
- `set_persist_memory_similarity_search_metric`: set the distance metric for similarity search with persist memory
  - 4 distance metric options:
    - l2_distance
    - l1_distance
    - max_inner_product
    - cosine_distance
- `set_suit_embedder`: configure the embedder for your product
- `set_suit_llm`: configure the LLM for your product
- `set_suit_splitter`: configure the splitter/chunker for processing your documents
- `should_customize_node_llm`: for each node, decide whether to use assistant's llm or user's config llm
