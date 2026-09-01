# salvage — verified recovery results

**Every metric on this page is computed on the `holdout` split.** Nothing here is a training number, and nothing here counts a rupee that a stepproof seal did not confirm arrived.

## AI judgment

Root cause settled deterministically on 48 of 48 records (100.0%); the model was invoked on the remaining 0.0% (0 records), where the gateway reason was absent or ambiguous.

The model reads unstructured context and returns a typed diagnostic. It never chooses an action, never touches money, and its prose is never used as evidence.

## Headline

| Measure | Value |
|---|---|
| Records at risk | 48 |
| Value at risk | ₹105,738.49 |
| Recovered, seal-verified | 23 |
| **Value recovered** | **₹58,764.55** |
| **Recovery rate by value** | **55.6%** |
| Recovery rate by count | 47.9% |
| Interventions | 48 |
| Intervention precision | 47.9% |
| False positives (would have self-healed) | 8 (16.7%) |
| False-positive cost | ₹0.25 |
| Suppressed by policy | 0 |
| Unresolved | 4 |
| **Failed verification** | **21** |
| **Verification gap** | **₹41,071.53** |

Calibration: 55.6% sits inside the 45–65% band published for reason-specific smart retries, and above the 20–30% a generic daily retry earns (Contract §10.2).

The verification gap is ₹41,071.53 across 21 records: money an agent that trusted its own success claim would have booked as recovered and never received.

## Audit trail

- Hash chain: **INTACT** — chain intact (234 records)
- Seals written: 234
- Seals that failed verification: 106
- Seals left unverified: 0

## Root-cause accuracy

The settled root cause matched the ground-truth label on 46 of 48 (95.8%) scored records. Accuracy is reported here and not in `Metrics`, which stays frozen at Contract §7.

## Failed verification — claimed, not confirmed

Each line quotes the sealed observation verbatim. These are the records where the action reported success and the payment state disagreed.

