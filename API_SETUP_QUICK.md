# Quick API Setup for Multi-Model Testing

## Current Status
✅ **Vision API** - FREE, already working
❌ **OpenAI (gpt-4o-mini)** - Need API key
❌ **Google (Gemini)** - Need API key
❌ **Anthropic (Claude)** - Need API key

## Add API Keys (Optional)

### OpenAI (gpt-4o-mini - $0.65 for full dataset)
```bash
export OPENAI_API_KEY="sk-..."
```

### Google Gemini ($11 for full dataset)
```bash
export GOOGLE_API_KEY="..."
```

### Anthropic Claude ($65 for full dataset)
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## Pragmatic Approach

**Option 1: FREE** (Do this now)
- Use Vision API with NEW expanded schema + layout-aware prompts
- Compare against old extraction
- Likely improvement from better prompts alone

**Option 2: PAID** (If needed after Option 1)
- Add OpenAI key → test gpt-4o-mini ($0.65)
- Compare accuracy vs Vision API
- Only pay if Vision API insufficient

## Test Commands

### Test with Vision (FREE)
```bash
# Copy 20 validated images to test directory
python test_vision_improved.py
```

### Test with gpt-4o-mini (requires OPENAI_API_KEY)
```bash
python cli.py process --input test_20_specimens --output gpt4omini_test --engine gpt4omini
```

### Test with Gemini (requires GOOGLE_API_KEY)
```bash
python cli.py process --input test_20_specimens --output gemini_test --engine gemini
```

## Recommendation

1. **Start FREE**: Test improved Vision API prompts first
2. **Add OpenAI if needed**: gpt-4o-mini is cheapest paid option ($0.65)
3. **Skip expensive models**: Claude/Gemini probably not worth $11-65
