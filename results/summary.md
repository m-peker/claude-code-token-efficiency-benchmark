## Overall (400 single runs)

| condition | runs | success | median cost $ | cost × | 95% CI | cost × (stratified) | input tok × | output tok × | peak ctx × | turns × |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 30 | 100% | 0.060 | 1.00 | 0.89–1.12 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| best_practice | 30 | 100% | 0.058 | 0.88 | 0.80–1.00 | 0.90 | 0.88 | 0.95 | 0.96 | 0.93 |
| claudemd_bloated | 30 | 100% | 0.131 | 2.20 | 2.01–2.49 | 2.24 | 1.74 | 1.33 | 1.47 | 1.25 |
| claudemd_lean | 30 | 100% | 0.070 | 1.13 | 1.01–1.27 | 1.14 | 1.12 | 1.32 | 0.99 | 1.36 |
| effort_low | 30 | 100% | 0.053 | 0.89 | 0.81–1.01 | 0.92 | 0.95 | 0.86 | 0.99 | 0.89 |
| mcp_heavy | 30 | 100% | 0.069 | 1.23 | 1.07–1.38 | 1.24 | 1.09 | 1.11 | 1.05 | 1.15 |
| mcp_heavy_eager | 30 | 100% | 0.095 | 1.69 | 1.54–2.07 | 1.84 | 2.49 | 1.11 | 2.13 | 1.07 |
| model_haiku | 30 | 93% | 0.007 | 0.11 | 0.10–0.13 | 0.11 | 1.99 | 2.69 | 1.22 | 1.71 |
| model_opus | 30 | 100% | 0.152 | 2.29 | 2.05–2.71 | 2.44 | 1.24 | 1.56 | 1.05 | 1.09 |
| plan_mode | 25 | 92% | 0.160 | 2.80 | 2.28–3.59 | 2.74 | 2.32 | 3.93 | 1.21 | 2.02 |
| plan_opus_exec_sonnet | 25 | 100% | 0.252 | 4.15 | 3.75–5.19 | 4.26 | 2.34 | 2.97 | 1.21 | 2.01 |
| plan_sonnet_exec_haiku | 25 | 96% | 0.110 | 1.75 | 1.48–2.29 | 1.67 | 2.67 | 4.30 | 1.28 | 2.37 |
| plan_sonnet_exec_opus | 25 | 100% | 0.292 | 4.69 | 4.05–5.97 | 4.88 | 2.36 | 3.70 | 1.26 | 1.86 |
| specific_prompt | 30 | 100% | 0.046 | 0.74 | 0.65–0.82 | 0.72 | 0.78 | 0.85 | 0.94 | 0.84 |

## Per task (median)

