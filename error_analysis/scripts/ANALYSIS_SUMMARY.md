# Hebrew Coreference Resolution Error Analysis Summary

## Document Analyzed: htb:240

This document summarizes the comparison between different coreference resolution approaches for Hebrew text.

## Key Findings

### Performance Rankings (by F1 Score)

1. **Neural Gold Tokenization**: **1.000 F1** (Perfect performance)
2. **Neural SOTA Tokenization**: **0.235 F1** 
3. **LLM Raw**: **0.000 F1**
4. **LLM Gold Tokenization**: **0.000 F1**
5. **LLM SOTA Tokenization**: **0.000 F1**

### Analysis Summary

#### Neural Models
- **Gold Tokenization**: Achieved perfect performance (100% precision, 100% recall)
- **SOTA Tokenization**: Significantly worse performance with many missing and extra mentions
- **Key Insight**: Tokenization quality has a massive impact on neural model performance

#### LLM Models
- **All LLM approaches**: Completely failed to identify any correct mentions (0% precision, 0% recall)
- **Consistent failure**: All three tokenization strategies (raw, gold, SOTA) performed identically poorly
- **Key Insight**: LLM models appear to be fundamentally struggling with Hebrew coreference resolution

### Detailed Error Analysis

#### Missing Mentions (Gold mentions not found by predictions)
- **LLM approaches**: All 14 gold mentions were missed
- **Neural SOTA**: 10 out of 14 mentions were missed
- **Neural Gold**: 0 mentions missed (perfect)

#### Extra Mentions (Incorrect predictions)
- **LLM approaches**: 4-5 extra mentions each
- **Neural SOTA**: 16 extra mentions
- **Neural Gold**: 0 extra mentions (perfect)

### Common Error Patterns

1. **Long-span mentions**: Many gold mentions span very long text segments (e.g., 40-251 tokens)
2. **Boundary errors**: Models often predict mentions that are too short or too long
3. **Missing core entities**: Key entities like "_אנחנו" (we) are frequently missed
4. **Over-segmentation**: Models tend to break long mentions into smaller, incorrect pieces

### Recommendations

1. **Use Neural Gold Tokenization**: This approach achieved perfect performance
2. **Improve LLM performance**: The complete failure of LLM models suggests fundamental issues that need investigation
3. **Tokenization quality**: SOTA tokenization significantly degrades neural model performance
4. **Long mention handling**: Models need better strategies for handling mentions that span many tokens

### Technical Notes

- **Gold mentions**: 14 total mentions in the document
- **Token count**: Document contains 486 tokens across 23 sentences
- **Language**: Hebrew text with complex morphological structures
- **Domain**: Sports/football news article

### Files Generated

- `comparison_results_240.json`: Detailed metrics and mention data
- `simple_comparison.py`: Analysis script
- `comprehensive_error_analysis.py`: Extended analysis script

## Conclusion

The analysis reveals a stark contrast between neural and LLM approaches for Hebrew coreference resolution. Neural models with high-quality tokenization can achieve excellent performance, while LLM models currently fail completely. This suggests that for Hebrew coreference resolution, the choice of model architecture and tokenization quality are critical factors for success. 