- `pay_I9M2BNfvUhzDt3` ₹3,112.57 via payment_link — seal `e554511d19a5` — evidence: `rzp plink_f219da64d2818f status=expired amount_paid=0 expected>=311257 for pay_I9M2BNfvUhzDt3`
- `pay_2NLUFRoPwFyIkY` ₹12,849.64 via retry — seal `de75d6877541` — evidence: `rzp pay_2NLUFRoPwFyIkY status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_Cn7XbDBgPQcE53` ₹360.56 via retry — seal `c307707a8436` — evidence: `rzp pay_Cn7XbDBgPQcE53 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_9iTFdREf99X45E` ₹777.27 via payment_link — seal `e4de4d94d28f` — evidence: `rzp plink_12bfc651547e53 status=expired amount_paid=0 expected>=77727 for pay_9iTFdREf99X45E`
- `pay_p5OCUaqMxtfM8T` ₹207.08 via retry — seal `b3ebd5333a7b` — evidence: `rzp pay_p5OCUaqMxtfM8T status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_AUqLTMxhDGYinF` ₹5,570.58 via retry — seal `c27116ea2ffe` — evidence: `rzp pay_AUqLTMxhDGYinF status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_Rg5Gex7MH68dD5` ₹581.30 via retry — seal `af3783edcf10` — evidence: `rzp pay_Rg5Gex7MH68dD5 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_PYWfLA9cbmyzyY` ₹179.37 via retry — seal `5f30540a3480` — evidence: `rzp pay_PYWfLA9cbmyzyY status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_pTACJmaf3IOoBA` ₹1,162.73 via payment_link — seal `3844037df621` — evidence: `rzp plink_b49cb54e7a62de status=expired amount_paid=0 expected>=116273 for pay_pTACJmaf3IOoBA`
- `pay_4GloMZgnoZmfDm` ₹933.14 via retry — seal `3243093ca63e` — evidence: `rzp pay_4GloMZgnoZmfDm status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_YlX0580hdgAB7O` ₹2,770.94 via retry — seal `97cbd6ddcaf0` — evidence: `rzp pay_YlX0580hdgAB7O status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_0JJPUgJUL8tG7G` ₹2,381.37 via payment_link — seal `b22c02dcb0d9` — evidence: `rzp plink_92e149eff645d4 status=expired amount_paid=0 expected>=238137 for pay_0JJPUgJUL8tG7G`
- `pay_kOLHaQr3PYsJ0d` ₹626.96 via payment_link — seal `f94fde1d64f7` — evidence: `rzp plink_93a12c7a2918d6 status=expired amount_paid=0 expected>=62696 for pay_kOLHaQr3PYsJ0d`
- `pay_H9WDRYAZarVQNt` ₹6,342.26 via payment_link — seal `6b245cf47f9b` — evidence: `rzp plink_5da743adf3e20d status=expired amount_paid=0 expected>=634226 for pay_H9WDRYAZarVQNt`
- `pay_xxWoTemF3JSXFj` ₹595.57 via payment_link — seal `c17e4db083f8` — evidence: `rzp plink_352fd732f0bdeb status=expired amount_paid=0 expected>=59557 for pay_xxWoTemF3JSXFj`
- `pay_QOIeDcIeeh1A0d` ₹1,554.50 via payment_link — seal `8ea61d7fea1c` — evidence: `rzp plink_6e0ce08cb96fda status=expired amount_paid=0 expected>=155450 for pay_QOIeDcIeeh1A0d`
- `pay_zwiPSaTan5DjCH` ₹2,218.99 via retry — seal `3e0f566d3a37` — evidence: `rzp pay_zwiPSaTan5DjCH status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_a3Xql3yRAQaky3` ₹417.06 via retry — seal `ccce1e279c9b` — evidence: `rzp pay_a3Xql3yRAQaky3 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_DlYH7Pin7pYbJ7` ₹2,406.77 via payment_link — seal `ee5c3f6f6e5a` — evidence: `rzp plink_1e6b13184d9fc9 status=expired amount_paid=0 expected>=240677 for pay_DlYH7Pin7pYbJ7`
- `pay_995GR3DtS8AyVI` ₹2,244.05 via retry — seal `cd3b27cc1797` — evidence: `rzp pay_995GR3DtS8AyVI status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_EafBI8w6ny22Cn` ₹8,779.00 via payment_link — seal `8b8cce204b25` — evidence: `rzp plink_f7e27266f26709 status=expired amount_paid=0 expected>=877900 for pay_EafBI8w6ny22Cn`
- `pay_LmBNYvCDONJkKA` ₹585.32 via retry — seal `728d4cfdfb68` — evidence: `rzp pay_LmBNYvCDONJkKA status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_0jsPaqVAzwRC0l` ₹191.40 via retry — seal `8f691096049d` — evidence: `rzp pay_0jsPaqVAzwRC0l status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_46eeJSkEqKb8FC` ₹608.46 via payment_link — seal `9a306071b57f` — evidence: `rzp plink_d396347a8adfed status=expired amount_paid=0 expected>=60846 for pay_46eeJSkEqKb8FC`
- `pay_hkiolUtPsvwTv8` ₹1,506.97 via payment_link — seal `0a6260011118` — evidence: `rzp plink_d8b055263b1b43 status=expired amount_paid=0 expected>=150697 for pay_hkiolUtPsvwTv8`
- `pay_ycnz31CXzyHJPG` ₹1,573.76 via retry — seal `92f5740ab1ba` — evidence: `rzp pay_ycnz31CXzyHJPG status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_NzJ4MGFw6ZoP4q` ₹1,209.88 via retry — seal `1a0563e9a4c7` — evidence: `rzp pay_NzJ4MGFw6ZoP4q status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_zKgAK6cyPVGi1f` ₹1,486.85 via retry — seal `cbb0a452d4dd` — evidence: `rzp pay_zKgAK6cyPVGi1f status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_HZ0w0YeU1sItZ5` ₹851.09 via payment_link — seal `15d72d827677` — evidence: `rzp plink_69ce72e4b84664 status=expired amount_paid=0 expected>=85109 for pay_HZ0w0YeU1sItZ5`
- `pay_NFp8xWrEzUAnIR` ₹1,607.05 via retry — seal `04c75c974faf` — evidence: `rzp pay_NFp8xWrEzUAnIR status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_aBsvV1W2eFUT38` ₹1,301.57 via payment_link — seal `9bee452d8d93` — evidence: `rzp plink_d18f88f1c12c56 status=expired amount_paid=0 expected>=130157 for pay_aBsvV1W2eFUT38`
- `pay_6RYV7F1nmotIEE` ₹776.81 via retry — seal `ddd719273bc8` — evidence: `rzp pay_6RYV7F1nmotIEE status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_FHdKObHEWd6iEN` ₹1,136.40 via payment_link — seal `2b62f8616eb2` — evidence: `rzp plink_f6cdebceef7209 status=expired amount_paid=0 expected>=113640 for pay_FHdKObHEWd6iEN`
- `pay_7TZVpBXKzAlPci` ₹320.67 via retry — seal `71f5f10dc454` — evidence: `rzp pay_7TZVpBXKzAlPci status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_EXSprkbegqWgib` ₹6,236.70 via retry — seal `1f5ac8cb7226` — evidence: `rzp pay_EXSprkbegqWgib status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_rXeW9n2Hf2modc` ₹467.13 via payment_link — seal `13f661a43f47` — evidence: `rzp plink_c126632a139571 status=expired amount_paid=0 expected>=46713 for pay_rXeW9n2Hf2modc`
- `pay_BxzFPKK3wOBFFM` ₹781.35 via payment_link — seal `3d6f9a9bca9f` — evidence: `rzp plink_c031b0dfd415d2 status=expired amount_paid=0 expected>=78135 for pay_BxzFPKK3wOBFFM`
- `pay_BTws1qdTEombEx` ₹1,678.95 via retry — seal `9ddd4a391069` — evidence: `rzp pay_BTws1qdTEombEx status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_grTylZOXyrW3ci` ₹6,209.64 via payment_link — seal `f3e1b0bd3e07` — evidence: `rzp plink_cd16cbdbd99b51 status=expired amount_paid=0 expected>=620964 for pay_grTylZOXyrW3ci`
- `pay_VwPCC9OT26SmYR` ₹834.21 via retry — seal `5b4147f88bfd` — evidence: `rzp pay_VwPCC9OT26SmYR status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_kasaFgywWNuxN2` ₹2,957.67 via retry — seal `e0cd3f1443d2` — evidence: `rzp pay_kasaFgywWNuxN2 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_InxalQRafdFAVs` ₹6,725.51 via payment_link — seal `89fd4fdde9a8` — evidence: `rzp plink_c6c3c949e69def status=expired amount_paid=0 expected>=672551 for pay_InxalQRafdFAVs`
- `pay_bxjb2lUY614iIK` ₹12,253.04 via retry — seal `634260ffd527` — evidence: `rzp pay_bxjb2lUY614iIK status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_jh719ezCaFZSfr` ₹494.52 via retry — seal `16b7f94af1f8` — evidence: `rzp pay_jh719ezCaFZSfr status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_4xquOcz75JqiZK` ₹6,263.37 via retry — seal `42a66e6d5c15` — evidence: `rzp pay_4xquOcz75JqiZK status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_7pKLLSsrkaMEfp` ₹563.23 via retry — seal `462bc7d4276c` — evidence: `rzp pay_7pKLLSsrkaMEfp status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_301baT8LJR50U0` ₹542.64 via payment_link — seal `52e5d6a1977f` — evidence: `rzp plink_36c0582e19df54 status=expired amount_paid=0 expected>=54264 for pay_301baT8LJR50U0`
- `pay_XdEnqJitG01DPF` ₹3,409.01 via payment_link — seal `7248cb1c0eb1` — evidence: `rzp plink_9c3ce3ba58609d status=expired amount_paid=0 expected>=340901 for pay_XdEnqJitG01DPF`
- `pay_XZ3Q8396PylM9o` ₹2,163.39 via payment_link — seal `721b76569727` — evidence: `rzp plink_f000116f313be0 status=expired amount_paid=0 expected>=216339 for pay_XZ3Q8396PylM9o`
- `pay_fUiCFqEiKWw3cU` ₹968.14 via retry — seal `b9fd28145ea1` — evidence: `rzp pay_fUiCFqEiKWw3cU status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_GmyPq3HIeU69bx` ₹724.71 via retry — seal `a81224681f67` — evidence: `rzp pay_GmyPq3HIeU69bx status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_7zkjAXQmEhXeZG` ₹484.77 via payment_link — seal `47a1622eb215` — evidence: `rzp plink_24eadb3f251dd0 status=expired amount_paid=0 expected>=48477 for pay_7zkjAXQmEhXeZG`
- `pay_8mdnhr6AT2DwBo` ₹341.19 via payment_link — seal `2f5977654f0d` — evidence: `rzp plink_b1803d57406d26 status=expired amount_paid=0 expected>=34119 for pay_8mdnhr6AT2DwBo`
- `pay_UJISrjHxfIyyN6` ₹4,478.62 via retry — seal `e5d5e360680f` — evidence: `rzp pay_UJISrjHxfIyyN6 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_QGfvJa9dX03XHn` ₹11,920.64 via retry — seal `66a7b1afe9e7` — evidence: `rzp pay_QGfvJa9dX03XHn status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_Fn9TMXpqcaYNTH` ₹1,492.72 via payment_link — seal `cfac6737baa8` — evidence: `rzp plink_a4c313fa72f21f status=created amount_paid=0 expected>=149272 for pay_Fn9TMXpqcaYNTH`
- `pay_qX4ySEioNCeCtm` ₹1,771.57 via payment_link — seal `7251f6cf2258` — evidence: `rzp plink_586d4b1e99b7c1 status=expired amount_paid=0 expected>=177157 for pay_qX4ySEioNCeCtm`
- `pay_nidWr5F1jukqno` ₹6,799.52 via retry — seal `be9bf0c55c43` — evidence: `rzp pay_nidWr5F1jukqno status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_e4PPqOPPMgIqe1` ₹1,552.22 via retry — seal `c665c477fb10` — evidence: `rzp pay_e4PPqOPPMgIqe1 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_jJDs1p44Opbz23` ₹1,168.25 via retry — seal `077a0685e8b4` — evidence: `rzp pay_jJDs1p44Opbz23 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_byLsU67UlGZmnV` ₹3,762.58 via retry — seal `418d8bb1b669` — evidence: `rzp pay_byLsU67UlGZmnV status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_zBDLSy17fJ3ohS` ₹4,330.02 via payment_link — seal `cd62d662fbc9` — evidence: `rzp plink_3bae3838b93b4f status=expired amount_paid=0 expected>=433002 for pay_zBDLSy17fJ3ohS`
- `pay_Jg3uYdR7wqStex` ₹14,699.00 via payment_link — seal `8cd1b2ba5619` — evidence: `rzp plink_d0146ed9f58c16 status=expired amount_paid=0 expected>=1469900 for pay_Jg3uYdR7wqStex`
- `pay_bTlV87tzEHVHa9` ₹3,211.65 via payment_link — seal `8998ddb98fae` — evidence: `rzp plink_0ae62b6e634426 status=created amount_paid=0 expected>=321165 for pay_bTlV87tzEHVHa9`
- `pay_llUk4Yu62UsyIx` ₹1,839.11 via retry — seal `00c2add807ec` — evidence: `rzp pay_llUk4Yu62UsyIx status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_B0TDQOGb5nOOGk` ₹135.72 via payment_link — seal `a5dabd847d4d` — evidence: `rzp plink_f5946ae90ce271 status=expired amount_paid=0 expected>=13572 for pay_B0TDQOGb5nOOGk`
- `pay_I6c9ALhLlygoMj` ₹677.91 via payment_link — seal `36f6b3f84fc0` — evidence: `rzp plink_45273f25f20ef8 status=expired amount_paid=0 expected>=67791 for pay_I6c9ALhLlygoMj`
- `pay_s1rCefoKzSeE2b` ₹4,013.11 via payment_link — seal `8857ab728bc4` — evidence: `rzp plink_290ae85e07591d status=expired amount_paid=0 expected>=401311 for pay_s1rCefoKzSeE2b`
- `pay_3TZeXfMgOeLuh6` ₹11,798.23 via payment_link — seal `e4e1bba07892` — evidence: `rzp plink_9d1664d030ea9c status=created amount_paid=0 expected>=1179823 for pay_3TZeXfMgOeLuh6`
- `pay_XGmCXgBJVqFwL0` ₹226.14 via payment_link — seal `3c957a6af2d1` — evidence: `rzp plink_019c03f224964d status=created amount_paid=0 expected>=22614 for pay_XGmCXgBJVqFwL0`
- `pay_W9T4wztIhPSNi4` ₹6,609.94 via payment_link — seal `1b03b643609a` — evidence: `rzp plink_e7115544e13ae8 status=expired amount_paid=0 expected>=660994 for pay_W9T4wztIhPSNi4`
- `pay_CpW5SaThRpZrSc` ₹181.08 via payment_link — seal `650192ee5332` — evidence: `rzp plink_02fab50699c5f6 status=expired amount_paid=0 expected>=18108 for pay_CpW5SaThRpZrSc`
- `pay_kNrKqms6SqY3zv` ₹268.95 via retry — seal `91a27870515b` — evidence: `rzp pay_kNrKqms6SqY3zv status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_Ip4UpL9izGoAlx` ₹1,582.75 via retry — seal `e9a60fab8cea` — evidence: `rzp pay_Ip4UpL9izGoAlx status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_7MCvKuAHWFdVte` ₹5,657.36 via retry — seal `5d009cd109dc` — evidence: `rzp pay_7MCvKuAHWFdVte status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_YefNQ00rqfjpAb` ₹1,945.58 via payment_link — seal `364901f5b5ee` — evidence: `rzp plink_f2286f046dc109 status=created amount_paid=0 expected>=194558 for pay_YefNQ00rqfjpAb`
- `pay_JppOdN2nqmD2wf` ₹1,282.14 via payment_link — seal `f53475bc0d25` — evidence: `rzp plink_b2bbad988469f4 status=created amount_paid=0 expected>=128214 for pay_JppOdN2nqmD2wf`
- `pay_r5Jn7X2xTIxZVc` ₹2,519.98 via payment_link — seal `3da6949cea23` — evidence: `rzp plink_e26a7c5b1a61a2 status=expired amount_paid=0 expected>=251998 for pay_r5Jn7X2xTIxZVc`
- `pay_rAz3Wgo5ofveCh` ₹2,325.97 via payment_link — seal `8f31c43c3663` — evidence: `rzp plink_807758f1fb2259 status=expired amount_paid=0 expected>=232597 for pay_rAz3Wgo5ofveCh`
- `pay_Qwvl59SY7SD7T4` ₹565.43 via payment_link — seal `b5a21b0e1459` — evidence: `rzp plink_cf41aa6e7ca5c9 status=expired amount_paid=0 expected>=56543 for pay_Qwvl59SY7SD7T4`
- `pay_FdX9CLEi7wGhW8` ₹687.13 via payment_link — seal `e1dfac4d145a` — evidence: `rzp plink_7599c3bfe75d1a status=expired amount_paid=0 expected>=68713 for pay_FdX9CLEi7wGhW8`
- `pay_El0BLoUTAAYgZ8` ₹1,346.08 via payment_link — seal `743aaed45b95` — evidence: `rzp plink_864dfcd23accfa status=expired amount_paid=0 expected>=134608 for pay_El0BLoUTAAYgZ8`
- `pay_ec75ZeGugK2CLd` ₹289.83 via retry — seal `03b050d12864` — evidence: `rzp pay_ec75ZeGugK2CLd status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_iUOxwIwaJHQZ9r` ₹2,279.73 via payment_link — seal `06fbf1f94990` — evidence: `rzp plink_9ace70e97f1f20 status=expired amount_paid=0 expected>=227973 for pay_iUOxwIwaJHQZ9r`
- `pay_8d1Yax8urz47gY` ₹3,842.21 via payment_link — seal `df5ef7b16881` — evidence: `rzp plink_99b81e8b95d18d status=expired amount_paid=0 expected>=384221 for pay_8d1Yax8urz47gY`
- `pay_uG613juRg5xNWZ` ₹34,076.41 via payment_link — seal `37f8ff523f6c` — evidence: `rzp plink_120e0b7bf956ab status=created amount_paid=0 expected>=3407641 for pay_uG613juRg5xNWZ`
- `pay_oz3X9YtzWaWVZ0` ₹2,069.05 via payment_link — seal `4623c8f46ff9` — evidence: `rzp plink_1731187f0a840c status=expired amount_paid=0 expected>=206905 for pay_oz3X9YtzWaWVZ0`
- `pay_jqi4A8mZ43kAmZ` ₹648.28 via payment_link — seal `d78fe7d27e5d` — evidence: `rzp plink_37980946ac55c5 status=expired amount_paid=0 expected>=64828 for pay_jqi4A8mZ43kAmZ`
- `pay_vrgjLnY8e3eRt8` ₹2,556.33 via payment_link — seal `feb8c83dc4a4` — evidence: `rzp plink_23aea8b559d6aa status=expired amount_paid=0 expected>=255633 for pay_vrgjLnY8e3eRt8`
- `pay_4qXuG18TVf1uWy` ₹1,676.56 via retry — seal `195fc7ff70b6` — evidence: `rzp pay_4qXuG18TVf1uWy status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_SCo6J5RgryT1F3` ₹1,267.84 via payment_link — seal `4ee06468013d` — evidence: `rzp plink_7fd51803babbc0 status=expired amount_paid=0 expected>=126784 for pay_SCo6J5RgryT1F3`
- `pay_1d6wiWGJVe3FjM` ₹26,614.63 via payment_link — seal `d657d9800bbf` — evidence: `rzp plink_89ad2d8c2232f3 status=expired amount_paid=0 expected>=2661463 for pay_1d6wiWGJVe3FjM`
- `pay_PZZrRWfOaufDVj` ₹529.79 via payment_link — seal `2c8d11bf2b5f` — evidence: `rzp plink_8aa7e926ceee45 status=expired amount_paid=0 expected>=52979 for pay_PZZrRWfOaufDVj`
- `pay_59d79lQJfgvI78` ₹3,083.50 via retry — seal `ce062f5407f9` — evidence: `rzp pay_59d79lQJfgvI78 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_vOAiJfdON1G1io` ₹6,973.29 via retry — seal `ac777614cb79` — evidence: `rzp pay_vOAiJfdON1G1io status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_z5IazTPBhiNQnK` ₹558.11 via payment_link — seal `b9c326db70ef` — evidence: `rzp plink_41f24ba082b6c4 status=expired amount_paid=0 expected>=55811 for pay_z5IazTPBhiNQnK`
- `pay_edBb4AnFgtDtHU` ₹467.89 via payment_link — seal `1dac8b948002` — evidence: `rzp plink_914470823e66cc status=expired amount_paid=0 expected>=46789 for pay_edBb4AnFgtDtHU`
- `pay_aThlbRBk2gpSuS` ₹631.79 via payment_link — seal `39cc2add504b` — evidence: `rzp plink_979771da21eee3 status=expired amount_paid=0 expected>=63179 for pay_aThlbRBk2gpSuS`
- `pay_bh9UAY2Fgl0Ul7` ₹813.83 via retry — seal `a2bc7430cfa6` — evidence: `rzp pay_bh9UAY2Fgl0Ul7 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_5OfSB6Sm2wIY3W` ₹1,960.75 via retry — seal `14ce09aa1aff` — evidence: `rzp pay_5OfSB6Sm2wIY3W status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_jRSxy7qfYro6uX` ₹1,563.30 via payment_link — seal `f7e422429b71` — evidence: `rzp plink_b06c1b05f06ec8 status=expired amount_paid=0 expected>=156330 for pay_jRSxy7qfYro6uX`
- `pay_1okcRLOlqPYlob` ₹2,204.72 via payment_link — seal `69e2bdf32db2` — evidence: `rzp plink_105a5450cbd065 status=expired amount_paid=0 expected>=220472 for pay_1okcRLOlqPYlob`
- `pay_UlQseTbAG4FYpC` ₹266.90 via payment_link — seal `dcef86b36145` — evidence: `rzp plink_e0bd658fdda5bb status=expired amount_paid=0 expected>=26690 for pay_UlQseTbAG4FYpC`
- `pay_OQ4saXtJsOxE41` ₹2,588.04 via payment_link — seal `08406889be7a` — evidence: `rzp plink_4d84e6fe25c51e status=created amount_paid=0 expected>=258804 for pay_OQ4saXtJsOxE41`
- `pay_mWbrdUNcfnKcTU` ₹711.85 via payment_link — seal `ee156ed70e83` — evidence: `rzp plink_aaaac70d5a76ff status=created amount_paid=0 expected>=71185 for pay_mWbrdUNcfnKcTU`
- `pay_tUDb4imvn67tyI` ₹2,726.21 via payment_link — seal `a5ea507762d4` — evidence: `rzp plink_dbaee719b9de33 status=created amount_paid=0 expected>=272621 for pay_tUDb4imvn67tyI`

