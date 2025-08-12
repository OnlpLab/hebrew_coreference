# Error Analysis Summary for Hebrew Coreference Resolution

## Overall Error Statistics

- **Lingmess Coref**: 393/454 errors (86.6% error rate)
- **GPT-4o-mini Raw Text**: 451/454 errors (99.3% error rate)
- **GPT-4o-mini Gold Mentions**: 445/454 errors (98.0% error rate)
- **Gemini 2.5 Pro Raw Text**: 442/454 errors (97.4% error rate)
- **Gemini 2.5 Pro Gold Mentions**: 415/454 errors (91.4% error rate)

## Error Type Analysis


### No Prediction

- **Lingmess Coref**: 176 (38.8%)
- **GPT-4o-mini Raw Text**: 271 (59.7%)
- **GPT-4o-mini Gold Mentions**: 4 (0.9%)
- **Gemini 2.5 Pro Raw Text**: 201 (44.3%)
- **Gemini 2.5 Pro Gold Mentions**: 14 (3.1%)

### Partial Match

- **Lingmess Coref**: 195 (43.0%)
- **GPT-4o-mini Raw Text**: 180 (39.6%)
- **GPT-4o-mini Gold Mentions**: 372 (81.9%)
- **Gemini 2.5 Pro Raw Text**: 231 (50.9%)
- **Gemini 2.5 Pro Gold Mentions**: 354 (78.0%)

### Over Prediction

- **Lingmess Coref**: 22 (4.8%)
- **GPT-4o-mini Raw Text**: 0 (0.0%)
- **GPT-4o-mini Gold Mentions**: 69 (15.2%)
- **Gemini 2.5 Pro Raw Text**: 10 (2.2%)
- **Gemini 2.5 Pro Gold Mentions**: 47 (10.4%)

### Complete Mismatch

- **Lingmess Coref**: 0 (0.0%)
- **GPT-4o-mini Raw Text**: 0 (0.0%)
- **GPT-4o-mini Gold Mentions**: 0 (0.0%)
- **Gemini 2.5 Pro Raw Text**: 0 (0.0%)
- **Gemini 2.5 Pro Gold Mentions**: 0 (0.0%)

## Key Findings

- **Best performing approach**: Lingmess Coref with 393 errors
- **Most common error type**: partial match (1332 occurrences)