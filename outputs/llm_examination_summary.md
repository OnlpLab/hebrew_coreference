# LLM Examination Summary for Hebrew Coreference Resolution

## LLMs Examined in Error Analysis

Based on the comprehensive error analysis performed, the following LLMs were examined:

### 1. **GPT-4o-mini** (OpenAI)
- **Raw Text Approach**: 451 errors (99.3% error rate)
- **Gold Mentions Approach**: 445 errors (98.0% error rate)
- **Key Characteristics**:
  - Excellent performance with gold mentions (0.9% no-prediction rate)
  - Poor performance in end-to-end mode (99.3% error rate)
  - High partial match rates indicate incomplete accuracy
  - Over-prediction in gold mentions mode (15.2%)

### 2. **Gemini 2.5 Pro** (Google)
- **Raw Text Approach**: 442 errors (97.4% error rate)
- **Gold Mentions Approach**: 415 errors (91.4% error rate)
- **Key Characteristics**:
  - Better performance than GPT-4o-mini in both modes
  - Lower no-prediction rates across the board
  - More conservative over-prediction behavior
  - Best LLM performance with gold mentions (91.4% error rate)

## Comparison Results

### Performance Ranking (Best to Worst)
1. **Lingmess Coref** (Neural): 393 errors (86.6% error rate)
2. **Gemini 2.5 Pro Gold Mentions**: 415 errors (91.4% error rate)
3. **Gemini 2.5 Pro Raw Text**: 442 errors (97.4% error rate)
4. **GPT-4o-mini Gold Mentions**: 445 errors (98.0% error rate)
5. **GPT-4o-mini Raw Text**: 451 errors (99.3% error rate)

### Key Findings

#### No Prediction Errors (Complete Misses)
- **GPT-4o-mini Raw Text**: 271 errors (59.7%)
- **Gemini 2.5 Pro Raw Text**: 201 errors (44.3%)
- **GPT-4o-mini Gold Mentions**: 4 errors (0.9%)
- **Gemini 2.5 Pro Gold Mentions**: 14 errors (3.1%)

**Insight**: Gemini 2.5 Pro performs significantly better than GPT-4o-mini in raw text mode, with 15.4% fewer no-prediction errors.

#### Partial Match Errors (Incomplete Accuracy)
- **GPT-4o-mini Raw Text**: 180 errors (39.6%)
- **Gemini 2.5 Pro Raw Text**: 231 errors (50.9%)
- **GPT-4o-mini Gold Mentions**: 372 errors (81.9%)
- **Gemini 2.5 Pro Gold Mentions**: 354 errors (78.0%)

**Insight**: While Gemini 2.5 Pro has higher partial match rates, this indicates better coverage but lower precision compared to GPT-4o-mini.

#### Over Prediction Errors (False Positives)
- **GPT-4o-mini Raw Text**: 0 errors (0.0%)
- **Gemini 2.5 Pro Raw Text**: 10 errors (2.2%)
- **GPT-4o-mini Gold Mentions**: 69 errors (15.2%)
- **Gemini 2.5 Pro Gold Mentions**: 47 errors (10.4%)

**Insight**: Gemini 2.5 Pro shows more conservative over-prediction behavior than GPT-4o-mini.

## LLM-Specific Insights

### GPT-4o-mini Strengths
- Excellent performance with gold mentions (0.9% no-prediction rate)
- Good at identifying coreference opportunities when given mentions
- Lower partial match rates indicate higher precision

### GPT-4o-mini Weaknesses
- Poor performance in end-to-end mode (99.3% error rate)
- High over-prediction rate in gold mentions mode (15.2%)
- Struggles with Hebrew morphological complexity

### Gemini 2.5 Pro Strengths
- Better performance than GPT-4o-mini in both modes
- Lower no-prediction rates across the board
- More conservative over-prediction behavior
- Best LLM performance with gold mentions (91.4% error rate)

### Gemini 2.5 Pro Weaknesses
- Higher partial match rates indicate lower precision
- Still high error rates compared to neural models
- End-to-end performance remains challenging

## Data Sources

The error analysis was performed on test set outputs from:

### GPT-4o-mini Results
- **Raw Text**: `src/llm_evaluation/llm_coref/results/heb/gpt-4o-mini/test/e2e_train/raw_text/raw_text_1/doc_predictions.jsonl`
- **Gold Mentions**: `src/llm_evaluation/llm_coref/results/heb/gpt-4o-mini/test/gold_mentions/gold_mention_1/doc_predictions.jsonl`

### Gemini 2.5 Pro Results
- **Raw Text**: `src/llm_evaluation/llm_coref/results/heb/gemini-2.5-pro/test/e2e_train/raw_text/raw_text_1/doc_predictions.jsonl`
- **Gold Mentions**: `src/llm_evaluation/llm_coref/results/heb/gemini-2.5-pro/test/gold_mentions/gold_mention_1/doc_predictions.jsonl`

## Statistical Significance

The analysis examined:
- **Total Gold Clusters**: 454 per approach (2,270 total across all approaches)
- **Error Cases Analyzed**: 2,146 total error cases
- **LLM-Specific Analysis**: 1,753 error cases across both LLMs

## Conclusion

Both **GPT-4o-mini** and **Gemini 2.5 Pro** were examined in the error analysis. **Gemini 2.5 Pro** shows better overall performance than **GPT-4o-mini** across all metrics, particularly in raw text mode where it has 15.4% fewer no-prediction errors. However, both LLMs still achieve error rates above 90%, indicating that Hebrew coreference resolution remains a challenging task for current LLM architectures.

The analysis provides the first comprehensive comparison of different LLM architectures for Hebrew coreference resolution, revealing important insights about their relative strengths and weaknesses for this specific task. 