## Exceptions — every record that did not end in verified money

126 of 240 records in this run need a human.

| Payment | Amount | Outcome | Action | Attempts | Why |
|---|---|---|---|---|---|
| `pay_I9M2BNfvUhzDt3` | ₹3,112.57 | failed_verification | payment_link | 1 | cause mandate_expired; mandate_expired: the mandate cannot be re-presented, only re-authorised; rzp plink_f219da64d2818f status=expired amount_paid=0 expected>=311257 for pay_I9M2BNfvUhzDt3 |
| `pay_2NLUFRoPwFyIkY` | ₹12,849.64 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 7.3d; rzp pay_2NLUFRoPwFyIkY status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_Cn7XbDBgPQcE53` | ₹360.56 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 4.8d; rzp pay_Cn7XbDBgPQcE53 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_9iTFdREf99X45E` | ₹777.27 | failed_verification | payment_link | 1 | cause mandate_expired; mandate_expired: the mandate cannot be re-presented, only re-authorised; rzp plink_12bfc651547e53 status=expired amount_paid=0 expected>=77727 for pay_9iTFdREf99X45E |
| `pay_p5OCUaqMxtfM8T` | ₹207.08 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 12.5d; rzp pay_p5OCUaqMxtfM8T status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_AUqLTMxhDGYinF` | ₹5,570.58 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 11.6d; rzp pay_AUqLTMxhDGYinF status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_Rg5Gex7MH68dD5` | ₹581.30 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 10.3d; rzp pay_Rg5Gex7MH68dD5 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_PYWfLA9cbmyzyY` | ₹179.37 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 9.8d; rzp pay_PYWfLA9cbmyzyY status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_pTACJmaf3IOoBA` | ₹1,162.73 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_b49cb54e7a62de status=expired amount_paid=0 expected>=116273 for pay_pTACJmaf3IOoBA |
| `pay_4GloMZgnoZmfDm` | ₹933.14 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 9.1d; rzp pay_4GloMZgnoZmfDm status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_YlX0580hdgAB7O` | ₹2,770.94 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 13.5d; rzp pay_YlX0580hdgAB7O status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_0JJPUgJUL8tG7G` | ₹2,381.37 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_92e149eff645d4 status=expired amount_paid=0 expected>=238137 for pay_0JJPUgJUL8tG7G |
| `pay_kOLHaQr3PYsJ0d` | ₹626.96 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_93a12c7a2918d6 status=expired amount_paid=0 expected>=62696 for pay_kOLHaQr3PYsJ0d |
| `pay_H9WDRYAZarVQNt` | ₹6,342.26 | failed_verification | payment_link | 1 | cause mandate_expired; mandate_expired: the mandate cannot be re-presented, only re-authorised; rzp plink_5da743adf3e20d status=expired amount_paid=0 expected>=634226 for pay_H9WDRYAZarVQNt |
| `pay_xxWoTemF3JSXFj` | ₹595.57 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_352fd732f0bdeb status=expired amount_paid=0 expected>=59557 for pay_xxWoTemF3JSXFj |
| `pay_QOIeDcIeeh1A0d` | ₹1,554.50 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_6e0ce08cb96fda status=expired amount_paid=0 expected>=155450 for pay_QOIeDcIeeh1A0d |
| `pay_zwiPSaTan5DjCH` | ₹2,218.99 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 13.7d; rzp pay_zwiPSaTan5DjCH status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_a3Xql3yRAQaky3` | ₹417.06 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 9.6d; rzp pay_a3Xql3yRAQaky3 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_DlYH7Pin7pYbJ7` | ₹2,406.77 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 8.4d old: past nudging, issue a fresh link; rzp plink_1e6b13184d9fc9 status=expired amount_paid=0 expected>=240677 for pay_DlYH7Pin7pYbJ7 |
| `pay_995GR3DtS8AyVI` | ₹2,244.05 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 4.0d; rzp pay_995GR3DtS8AyVI status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_EafBI8w6ny22Cn` | ₹8,779.00 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_f7e27266f26709 status=expired amount_paid=0 expected>=877900 for pay_EafBI8w6ny22Cn |
| `pay_LmBNYvCDONJkKA` | ₹585.32 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 5.5d; rzp pay_LmBNYvCDONJkKA status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_0jsPaqVAzwRC0l` | ₹191.40 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 9.8d; rzp pay_0jsPaqVAzwRC0l status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_46eeJSkEqKb8FC` | ₹608.46 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_d396347a8adfed status=expired amount_paid=0 expected>=60846 for pay_46eeJSkEqKb8FC |
| `pay_H5pPLbzkHBGxLi` | ₹9,741.86 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_H5pPLbzkHBGxLi' AND kind = 'escalate' |
| `pay_hkiolUtPsvwTv8` | ₹1,506.97 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_d8b055263b1b43 status=expired amount_paid=0 expected>=150697 for pay_hkiolUtPsvwTv8 |
| `pay_pFmCsZiqbpcjdo` | ₹2,947.93 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_pFmCsZiqbpcjdo' AND kind = 'escalate' |
| `pay_ycnz31CXzyHJPG` | ₹1,573.76 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 5.3d; rzp pay_ycnz31CXzyHJPG status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_ptYCqivvHNEyGF` | ₹1,547.80 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_ptYCqivvHNEyGF' AND kind = 'escalate' |
| `pay_NzJ4MGFw6ZoP4q` | ₹1,209.88 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 5.5d; rzp pay_NzJ4MGFw6ZoP4q status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_zKgAK6cyPVGi1f` | ₹1,486.85 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 13.8d; rzp pay_zKgAK6cyPVGi1f status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_HZ0w0YeU1sItZ5` | ₹851.09 | failed_verification | payment_link | 1 | cause mandate_expired; mandate_expired: the mandate cannot be re-presented, only re-authorised; rzp plink_69ce72e4b84664 status=expired amount_paid=0 expected>=85109 for pay_HZ0w0YeU1sItZ5 |
| `pay_NFp8xWrEzUAnIR` | ₹1,607.05 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 11.0d; rzp pay_NFp8xWrEzUAnIR status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_aBsvV1W2eFUT38` | ₹1,301.57 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_d18f88f1c12c56 status=expired amount_paid=0 expected>=130157 for pay_aBsvV1W2eFUT38 |
| `pay_6RYV7F1nmotIEE` | ₹776.81 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 2.6d; rzp pay_6RYV7F1nmotIEE status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_FHdKObHEWd6iEN` | ₹1,136.40 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_f6cdebceef7209 status=expired amount_paid=0 expected>=113640 for pay_FHdKObHEWd6iEN |
| `pay_7TZVpBXKzAlPci` | ₹320.67 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 9.4d; rzp pay_7TZVpBXKzAlPci status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_EXSprkbegqWgib` | ₹6,236.70 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 4.9d; rzp pay_EXSprkbegqWgib status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_rXeW9n2Hf2modc` | ₹467.13 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_c126632a139571 status=expired amount_paid=0 expected>=46713 for pay_rXeW9n2Hf2modc |
| `pay_BxzFPKK3wOBFFM` | ₹781.35 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_c031b0dfd415d2 status=expired amount_paid=0 expected>=78135 for pay_BxzFPKK3wOBFFM |
| `pay_cdymzdaA5N0cuf` | ₹320.89 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_cdymzdaA5N0cuf' AND kind = 'escalate' |
| `pay_BTws1qdTEombEx` | ₹1,678.95 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 9.7d; rzp pay_BTws1qdTEombEx status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_grTylZOXyrW3ci` | ₹6,209.64 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_cd16cbdbd99b51 status=expired amount_paid=0 expected>=620964 for pay_grTylZOXyrW3ci |
| `pay_VwPCC9OT26SmYR` | ₹834.21 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 4.5d; rzp pay_VwPCC9OT26SmYR status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_kasaFgywWNuxN2` | ₹2,957.67 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 12.9d; rzp pay_kasaFgywWNuxN2 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_InxalQRafdFAVs` | ₹6,725.51 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_c6c3c949e69def status=expired amount_paid=0 expected>=672551 for pay_InxalQRafdFAVs |
| `pay_bxjb2lUY614iIK` | ₹12,253.04 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 4.6d; rzp pay_bxjb2lUY614iIK status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_jh719ezCaFZSfr` | ₹494.52 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 11.1d; rzp pay_jh719ezCaFZSfr status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_Sl1t6V01QfbBFx` | ₹4,012.48 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_Sl1t6V01QfbBFx' AND kind = 'escalate' |
| `pay_4xquOcz75JqiZK` | ₹6,263.37 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 7.8d; rzp pay_4xquOcz75JqiZK status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_7pKLLSsrkaMEfp` | ₹563.23 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 7.6d; rzp pay_7pKLLSsrkaMEfp status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_301baT8LJR50U0` | ₹542.64 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_36c0582e19df54 status=expired amount_paid=0 expected>=54264 for pay_301baT8LJR50U0 |
| `pay_E46BmOFzcOLTnl` | ₹1,653.55 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_E46BmOFzcOLTnl' AND kind = 'escalate' |
| `pay_Iii3rKpF8aczsb` | ₹1,452.40 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_Iii3rKpF8aczsb' AND kind = 'escalate' |
| `pay_XdEnqJitG01DPF` | ₹3,409.01 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_9c3ce3ba58609d status=expired amount_paid=0 expected>=340901 for pay_XdEnqJitG01DPF |
| `pay_yNDN739fHq3aAQ` | ₹868.19 | unresolved | nudge | 1 | cause checkout_dropoff; checkout_dropoff 20h old: remind while the intent is warm; 1 row(s) in attempts where payment_id = 'pay_yNDN739fHq3aAQ' AND kind = 'nudge' |
| `pay_WxFBfnyilER8bk` | ₹587.67 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_WxFBfnyilER8bk' AND kind = 'escalate' |
| `pay_XZ3Q8396PylM9o` | ₹2,163.39 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_f000116f313be0 status=expired amount_paid=0 expected>=216339 for pay_XZ3Q8396PylM9o |
| `pay_fUiCFqEiKWw3cU` | ₹968.14 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 3.0d; rzp pay_fUiCFqEiKWw3cU status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_GmyPq3HIeU69bx` | ₹724.71 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 5.7d; rzp pay_GmyPq3HIeU69bx status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_7zkjAXQmEhXeZG` | ₹484.77 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_24eadb3f251dd0 status=expired amount_paid=0 expected>=48477 for pay_7zkjAXQmEhXeZG |
| `pay_8mdnhr6AT2DwBo` | ₹341.19 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_b1803d57406d26 status=expired amount_paid=0 expected>=34119 for pay_8mdnhr6AT2DwBo |
| `pay_UJISrjHxfIyyN6` | ₹4,478.62 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 12.0d; rzp pay_UJISrjHxfIyyN6 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_QGfvJa9dX03XHn` | ₹11,920.64 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 5.9d; rzp pay_QGfvJa9dX03XHn status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_Fn9TMXpqcaYNTH` | ₹1,492.72 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_a4c313fa72f21f status=created amount_paid=0 expected>=149272 for pay_Fn9TMXpqcaYNTH |
| `pay_qX4ySEioNCeCtm` | ₹1,771.57 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_586d4b1e99b7c1 status=expired amount_paid=0 expected>=177157 for pay_qX4ySEioNCeCtm |
| `pay_nidWr5F1jukqno` | ₹6,799.52 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 12.0d; rzp pay_nidWr5F1jukqno status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_e4PPqOPPMgIqe1` | ₹1,552.22 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 5.4d; rzp pay_e4PPqOPPMgIqe1 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_H0wulG7GwsTqZu` | ₹4,445.38 | unresolved | nudge | 1 | cause checkout_dropoff; checkout_dropoff 9h old: remind while the intent is warm; 1 row(s) in attempts where payment_id = 'pay_H0wulG7GwsTqZu' AND kind = 'nudge' |
| `pay_jJDs1p44Opbz23` | ₹1,168.25 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 11.2d; rzp pay_jJDs1p44Opbz23 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_byLsU67UlGZmnV` | ₹3,762.58 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 2.8d; rzp pay_byLsU67UlGZmnV status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_c0S9vYwwiru70l` | ₹1,561.27 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_c0S9vYwwiru70l' AND kind = 'escalate' |
| `pay_zBDLSy17fJ3ohS` | ₹4,330.02 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_3bae3838b93b4f status=expired amount_paid=0 expected>=433002 for pay_zBDLSy17fJ3ohS |
| `pay_Jg3uYdR7wqStex` | ₹14,699.00 | failed_verification | payment_link | 1 | cause mandate_expired; mandate_expired: the mandate cannot be re-presented, only re-authorised; rzp plink_d0146ed9f58c16 status=expired amount_paid=0 expected>=1469900 for pay_Jg3uYdR7wqStex |
| `pay_bTlV87tzEHVHa9` | ₹3,211.65 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_0ae62b6e634426 status=created amount_paid=0 expected>=321165 for pay_bTlV87tzEHVHa9 |
| `pay_llUk4Yu62UsyIx` | ₹1,839.11 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 9.1d; rzp pay_llUk4Yu62UsyIx status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_B0TDQOGb5nOOGk` | ₹135.72 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 12.1d old: past nudging, issue a fresh link; rzp plink_f5946ae90ce271 status=expired amount_paid=0 expected>=13572 for pay_B0TDQOGb5nOOGk |
| `pay_I6c9ALhLlygoMj` | ₹677.91 | failed_verification | payment_link | 1 | cause unknown; unknown decline: a link is the zero-cost rail that cannot re-present a blocked card; rzp plink_45273f25f20ef8 status=expired amount_paid=0 expected>=67791 for pay_I6c9ALhLlygoMj |
| `pay_s1rCefoKzSeE2b` | ₹4,013.11 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_290ae85e07591d status=expired amount_paid=0 expected>=401311 for pay_s1rCefoKzSeE2b |
| `pay_3TZeXfMgOeLuh6` | ₹11,798.23 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_9d1664d030ea9c status=created amount_paid=0 expected>=1179823 for pay_3TZeXfMgOeLuh6 |
| `pay_ilAlmvgHNoEGPx` | ₹1,254.88 | unresolved | nudge | 1 | cause checkout_dropoff; checkout_dropoff 10h old: remind while the intent is warm; 1 row(s) in attempts where payment_id = 'pay_ilAlmvgHNoEGPx' AND kind = 'nudge' |
| `pay_OUISqXTkmB2SmQ` | ₹367.28 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_OUISqXTkmB2SmQ' AND kind = 'escalate' |
| `pay_XGmCXgBJVqFwL0` | ₹226.14 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_019c03f224964d status=created amount_paid=0 expected>=22614 for pay_XGmCXgBJVqFwL0 |
| `pay_W9T4wztIhPSNi4` | ₹6,609.94 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_e7115544e13ae8 status=expired amount_paid=0 expected>=660994 for pay_W9T4wztIhPSNi4 |
| `pay_CpW5SaThRpZrSc` | ₹181.08 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_02fab50699c5f6 status=expired amount_paid=0 expected>=18108 for pay_CpW5SaThRpZrSc |
| `pay_OnBFreGd6YiafC` | ₹239.98 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_OnBFreGd6YiafC' AND kind = 'escalate' |
| `pay_kNrKqms6SqY3zv` | ₹268.95 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 1.5d; rzp pay_kNrKqms6SqY3zv status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_Ip4UpL9izGoAlx` | ₹1,582.75 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 11.4d; rzp pay_Ip4UpL9izGoAlx status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_7MCvKuAHWFdVte` | ₹5,657.36 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 9.0d; rzp pay_7MCvKuAHWFdVte status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_YefNQ00rqfjpAb` | ₹1,945.58 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_f2286f046dc109 status=created amount_paid=0 expected>=194558 for pay_YefNQ00rqfjpAb |
| `pay_JppOdN2nqmD2wf` | ₹1,282.14 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_b2bbad988469f4 status=created amount_paid=0 expected>=128214 for pay_JppOdN2nqmD2wf |
| `pay_r5Jn7X2xTIxZVc` | ₹2,519.98 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_e26a7c5b1a61a2 status=expired amount_paid=0 expected>=251998 for pay_r5Jn7X2xTIxZVc |
| `pay_rAz3Wgo5ofveCh` | ₹2,325.97 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_807758f1fb2259 status=expired amount_paid=0 expected>=232597 for pay_rAz3Wgo5ofveCh |
| `pay_Qwvl59SY7SD7T4` | ₹565.43 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 10.5d old: past nudging, issue a fresh link; rzp plink_cf41aa6e7ca5c9 status=expired amount_paid=0 expected>=56543 for pay_Qwvl59SY7SD7T4 |
| `pay_FdX9CLEi7wGhW8` | ₹687.13 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_7599c3bfe75d1a status=expired amount_paid=0 expected>=68713 for pay_FdX9CLEi7wGhW8 |
| `pay_El0BLoUTAAYgZ8` | ₹1,346.08 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 11.8d old: past nudging, issue a fresh link; rzp plink_864dfcd23accfa status=expired amount_paid=0 expected>=134608 for pay_El0BLoUTAAYgZ8 |
| `pay_ec75ZeGugK2CLd` | ₹289.83 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 3.2d; rzp pay_ec75ZeGugK2CLd status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_bbaWw2SsNAqwU9` | ₹2,753.28 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_bbaWw2SsNAqwU9' AND kind = 'escalate' |
| `pay_iUOxwIwaJHQZ9r` | ₹2,279.73 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_9ace70e97f1f20 status=expired amount_paid=0 expected>=227973 for pay_iUOxwIwaJHQZ9r |
| `pay_8d1Yax8urz47gY` | ₹3,842.21 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_99b81e8b95d18d status=expired amount_paid=0 expected>=384221 for pay_8d1Yax8urz47gY |
| `pay_uG613juRg5xNWZ` | ₹34,076.41 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_120e0b7bf956ab status=created amount_paid=0 expected>=3407641 for pay_uG613juRg5xNWZ |
| `pay_oz3X9YtzWaWVZ0` | ₹2,069.05 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_1731187f0a840c status=expired amount_paid=0 expected>=206905 for pay_oz3X9YtzWaWVZ0 |
| `pay_jqi4A8mZ43kAmZ` | ₹648.28 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_37980946ac55c5 status=expired amount_paid=0 expected>=64828 for pay_jqi4A8mZ43kAmZ |
| `pay_vrgjLnY8e3eRt8` | ₹2,556.33 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_23aea8b559d6aa status=expired amount_paid=0 expected>=255633 for pay_vrgjLnY8e3eRt8 |
| `pay_4qXuG18TVf1uWy` | ₹1,676.56 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 4.8d; rzp pay_4qXuG18TVf1uWy status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_SCo6J5RgryT1F3` | ₹1,267.84 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 13.7d old: past nudging, issue a fresh link; rzp plink_7fd51803babbc0 status=expired amount_paid=0 expected>=126784 for pay_SCo6J5RgryT1F3 |
| `pay_5mwsYea3YTwIQV` | ₹1,526.81 | unresolved | nudge | 1 | cause checkout_dropoff; checkout_dropoff 8h old: remind while the intent is warm; 1 row(s) in attempts where payment_id = 'pay_5mwsYea3YTwIQV' AND kind = 'nudge' |
| `pay_1d6wiWGJVe3FjM` | ₹26,614.63 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_89ad2d8c2232f3 status=expired amount_paid=0 expected>=2661463 for pay_1d6wiWGJVe3FjM |
| `pay_PZZrRWfOaufDVj` | ₹529.79 | failed_verification | payment_link | 1 | cause mandate_expired; mandate_expired: the mandate cannot be re-presented, only re-authorised; rzp plink_8aa7e926ceee45 status=expired amount_paid=0 expected>=52979 for pay_PZZrRWfOaufDVj |
| `pay_GnUqSLQss4ZEyP` | ₹3,406.84 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_GnUqSLQss4ZEyP' AND kind = 'escalate' |
| `pay_59d79lQJfgvI78` | ₹3,083.50 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 6.6d; rzp pay_59d79lQJfgvI78 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_vOAiJfdON1G1io` | ₹6,973.29 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 5.8d; rzp pay_vOAiJfdON1G1io status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_y4ODIohWsNlZIw` | ₹641.08 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_y4ODIohWsNlZIw' AND kind = 'escalate' |
| `pay_z5IazTPBhiNQnK` | ₹558.11 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 8.3d old: past nudging, issue a fresh link; rzp plink_41f24ba082b6c4 status=expired amount_paid=0 expected>=55811 for pay_z5IazTPBhiNQnK |
| `pay_edBb4AnFgtDtHU` | ₹467.89 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 1.8d old: past nudging, issue a fresh link; rzp plink_914470823e66cc status=expired amount_paid=0 expected>=46789 for pay_edBb4AnFgtDtHU |
| `pay_aThlbRBk2gpSuS` | ₹631.79 | failed_verification | payment_link | 1 | cause unknown; unknown decline: a link is the zero-cost rail that cannot re-present a blocked card; rzp plink_979771da21eee3 status=expired amount_paid=0 expected>=63179 for pay_aThlbRBk2gpSuS |
| `pay_bh9UAY2Fgl0Ul7` | ₹813.83 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 6.0d; rzp pay_bh9UAY2Fgl0Ul7 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_5OfSB6Sm2wIY3W` | ₹1,960.75 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 2.4d; rzp pay_5OfSB6Sm2wIY3W status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_jRSxy7qfYro6uX` | ₹1,563.30 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_b06c1b05f06ec8 status=expired amount_paid=0 expected>=156330 for pay_jRSxy7qfYro6uX |
| `pay_1okcRLOlqPYlob` | ₹2,204.72 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_105a5450cbd065 status=expired amount_paid=0 expected>=220472 for pay_1okcRLOlqPYlob |
| `pay_NrXcTOSQL2Xiyq` | ₹99.00 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_NrXcTOSQL2Xiyq' AND kind = 'escalate' |
| `pay_UlQseTbAG4FYpC` | ₹266.90 | failed_verification | payment_link | 1 | cause mandate_expired; mandate_expired: the mandate cannot be re-presented, only re-authorised; rzp plink_e0bd658fdda5bb status=expired amount_paid=0 expected>=26690 for pay_UlQseTbAG4FYpC |
| `pay_OQ4saXtJsOxE41` | ₹2,588.04 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 3.8d old: past nudging, issue a fresh link; rzp plink_4d84e6fe25c51e status=created amount_paid=0 expected>=258804 for pay_OQ4saXtJsOxE41 |
| `pay_7W3qE3Q8I3ffLe` | ₹2,588.26 | unresolved | nudge | 1 | cause checkout_dropoff; checkout_dropoff 9h old: remind while the intent is warm; 1 row(s) in attempts where payment_id = 'pay_7W3qE3Q8I3ffLe' AND kind = 'nudge' |
| `pay_mWbrdUNcfnKcTU` | ₹711.85 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 2.4d old: past nudging, issue a fresh link; rzp plink_aaaac70d5a76ff status=created amount_paid=0 expected>=71185 for pay_mWbrdUNcfnKcTU |
| `pay_tUDb4imvn67tyI` | ₹2,726.21 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_dbaee719b9de33 status=created amount_paid=0 expected>=272621 for pay_tUDb4imvn67tyI |

