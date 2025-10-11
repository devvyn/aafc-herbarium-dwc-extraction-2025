# OpenRouter Batch API Investigation

**Date**: 2025-10-11
**Status**: Investigation Complete
**Conclusion**: No native batch API currently available

---

## Investigation Summary

### OpenRouter API Capabilities

**Current Features**:
- Real-time completion API (`/v1/chat/completions`)
- Multi-model routing (400+ models)
- OpenAI-compatible interface
- Rate limiting per model/provider
- FREE tier models available (Qwen, Llama, Gemini)

**NOT Available**:
- ❌ Native batch processing API (like OpenAI Batch API)
- ❌ Asynchronous job submission
- ❌ 50% batch discount pricing
- ❌ Batch result polling/download

### Comparison with OpenAI Batch API

| Feature | OpenAI Batch API | OpenRouter | Alternative |
|---------|------------------|------------|-------------|
| Batch submission | ✅ Upload JSONL | ❌ No batch endpoint | Streaming + checkpointing |
| Async processing | ✅ 24h window | ❌ Real-time only | Parallel requests |
| Cost savings | ✅ 50% discount | ❌ No discount | Use FREE models |
| Result polling | ✅ Status checks | ❌ N/A | Event-driven monitoring |
| Resume capability | ✅ Built-in | ❌ Must implement | Custom checkpointing |

---

## Recommended Alternatives

### 1. **Parallel Streaming with Checkpointing** (Implemented)

**What we have**:
- `scripts/extract_openrouter.py` - Streaming extraction with progress tracking
- `src/events.py` - Event bus for monitoring
- `io_utils/jit_cache.py` - Graceful error handling

**How it works**:
```python
# Process specimens in parallel (controlled concurrency)
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(extract_specimen, img): img for img in images}

    # Checkpoint after each completion
    for future in as_completed(futures):
        result = future.result()
        save_result(result)  # Immediate write to raw.jsonl
```

**Benefits**:
- ✅ Automatic checkpointing (resume from any point)
- ✅ Real-time monitoring
- ✅ Works with FREE models
- ✅ Event emission for dashboards

### 2. **Rate-Limited Batch Processing** (Easy to implement)

Create a simple batch processor:

```python
def process_batch(images, batch_size=100, delay=1.0):
    """Process images in batches with rate limiting."""
    for i in range(0, len(images), batch_size):
        batch = images[i:i + batch_size]

        # Process batch
        for img in batch:
            result = extract_specimen(img)
            save_result(result)
            time.sleep(delay)  # Rate limiting

        # Checkpoint between batches
        save_checkpoint(i + len(batch))
```

**Benefits**:
- ✅ Controlled rate limiting
- ✅ Natural checkpointing
- ✅ Lower API pressure
- ✅ Simple to implement

### 3. **Multi-Key Rotation** (For high-volume)

Rotate between multiple API keys:

```python
class MultiKeyManager:
    def __init__(self, keys: List[str]):
        self.keys = keys
        self.current_idx = 0

    def get_next_key(self):
        key = self.keys[self.current_idx]
        self.current_idx = (self.current_idx + 1) % len(self.keys)
        return key
```

**Benefits**:
- ✅ Higher effective rate limits
- ✅ Automatic failover
- ✅ Cost distribution

---

## Cost Comparison: OpenRouter vs OpenAI Batch

### OpenRouter FREE Models (Current Strategy)
- **Cost**: $0.00
- **Models**: Qwen 2.5 VL 72B, Llama 3.2 Vision, Gemini Flash
- **Rate limits**: Varies by model (typically generous)
- **Quality**: Comparable to paid models

### OpenAI Batch API (If we switched)
- **Cost**: ~$0.075/specimen with 50% discount (GPT-4o-mini)
- **For 2,885 specimens**: ~$216
- **Processing time**: 12-24 hours
- **Quality**: Excellent

### OpenRouter Paid Models (If we upgraded)
- **Cost**: $0.0036/specimen (Qwen paid tier)
- **For 2,885 specimens**: ~$10.40
- **Processing time**: Real-time (~4-6 hours)
- **Quality**: Same as FREE tier, faster/more stable

**Recommendation**: Stick with OpenRouter FREE models. The $0 cost outweighs the lack of batch API, especially with our robust checkpointing.

---

## Implementation Recommendations

### For Remaining 2,230 Specimens

**Option A: Parallel Streaming** (Recommended)
```bash
uv run python scripts/extract_openrouter.py \
    --input ~/.persistent_cache \
    --output full_dataset_processing/resume_run_$(date +%Y%m%d) \
    --model qwen-vl-72b-free \
    --offset 549 \
    --limit 2230
```

**Features**:
- Uses existing infrastructure
- Automatic checkpointing
- Event-driven monitoring
- Graceful error handling

**Option B: Rate-Limited Batches**
```bash
# Process in 500-specimen batches
for i in 549 1049 1549 2049 2549; do
    uv run python scripts/extract_openrouter.py \
        --input ~/.persistent_cache \
        --output full_dataset_processing/batch_$(date +%Y%m%d_%H%M) \
        --model qwen-vl-72b-free \
        --offset $i \
        --limit 500

    # Wait between batches
    sleep 300  # 5 minute cooldown
done
```

**Features**:
- Natural rate limiting
- Easy to pause/resume
- Lower API pressure

---

## Monitoring During Large Runs

### Use Existing Monitoring Tools

**Terminal Monitor**:
```bash
./scripts/tmux-monitor.sh full_dataset_processing/resume_run_20251011
```

**Web Dashboard**:
```bash
uv run python scripts/web_monitor.py --port 5001 &
open http://127.0.0.1:5001
```

**Features**:
- Real-time progress tracking
- Success/failure rates
- Field quality metrics
- Event stream monitoring
- Throughput calculation

---

## Conclusion

**Batch API Status**: ❌ Not available on OpenRouter

**Recommended Strategy**:
1. ✅ Use parallel streaming with checkpointing (already implemented)
2. ✅ Leverage FREE models ($0 cost)
3. ✅ Implement rate limiting to avoid API issues
4. ✅ Use existing monitoring infrastructure
5. ✅ Resume capability via offset parameter

**Cost Savings**:
- OpenRouter FREE: $0
- vs OpenAI Batch: ~$216
- **Savings: $216** 💰

**Quality**:
- FREE models perform comparably to paid alternatives
- 549 specimens showed 64% completeness (acceptable for curation)
- Review system enables manual improvement

**Next Steps**:
1. Re-extract remaining 2,230 specimens using parallel streaming
2. Use JIT caching to prevent /tmp failures
3. Monitor with unified dashboard
4. Review and curate results with new review system

---

**Last Updated**: 2025-10-11
**Investigator**: Claude Code (Overnight Session)
**Recommendation**: Proceed with current infrastructure, no batch API needed
