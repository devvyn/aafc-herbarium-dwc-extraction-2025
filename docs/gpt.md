# GPT engine usage

## Supplying API keys

Set `OPENAI_API_KEY` in your environment before running the toolkit. Use a local
secret manager or `.env` file that is excluded from version control. Avoid
embedding keys in scripts or configuration.

## Customising prompts

Prompt templates live under [`../engines/gpt/prompts`](../engines/gpt/prompts).
Modify these files or point the configuration to alternatives to adjust system
behaviour.

## Configuration options

The `[gpt]` section of [`../config/config.default.toml`](../config/config.default.toml)
controls the model, fallback behaviour, and dry-run mode for offline testing.