| condition | task | n | success | cost $ | input tok | output tok | peak ctx | turns |
|---|---|---|---|---|---|---|---|---|
| baseline | t1_intrange | 5 | 100% | 0.046 | 107,162 | 750 | 27,846 | 4 |
| baseline | t2_help_order | 5 | 100% | 0.082 | 191,649 | 1,640 | 28,699 | 10 |
| baseline | t3_completion_hash | 5 | 100% | 0.071 | 135,350 | 1,467 | 28,777 | 8 |
| baseline | t4_keyvalue | 5 | 100% | 0.058 | 131,082 | 1,645 | 27,263 | 7 |
| baseline | t5_value_source | 5 | 100% | 0.062 | 80,781 | 1,816 | 29,596 | 5 |
| baseline | t6_default_map | 5 | 100% | 0.056 | 113,998 | 1,006 | 30,182 | 6 |
| best_practice | t1_intrange | 5 | 100% | 0.057 | 111,386 | 1,364 | 28,933 | 7 |
| best_practice | t2_help_order | 5 | 100% | 0.048 | 107,930 | 894 | 26,669 | 6 |
| best_practice | t3_completion_hash | 5 | 100% | 0.071 | 135,750 | 1,521 | 27,600 | 8 |
| best_practice | t4_keyvalue | 5 | 100% | 0.068 | 135,482 | 2,107 | 28,383 | 8 |
| best_practice | t5_value_source | 5 | 100% | 0.033 | 53,410 | 731 | 26,965 | 2 |
| best_practice | t6_default_map | 5 | 100% | 0.059 | 134,044 | 1,391 | 27,680 | 8 |
| claudemd_bloated | t1_intrange | 5 | 100% | 0.129 | 204,652 | 1,361 | 42,625 | 8 |
| claudemd_bloated | t2_help_order | 5 | 100% | 0.159 | 325,151 | 1,871 | 42,245 | 11 |
| claudemd_bloated | t3_completion_hash | 5 | 100% | 0.128 | 203,748 | 1,475 | 41,777 | 8 |
| claudemd_bloated | t4_keyvalue | 5 | 100% | 0.132 | 201,323 | 2,207 | 41,615 | 8 |
| claudemd_bloated | t5_value_source | 5 | 100% | 0.120 | 121,963 | 1,917 | 42,917 | 5 |
| claudemd_bloated | t6_default_map | 5 | 100% | 0.147 | 282,132 | 1,877 | 41,710 | 9 |
| claudemd_lean | t1_intrange | 5 | 100% | 0.068 | 136,104 | 1,372 | 28,601 | 8 |
| claudemd_lean | t2_help_order | 5 | 100% | 0.088 | 192,725 | 2,084 | 29,139 | 12 |
| claudemd_lean | t3_completion_hash | 5 | 100% | 0.058 | 133,923 | 1,182 | 28,039 | 7 |
| claudemd_lean | t4_keyvalue | 5 | 100% | 0.069 | 135,550 | 2,191 | 28,127 | 9 |
| claudemd_lean | t5_value_source | 5 | 100% | 0.063 | 80,996 | 1,976 | 28,877 | 7 |
| claudemd_lean | t6_default_map | 5 | 100% | 0.075 | 167,422 | 1,948 | 28,149 | 10 |
| effort_low | t1_intrange | 5 | 100% | 0.047 | 107,232 | 679 | 27,864 | 4 |
| effort_low | t2_help_order | 5 | 100% | 0.080 | 180,283 | 1,503 | 29,805 | 8 |
| effort_low | t3_completion_hash | 5 | 100% | 0.055 | 133,685 | 868 | 28,075 | 5 |
| effort_low | t4_keyvalue | 5 | 100% | 0.049 | 104,440 | 1,543 | 26,931 | 7 |
| effort_low | t5_value_source | 5 | 100% | 0.054 | 79,324 | 1,720 | 28,167 | 5 |
| effort_low | t6_default_map | 5 | 100% | 0.052 | 114,028 | 902 | 30,253 | 6 |
| mcp_heavy | t1_intrange | 5 | 100% | 0.054 | 113,679 | 815 | 29,028 | 5 |
| mcp_heavy | t2_help_order | 5 | 100% | 0.110 | 232,062 | 2,086 | 31,517 | 12 |
| mcp_heavy | t3_completion_hash | 5 | 100% | 0.089 | 143,776 | 1,538 | 29,976 | 9 |
| mcp_heavy | t4_keyvalue | 5 | 100% | 0.069 | 139,673 | 1,838 | 28,985 | 8 |
| mcp_heavy | t5_value_source | 5 | 100% | 0.080 | 86,605 | 2,097 | 29,653 | 6 |
| mcp_heavy | t6_default_map | 5 | 100% | 0.065 | 119,939 | 993 | 31,617 | 6 |
| mcp_heavy_eager | t1_intrange | 5 | 100% | 0.075 | 235,300 | 739 | 59,883 | 4 |
| mcp_heavy_eager | t2_help_order | 5 | 100% | 0.157 | 489,952 | 1,847 | 61,835 | 10 |
| mcp_heavy_eager | t3_completion_hash | 5 | 100% | 0.138 | 476,555 | 1,913 | 61,806 | 10 |
| mcp_heavy_eager | t4_keyvalue | 5 | 100% | 0.094 | 292,561 | 1,736 | 59,328 | 7 |
| mcp_heavy_eager | t5_value_source | 5 | 100% | 0.090 | 204,723 | 2,064 | 60,385 | 6 |
| mcp_heavy_eager | t6_default_map | 5 | 100% | 0.090 | 245,306 | 1,058 | 62,900 | 6 |
| model_haiku | t1_intrange | 5 | 100% | 0.005 | 153,231 | 2,366 | 33,621 | 9 |
| model_haiku | t2_help_order | 5 | 60% | 0.011 | 533,047 | 5,380 | 40,285 | 15 |
| model_haiku | t3_completion_hash | 5 | 100% | 0.008 | 309,513 | 3,953 | 33,360 | 14 |
| model_haiku | t4_keyvalue | 5 | 100% | 0.008 | 301,217 | 4,401 | 35,514 | 11 |
| model_haiku | t5_value_source | 5 | 100% | 0.005 | 130,213 | 2,691 | 34,674 | 9 |
| model_haiku | t6_default_map | 5 | 100% | 0.007 | 211,584 | 3,461 | 33,758 | 9 |
| model_opus | t1_intrange | 5 | 100% | 0.119 | 112,912 | 1,585 | 27,965 | 8 |
| model_opus | t2_help_order | 5 | 100% | 0.166 | 207,371 | 2,264 | 31,950 | 8 |
| model_opus | t3_completion_hash | 5 | 100% | 0.144 | 196,716 | 1,931 | 30,503 | 9 |
| model_opus | t4_keyvalue | 5 | 100% | 0.172 | 199,589 | 3,279 | 31,544 | 8 |
| model_opus | t5_value_source | 5 | 100% | 0.186 | 101,673 | 2,193 | 32,656 | 4 |
| model_opus | t6_default_map | 5 | 100% | 0.087 | 130,088 | 1,574 | 26,637 | 6 |
| plan_mode | t1_intrange | 5 | 100% | 0.108 | 233,510 | 2,668 | 33,620 | 11 |
| plan_mode | t2_help_order | 5 | 60% | 0.158 | 315,181 | 4,603 | 33,091 | 14 |
| plan_mode | t3_completion_hash | 5 | 100% | 0.201 | 314,025 | 6,387 | 34,576 | 14 |
| plan_mode | t4_keyvalue | 5 | 100% | 0.285 | 397,244 | 10,069 | 37,523 | 19 |
| plan_mode | t6_default_map | 5 | 100% | 0.154 | 305,038 | 3,560 | 34,577 | 11 |
| plan_opus_exec_sonnet | t1_intrange | 5 | 100% | 0.192 | 266,147 | 2,636 | 32,314 | 10 |
| plan_opus_exec_sonnet | t2_help_order | 5 | 100% | 0.291 | 366,718 | 3,390 | 36,424 | 15 |
| plan_opus_exec_sonnet | t3_completion_hash | 5 | 100% | 0.287 | 318,392 | 4,183 | 35,554 | 15 |
| plan_opus_exec_sonnet | t4_keyvalue | 5 | 100% | 0.353 | 344,907 | 5,981 | 36,560 | 18 |
| plan_opus_exec_sonnet | t6_default_map | 5 | 100% | 0.192 | 272,505 | 3,069 | 31,435 | 11 |
| plan_sonnet_exec_haiku | t1_intrange | 5 | 100% | 0.066 | 209,401 | 2,529 | 32,310 | 10 |
| plan_sonnet_exec_haiku | t2_help_order | 5 | 80% | 0.125 | 334,119 | 4,004 | 33,574 | 17 |
| plan_sonnet_exec_haiku | t3_completion_hash | 5 | 100% | 0.154 | 500,961 | 9,468 | 39,595 | 17 |
| plan_sonnet_exec_haiku | t4_keyvalue | 5 | 100% | 0.110 | 395,845 | 8,933 | 39,838 | 23 |
| plan_sonnet_exec_haiku | t6_default_map | 5 | 100% | 0.106 | 404,178 | 5,143 | 38,581 | 15 |
| plan_sonnet_exec_opus | t1_intrange | 5 | 100% | 0.187 | 211,634 | 2,631 | 32,967 | 10 |
| plan_sonnet_exec_opus | t2_help_order | 5 | 100% | 0.281 | 339,472 | 3,991 | 35,431 | 16 |
| plan_sonnet_exec_opus | t3_completion_hash | 5 | 100% | 0.407 | 419,694 | 8,345 | 36,764 | 12 |
| plan_sonnet_exec_opus | t4_keyvalue | 5 | 100% | 0.338 | 347,268 | 6,132 | 38,431 | 13 |
| plan_sonnet_exec_opus | t6_default_map | 5 | 100% | 0.276 | 291,301 | 3,864 | 36,027 | 12 |
| specific_prompt | t1_intrange | 5 | 100% | 0.051 | 83,322 | 1,164 | 28,404 | 6 |
| specific_prompt | t2_help_order | 5 | 100% | 0.032 | 76,882 | 680 | 25,696 | 4 |
| specific_prompt | t3_completion_hash | 5 | 100% | 0.046 | 104,676 | 1,091 | 26,766 | 7 |
| specific_prompt | t4_keyvalue | 5 | 100% | 0.062 | 105,890 | 2,190 | 27,890 | 8 |
| specific_prompt | t5_value_source | 5 | 100% | 0.038 | 78,808 | 834 | 26,619 | 3 |
| specific_prompt | t6_default_map | 5 | 100% | 0.053 | 130,562 | 1,262 | 26,777 | 6 |

