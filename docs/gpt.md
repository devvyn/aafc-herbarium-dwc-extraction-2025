# GPT engine usage

## Supplying API keys

Set `OPENAI_API_KEY` in your environment before running the toolkit. Use a local
secret manager or a `.env` file that is excluded from version control. Avoid
embedding keys in scripts or configuration.

## Customising prompts

Prompt templates live under [`../config/prompts`](../config/prompts). Modify
these files or point the configuration to another directory via the
`gpt.prompt_dir` setting to adjust system behaviour. Each task uses separate
files for different roles:

- `*.system.prompt` sets global behaviour and constraints.
- `*.user.prompt` contains the request that is sent with runtime input.
- `*.assistant.prompt` (optional) can seed an example reply.

## Configuration options

The `[gpt]` section of [`../config/config.default.toml`](../config/config.default.toml)
controls the model, fallback behaviour, prompt directory, and dry-run mode for
offline testing.

## Testing

Unit tests in [../tests/unit/test_gpt_prompts.py](../tests/unit/test_gpt_prompts.py) load fixture templates from [../tests/resources/gpt_prompts](../tests/resources/gpt_prompts) to ensure custom prompt directories and legacy `*.prompt` files are honoured. Run `pytest` to validate these behaviours whenever prompts change.
