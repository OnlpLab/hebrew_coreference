# Error Analysis Summary for Hebrew Coreference Resolution

## Overall Error Statistics

- **Lingmess Coref**: 393/454 errors (86.6% error rate)
- **LLM Raw Text**: 451/454 errors (99.3% error rate)
- **LLM Gold Mentions**: 445/454 errors (98.0% error rate)

## Error Type Analysis


### No Prediction

- **Lingmess Coref**: 176 (38.8%)
- **LLM Raw Text**: 271 (59.7%)
- **LLM Gold Mentions**: 4 (0.9%)

### Partial Match

- **Lingmess Coref**: 195 (43.0%)
- **LLM Raw Text**: 180 (39.6%)
- **LLM Gold Mentions**: 372 (81.9%)

### Over Prediction

- **Lingmess Coref**: 22 (4.8%)
- **LLM Raw Text**: 0 (0.0%)
- **LLM Gold Mentions**: 69 (15.2%)

### Complete Mismatch

- **Lingmess Coref**: 0 (0.0%)
- **LLM Raw Text**: 0 (0.0%)
- **LLM Gold Mentions**: 0 (0.0%)

## Key Findings

- **Best performing approach**: Lingmess Coref with 393 errors
- **Most common error type**: partial match (747 occurrences)