## Long session vs fresh sessions

baseline fresh sessions, sum of task medians: $0.376, 760,022 input tokens
long_session__r1: $0.340, 898,095 input tokens, 6/6 ok, peak ctx by step [27548, 29976, 32814, 36226, 38126, 46308]
long_session__r2: $0.355, 929,307 input tokens, 6/6 ok, peak ctx by step [27485, 31508, 34554, 38438, 40371, 47092]
long_session__r3: $0.373, 969,937 input tokens, 6/6 ok, peak ctx by step [28152, 32755, 36633, 40376, 42323, 49404]
long_session__r4: $0.311, 722,964 input tokens, 6/6 ok, peak ctx by step [19305, 24361, 27432, 30439, 32430, 38304]
long_session__r5: $0.363, 838,093 input tokens, 6/6 ok, peak ctx by step [19457, 24704, 28385, 32371, 34315, 41804]
long_session_compact__r1: $0.492, 651,836 input tokens, 6/6 ok, peak ctx by step [19752, 22173, 25443, 25443, 25443, 25443]
long_session_compact__r2: $0.561, 943,398 input tokens, 6/6 ok, peak ctx by step [27475, 30042, 34436, 34436, 34436, 34436]
long_session_compact__r3: $0.570, 1,031,927 input tokens, 6/6 ok, peak ctx by step [27471, 32702, 33928, 33928, 33928, 33928]
long_session_compact__r4: $0.576, 955,511 input tokens, 6/6 ok, peak ctx by step [28098, 32410, 34380, 34380, 34380, 34380]
long_session_compact__r5: $0.591, 975,802 input tokens, 6/6 ok, peak ctx by step [28350, 31812, 34537, 34537, 34537, 34630]
