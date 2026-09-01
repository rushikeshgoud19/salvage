# salvage — verified recovery results

**Every metric on this page is computed on the `holdout` split.** Nothing here is a training number, and nothing here counts a rupee that a stepproof seal did not confirm arrived.

## AI judgment

Root cause settled deterministically on 46 of 48 records (95.8%); the model was invoked on the remaining 4.2% (2 records), where the gateway reason was absent or ambiguous.

The model reads unstructured context and returns a typed diagnostic. It never chooses an action, never touches money, and its prose is never used as evidence.

## Headline

| Measure | Value |
|---|---|
| Records at risk | 48 |
| Value at risk | ₹111,313.68 |
| Recovered, seal-verified | 20 |
| **Value recovered** | **₹59,031.02** |
| **Recovery rate by value** | **53.0%** |
| Recovery rate by count | 41.7% |
| Interventions | 47 |
| Intervention precision | 42.6% |
| False positives (would have self-healed) | 5 (10.6%) |
| False-positive cost | ₹0.25 |
| Suppressed by policy | 1 |
| Unresolved | 4 |
| **Failed verification** | **23** |
| **Verification gap** | **₹43,996.41** |

Calibration: 53.0% sits inside the 45–65% band published for reason-specific smart retries, and above the 20–30% a generic daily retry earns (Contract §10.2).

The verification gap is ₹43,996.41 across 23 records: money an agent that trusted its own success claim would have booked as recovered and never received.

## The same run, scored the way everyone else scores it

Identical records, identical policy, identical provider responses. Only the scoring rule changes: the baseline books a recovery when a money-rail action returned success, which is what an agent without a verification layer has to do. Outreach is never counted for it -- a strawman would prove nothing.

| | Reports | Rate |
|---|---|---|
| Naive agent (trusts the API) | ₹103,027.43 | 92.6% |
| **salvage (seal-verified)** | **₹59,031.02** | **53.0%** |
| **Fiction** | **₹43,996.41** | **42.7% of the claim** |

The naive agent books 43 recoveries. 20 of them actually happened. It is not lying and it is not badly built -- it simply has no way to find out, because every layer beneath it honestly reported success.

## Audit trail

- Hash chain: **INTACT** — chain intact (230 records)
- Seals written: 230
- Seals that failed verification: 108
- Seals left unverified: 0

## Root-cause accuracy

The settled root cause matched the ground-truth label on 48 of 48 (100.0%) scored records. Accuracy is reported here and not in `Metrics`, which stays frozen at Contract §7.

## Failed verification — claimed, not confirmed

Each line quotes the sealed observation verbatim. These are the records where the action reported success and the payment state disagreed.

- `pay_I9M2BNfvUhzDt3` ₹3,112.57 via payment_link — seal `074a37a9fd7d` — evidence: `rzp plink_f219da64d2818f status=expired amount_paid=0 expected>=311257 for pay_I9M2BNfvUhzDt3`
- `pay_2NLUFRoPwFyIkY` ₹12,849.64 via retry — seal `9743b2047374` — evidence: `rzp pay_2NLUFRoPwFyIkY status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_Cn7XbDBgPQcE53` ₹360.56 via retry — seal `25b5936b9856` — evidence: `rzp pay_Cn7XbDBgPQcE53 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_9iTFdREf99X45E` ₹777.27 via payment_link — seal `ab25dc02b9db` — evidence: `rzp plink_12bfc651547e53 status=expired amount_paid=0 expected>=77727 for pay_9iTFdREf99X45E`
- `pay_p5OCUaqMxtfM8T` ₹207.08 via retry — seal `8049e22dc543` — evidence: `rzp pay_p5OCUaqMxtfM8T status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_AUqLTMxhDGYinF` ₹5,570.58 via retry — seal `decd4a1e7b37` — evidence: `rzp pay_AUqLTMxhDGYinF status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_Rg5Gex7MH68dD5` ₹581.30 via retry — seal `345d892822b1` — evidence: `rzp pay_Rg5Gex7MH68dD5 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_PYWfLA9cbmyzyY` ₹179.37 via retry — seal `e3510e8fd4f6` — evidence: `rzp pay_PYWfLA9cbmyzyY status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_pTACJmaf3IOoBA` ₹1,162.73 via payment_link — seal `2c4cdf7206af` — evidence: `rzp plink_b49cb54e7a62de status=expired amount_paid=0 expected>=116273 for pay_pTACJmaf3IOoBA`
- `pay_4GloMZgnoZmfDm` ₹933.14 via retry — seal `06cb67cc3759` — evidence: `rzp pay_4GloMZgnoZmfDm status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_YlX0580hdgAB7O` ₹2,770.94 via retry — seal `26f1524f6411` — evidence: `rzp pay_YlX0580hdgAB7O status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_0JJPUgJUL8tG7G` ₹2,381.37 via payment_link — seal `ff7557ddc728` — evidence: `rzp plink_92e149eff645d4 status=expired amount_paid=0 expected>=238137 for pay_0JJPUgJUL8tG7G`
- `pay_kOLHaQr3PYsJ0d` ₹626.96 via payment_link — seal `d0aec65c6f45` — evidence: `rzp plink_93a12c7a2918d6 status=expired amount_paid=0 expected>=62696 for pay_kOLHaQr3PYsJ0d`
- `pay_H9WDRYAZarVQNt` ₹6,342.26 via payment_link — seal `2d8edd8a0838` — evidence: `rzp plink_5da743adf3e20d status=expired amount_paid=0 expected>=634226 for pay_H9WDRYAZarVQNt`
- `pay_xxWoTemF3JSXFj` ₹595.57 via payment_link — seal `9c1741298c32` — evidence: `rzp plink_352fd732f0bdeb status=expired amount_paid=0 expected>=59557 for pay_xxWoTemF3JSXFj`
- `pay_QOIeDcIeeh1A0d` ₹1,554.50 via payment_link — seal `63d2a48a75cb` — evidence: `rzp plink_6e0ce08cb96fda status=expired amount_paid=0 expected>=155450 for pay_QOIeDcIeeh1A0d`
- `pay_zwiPSaTan5DjCH` ₹2,218.99 via retry — seal `92718fe1ae19` — evidence: `rzp pay_zwiPSaTan5DjCH status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_a3Xql3yRAQaky3` ₹417.06 via retry — seal `ab95256d7a3b` — evidence: `rzp pay_a3Xql3yRAQaky3 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_DlYH7Pin7pYbJ7` ₹2,406.77 via payment_link — seal `c1b51753adde` — evidence: `rzp plink_1e6b13184d9fc9 status=expired amount_paid=0 expected>=240677 for pay_DlYH7Pin7pYbJ7`
- `pay_Inbffbw6RWCZRL` ₹1,886.10 via payment_link — seal `191077818acc` — evidence: `rzp plink_81cdbde40579e4 status=expired amount_paid=0 expected>=188610 for pay_Inbffbw6RWCZRL`
- `pay_ZIk1JjuKz6Ya0g` ₹4,455.02 via retry — seal `bc928ecca855` — evidence: `rzp pay_ZIk1JjuKz6Ya0g status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_NfXkAV1OieR9Sv` ₹3,541.67 via retry — seal `b739c1151ae0` — evidence: `rzp pay_NfXkAV1OieR9Sv status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_e7jZw2lXccsSYi` ₹565.17 via payment_link — seal `92cb4b34dbb0` — evidence: `rzp plink_7b66ae10580ef0 status=expired amount_paid=0 expected>=56517 for pay_e7jZw2lXccsSYi`
- `pay_SETOHsRZ4w21IR` ₹2,271.24 via payment_link — seal `cab8352b6bc8` — evidence: `rzp plink_3f1ce059021ca0 status=created amount_paid=0 expected>=227124 for pay_SETOHsRZ4w21IR`
- `pay_nhPDWZMTIrpOOf` ₹537.16 via payment_link — seal `56308c9bd047` — evidence: `rzp plink_d9830e739f9e90 status=created amount_paid=0 expected>=53716 for pay_nhPDWZMTIrpOOf`
- `pay_d8euUtQn7ewTWF` ₹587.61 via retry — seal `e53af10ff61e` — evidence: `rzp pay_d8euUtQn7ewTWF status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_46eeJSkEqKb8FC` ₹608.46 via payment_link — seal `7f19c4a65193` — evidence: `rzp plink_d396347a8adfed status=expired amount_paid=0 expected>=60846 for pay_46eeJSkEqKb8FC`
- `pay_Mt7lEy2VILh2n5` ₹1,394.01 via retry — seal `1059054a4ef2` — evidence: `rzp pay_Mt7lEy2VILh2n5 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_hkiolUtPsvwTv8` ₹1,506.97 via payment_link — seal `0da04fec6c0a` — evidence: `rzp plink_d8b055263b1b43 status=expired amount_paid=0 expected>=150697 for pay_hkiolUtPsvwTv8`
- `pay_ycnz31CXzyHJPG` ₹1,573.76 via retry — seal `3e4ee87d9f71` — evidence: `rzp pay_ycnz31CXzyHJPG status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_NzJ4MGFw6ZoP4q` ₹1,209.88 via retry — seal `8e2355e5e8a1` — evidence: `rzp pay_NzJ4MGFw6ZoP4q status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_HZ0w0YeU1sItZ5` ₹851.09 via payment_link — seal `4630a65a4e0c` — evidence: `rzp plink_69ce72e4b84664 status=expired amount_paid=0 expected>=85109 for pay_HZ0w0YeU1sItZ5`
- `pay_NFp8xWrEzUAnIR` ₹1,607.05 via retry — seal `d4ef8601b462` — evidence: `rzp pay_NFp8xWrEzUAnIR status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_aBsvV1W2eFUT38` ₹1,301.57 via payment_link — seal `d27ed2edf739` — evidence: `rzp plink_d18f88f1c12c56 status=expired amount_paid=0 expected>=130157 for pay_aBsvV1W2eFUT38`
- `pay_6RYV7F1nmotIEE` ₹776.81 via retry — seal `4b3cefad86b3` — evidence: `rzp pay_6RYV7F1nmotIEE status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_FHdKObHEWd6iEN` ₹1,136.40 via payment_link — seal `c2f4654a223d` — evidence: `rzp plink_f6cdebceef7209 status=expired amount_paid=0 expected>=113640 for pay_FHdKObHEWd6iEN`
- `pay_7TZVpBXKzAlPci` ₹320.67 via retry — seal `35afee7f8b36` — evidence: `rzp pay_7TZVpBXKzAlPci status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_EXSprkbegqWgib` ₹6,236.70 via retry — seal `bc6d3ba10592` — evidence: `rzp pay_EXSprkbegqWgib status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_rXeW9n2Hf2modc` ₹467.13 via payment_link — seal `e08872d98d19` — evidence: `rzp plink_c126632a139571 status=expired amount_paid=0 expected>=46713 for pay_rXeW9n2Hf2modc`
- `pay_BxzFPKK3wOBFFM` ₹781.35 via payment_link — seal `908f991db6c2` — evidence: `rzp plink_c031b0dfd415d2 status=expired amount_paid=0 expected>=78135 for pay_BxzFPKK3wOBFFM`
- `pay_BTws1qdTEombEx` ₹1,678.95 via retry — seal `e6dc33d34698` — evidence: `rzp pay_BTws1qdTEombEx status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_grTylZOXyrW3ci` ₹6,209.64 via payment_link — seal `b8579c946a82` — evidence: `rzp plink_cd16cbdbd99b51 status=expired amount_paid=0 expected>=620964 for pay_grTylZOXyrW3ci`
- `pay_VwPCC9OT26SmYR` ₹834.21 via retry — seal `11ae0d3fc0ee` — evidence: `rzp pay_VwPCC9OT26SmYR status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_kasaFgywWNuxN2` ₹2,957.67 via retry — seal `3937ba383230` — evidence: `rzp pay_kasaFgywWNuxN2 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_InxalQRafdFAVs` ₹6,725.51 via payment_link — seal `e71d52a6d2ae` — evidence: `rzp plink_c6c3c949e69def status=expired amount_paid=0 expected>=672551 for pay_InxalQRafdFAVs`
- `pay_bxjb2lUY614iIK` ₹12,253.04 via retry — seal `ef700a15f6e3` — evidence: `rzp pay_bxjb2lUY614iIK status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_jh719ezCaFZSfr` ₹494.52 via retry — seal `4e4d239aa99c` — evidence: `rzp pay_jh719ezCaFZSfr status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_4xquOcz75JqiZK` ₹6,263.37 via retry — seal `0620efa7d89c` — evidence: `rzp pay_4xquOcz75JqiZK status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_7pKLLSsrkaMEfp` ₹563.23 via retry — seal `541a987857ee` — evidence: `rzp pay_7pKLLSsrkaMEfp status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_301baT8LJR50U0` ₹542.64 via payment_link — seal `6917db2fee40` — evidence: `rzp plink_36c0582e19df54 status=expired amount_paid=0 expected>=54264 for pay_301baT8LJR50U0`
- `pay_XdEnqJitG01DPF` ₹3,409.01 via payment_link — seal `c69ebedc7533` — evidence: `rzp plink_9c3ce3ba58609d status=expired amount_paid=0 expected>=340901 for pay_XdEnqJitG01DPF`
- `pay_yNDN739fHq3aAQ` ₹868.19 via payment_link — seal `c8e042470246` — evidence: `rzp plink_ac222a8b2b0a68 status=created amount_paid=0 expected>=86819 for pay_yNDN739fHq3aAQ`
- `pay_XZ3Q8396PylM9o` ₹2,163.39 via payment_link — seal `b0d4b98c29f7` — evidence: `rzp plink_f000116f313be0 status=expired amount_paid=0 expected>=216339 for pay_XZ3Q8396PylM9o`
- `pay_fUiCFqEiKWw3cU` ₹968.14 via retry — seal `11e26a51d39d` — evidence: `rzp pay_fUiCFqEiKWw3cU status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_GmyPq3HIeU69bx` ₹724.71 via retry — seal `c6845235fbed` — evidence: `rzp pay_GmyPq3HIeU69bx status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_7zkjAXQmEhXeZG` ₹484.77 via payment_link — seal `7141d514b7d8` — evidence: `rzp plink_24eadb3f251dd0 status=expired amount_paid=0 expected>=48477 for pay_7zkjAXQmEhXeZG`
- `pay_8mdnhr6AT2DwBo` ₹341.19 via payment_link — seal `406dcfac4ab9` — evidence: `rzp plink_b1803d57406d26 status=expired amount_paid=0 expected>=34119 for pay_8mdnhr6AT2DwBo`
- `pay_UJISrjHxfIyyN6` ₹4,478.62 via retry — seal `3d6cf0e4162d` — evidence: `rzp pay_UJISrjHxfIyyN6 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_QGfvJa9dX03XHn` ₹11,920.64 via retry — seal `529af128245b` — evidence: `rzp pay_QGfvJa9dX03XHn status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_Fn9TMXpqcaYNTH` ₹1,492.72 via payment_link — seal `60c8c42c2d12` — evidence: `rzp plink_a4c313fa72f21f status=created amount_paid=0 expected>=149272 for pay_Fn9TMXpqcaYNTH`
- `pay_qX4ySEioNCeCtm` ₹1,771.57 via payment_link — seal `dd34e6fc160e` — evidence: `rzp plink_586d4b1e99b7c1 status=expired amount_paid=0 expected>=177157 for pay_qX4ySEioNCeCtm`
- `pay_nidWr5F1jukqno` ₹6,799.52 via retry — seal `678828aa4cfe` — evidence: `rzp pay_nidWr5F1jukqno status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_e4PPqOPPMgIqe1` ₹1,552.22 via retry — seal `6640b4c2f5f7` — evidence: `rzp pay_e4PPqOPPMgIqe1 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_jJDs1p44Opbz23` ₹1,168.25 via retry — seal `39f149ec5df8` — evidence: `rzp pay_jJDs1p44Opbz23 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_byLsU67UlGZmnV` ₹3,762.58 via retry — seal `8c84ae6cb2c7` — evidence: `rzp pay_byLsU67UlGZmnV status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_zBDLSy17fJ3ohS` ₹4,330.02 via payment_link — seal `8465f06e2a3c` — evidence: `rzp plink_3bae3838b93b4f status=expired amount_paid=0 expected>=433002 for pay_zBDLSy17fJ3ohS`
- `pay_Jg3uYdR7wqStex` ₹14,699.00 via payment_link — seal `7026e645d4b5` — evidence: `rzp plink_d0146ed9f58c16 status=expired amount_paid=0 expected>=1469900 for pay_Jg3uYdR7wqStex`
- `pay_bTlV87tzEHVHa9` ₹3,211.65 via payment_link — seal `34f5ef1b9191` — evidence: `rzp plink_0ae62b6e634426 status=created amount_paid=0 expected>=321165 for pay_bTlV87tzEHVHa9`
- `pay_llUk4Yu62UsyIx` ₹1,839.11 via retry — seal `57ffc79c87d9` — evidence: `rzp pay_llUk4Yu62UsyIx status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_B0TDQOGb5nOOGk` ₹135.72 via payment_link — seal `906f84d4d547` — evidence: `rzp plink_f5946ae90ce271 status=expired amount_paid=0 expected>=13572 for pay_B0TDQOGb5nOOGk`
- `pay_s1rCefoKzSeE2b` ₹4,013.11 via payment_link — seal `dcbb0e5c63ca` — evidence: `rzp plink_290ae85e07591d status=expired amount_paid=0 expected>=401311 for pay_s1rCefoKzSeE2b`
- `pay_3TZeXfMgOeLuh6` ₹11,798.23 via payment_link — seal `b9602a9ef359` — evidence: `rzp plink_9d1664d030ea9c status=created amount_paid=0 expected>=1179823 for pay_3TZeXfMgOeLuh6`
- `pay_XGmCXgBJVqFwL0` ₹226.14 via payment_link — seal `a48386aa5284` — evidence: `rzp plink_019c03f224964d status=created amount_paid=0 expected>=22614 for pay_XGmCXgBJVqFwL0`
- `pay_W9T4wztIhPSNi4` ₹6,609.94 via payment_link — seal `e6ebd33f866e` — evidence: `rzp plink_e7115544e13ae8 status=expired amount_paid=0 expected>=660994 for pay_W9T4wztIhPSNi4`
- `pay_CpW5SaThRpZrSc` ₹181.08 via payment_link — seal `5a4b2225c735` — evidence: `rzp plink_02fab50699c5f6 status=expired amount_paid=0 expected>=18108 for pay_CpW5SaThRpZrSc`
- `pay_kNrKqms6SqY3zv` ₹268.95 via retry — seal `4c7ad40423d8` — evidence: `rzp pay_kNrKqms6SqY3zv status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_Ip4UpL9izGoAlx` ₹1,582.75 via retry — seal `e318cf47a2b8` — evidence: `rzp pay_Ip4UpL9izGoAlx status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_7MCvKuAHWFdVte` ₹5,657.36 via retry — seal `f8c81fbff95f` — evidence: `rzp pay_7MCvKuAHWFdVte status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_YefNQ00rqfjpAb` ₹1,945.58 via payment_link — seal `81d1d7f365ae` — evidence: `rzp plink_f2286f046dc109 status=created amount_paid=0 expected>=194558 for pay_YefNQ00rqfjpAb`
- `pay_JppOdN2nqmD2wf` ₹1,282.14 via payment_link — seal `ebd95fd176e1` — evidence: `rzp plink_b2bbad988469f4 status=created amount_paid=0 expected>=128214 for pay_JppOdN2nqmD2wf`
- `pay_r5Jn7X2xTIxZVc` ₹2,519.98 via payment_link — seal `75f747efb089` — evidence: `rzp plink_e26a7c5b1a61a2 status=expired amount_paid=0 expected>=251998 for pay_r5Jn7X2xTIxZVc`
- `pay_rAz3Wgo5ofveCh` ₹2,325.97 via payment_link — seal `f1b0f2fd9cce` — evidence: `rzp plink_807758f1fb2259 status=expired amount_paid=0 expected>=232597 for pay_rAz3Wgo5ofveCh`
- `pay_Qwvl59SY7SD7T4` ₹565.43 via payment_link — seal `eaff0dbd43fe` — evidence: `rzp plink_cf41aa6e7ca5c9 status=expired amount_paid=0 expected>=56543 for pay_Qwvl59SY7SD7T4`
- `pay_FdX9CLEi7wGhW8` ₹687.13 via payment_link — seal `321e325e5ebb` — evidence: `rzp plink_7599c3bfe75d1a status=expired amount_paid=0 expected>=68713 for pay_FdX9CLEi7wGhW8`
- `pay_El0BLoUTAAYgZ8` ₹1,346.08 via payment_link — seal `cfbbb0846c1d` — evidence: `rzp plink_864dfcd23accfa status=expired amount_paid=0 expected>=134608 for pay_El0BLoUTAAYgZ8`
- `pay_ec75ZeGugK2CLd` ₹289.83 via retry — seal `072f30a9981a` — evidence: `rzp pay_ec75ZeGugK2CLd status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_iUOxwIwaJHQZ9r` ₹2,279.73 via payment_link — seal `7c67e6980a86` — evidence: `rzp plink_9ace70e97f1f20 status=expired amount_paid=0 expected>=227973 for pay_iUOxwIwaJHQZ9r`
- `pay_8d1Yax8urz47gY` ₹3,842.21 via payment_link — seal `2f2a81dd7fe3` — evidence: `rzp plink_99b81e8b95d18d status=expired amount_paid=0 expected>=384221 for pay_8d1Yax8urz47gY`
- `pay_uG613juRg5xNWZ` ₹34,076.41 via payment_link — seal `db6ac709ca12` — evidence: `rzp plink_120e0b7bf956ab status=created amount_paid=0 expected>=3407641 for pay_uG613juRg5xNWZ`
- `pay_oz3X9YtzWaWVZ0` ₹2,069.05 via payment_link — seal `6ecc8f2984fa` — evidence: `rzp plink_1731187f0a840c status=expired amount_paid=0 expected>=206905 for pay_oz3X9YtzWaWVZ0`
- `pay_jqi4A8mZ43kAmZ` ₹648.28 via payment_link — seal `29567425fa2c` — evidence: `rzp plink_37980946ac55c5 status=expired amount_paid=0 expected>=64828 for pay_jqi4A8mZ43kAmZ`
- `pay_vrgjLnY8e3eRt8` ₹2,556.33 via payment_link — seal `ad2fb9e61e5e` — evidence: `rzp plink_23aea8b559d6aa status=expired amount_paid=0 expected>=255633 for pay_vrgjLnY8e3eRt8`
- `pay_4qXuG18TVf1uWy` ₹1,676.56 via retry — seal `0790e547b541` — evidence: `rzp pay_4qXuG18TVf1uWy status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_SCo6J5RgryT1F3` ₹1,267.84 via payment_link — seal `e926b5f39a34` — evidence: `rzp plink_7fd51803babbc0 status=expired amount_paid=0 expected>=126784 for pay_SCo6J5RgryT1F3`
- `pay_1d6wiWGJVe3FjM` ₹26,614.63 via payment_link — seal `2242401142dd` — evidence: `rzp plink_89ad2d8c2232f3 status=expired amount_paid=0 expected>=2661463 for pay_1d6wiWGJVe3FjM`
- `pay_PZZrRWfOaufDVj` ₹529.79 via payment_link — seal `08b41e9aa5de` — evidence: `rzp plink_8aa7e926ceee45 status=expired amount_paid=0 expected>=52979 for pay_PZZrRWfOaufDVj`
- `pay_59d79lQJfgvI78` ₹3,083.50 via retry — seal `e9ba8d2cb62d` — evidence: `rzp pay_59d79lQJfgvI78 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_vOAiJfdON1G1io` ₹6,973.29 via retry — seal `04a8a26f8cf3` — evidence: `rzp pay_vOAiJfdON1G1io status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_z5IazTPBhiNQnK` ₹558.11 via payment_link — seal `7d37f85b7115` — evidence: `rzp plink_41f24ba082b6c4 status=expired amount_paid=0 expected>=55811 for pay_z5IazTPBhiNQnK`
- `pay_edBb4AnFgtDtHU` ₹467.89 via payment_link — seal `aea7883a66c8` — evidence: `rzp plink_914470823e66cc status=expired amount_paid=0 expected>=46789 for pay_edBb4AnFgtDtHU`
- `pay_bh9UAY2Fgl0Ul7` ₹813.83 via retry — seal `95939a99aabc` — evidence: `rzp pay_bh9UAY2Fgl0Ul7 status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_5OfSB6Sm2wIY3W` ₹1,960.75 via retry — seal `99a11c0dc1d9` — evidence: `rzp pay_5OfSB6Sm2wIY3W status=failed expected status=captured (amount not independently confirmed in offline mode)`
- `pay_jRSxy7qfYro6uX` ₹1,563.30 via payment_link — seal `f7e76c76c9d1` — evidence: `rzp plink_b06c1b05f06ec8 status=expired amount_paid=0 expected>=156330 for pay_jRSxy7qfYro6uX`
- `pay_1okcRLOlqPYlob` ₹2,204.72 via payment_link — seal `791677c689ca` — evidence: `rzp plink_105a5450cbd065 status=expired amount_paid=0 expected>=220472 for pay_1okcRLOlqPYlob`
- `pay_UlQseTbAG4FYpC` ₹266.90 via payment_link — seal `79e6fe79069a` — evidence: `rzp plink_e0bd658fdda5bb status=expired amount_paid=0 expected>=26690 for pay_UlQseTbAG4FYpC`
- `pay_OQ4saXtJsOxE41` ₹2,588.04 via payment_link — seal `116cac4bab0b` — evidence: `rzp plink_4d84e6fe25c51e status=created amount_paid=0 expected>=258804 for pay_OQ4saXtJsOxE41`
- `pay_mWbrdUNcfnKcTU` ₹711.85 via payment_link — seal `b9fe0aaea20d` — evidence: `rzp plink_aaaac70d5a76ff status=created amount_paid=0 expected>=71185 for pay_mWbrdUNcfnKcTU`
- `pay_tUDb4imvn67tyI` ₹2,726.21 via payment_link — seal `1f1496747a04` — evidence: `rzp plink_dbaee719b9de33 status=created amount_paid=0 expected>=272621 for pay_tUDb4imvn67tyI`

## Exceptions — every record that did not end in verified money

128 of 240 records in this run need a human.

| Payment | Amount | Outcome | Action | Attempts | Why |
|---|---|---|---|---|---|
| `pay_I9M2BNfvUhzDt3` | ₹3,112.57 | failed_verification | payment_link | 1 | cause mandate_expired; mandate_expired: the mandate cannot be re-presented, only re-authorised; rzp plink_f219da64d2818f status=expired amount_paid=0 expected>=311257 for pay_I9M2BNfvUhzDt3 |
| `pay_2NLUFRoPwFyIkY` | ₹12,849.64 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 7.6d; rzp pay_2NLUFRoPwFyIkY status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_Cn7XbDBgPQcE53` | ₹360.56 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 5.0d; rzp pay_Cn7XbDBgPQcE53 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_9iTFdREf99X45E` | ₹777.27 | failed_verification | payment_link | 1 | cause mandate_expired; mandate_expired: the mandate cannot be re-presented, only re-authorised; rzp plink_12bfc651547e53 status=expired amount_paid=0 expected>=77727 for pay_9iTFdREf99X45E |
| `pay_p5OCUaqMxtfM8T` | ₹207.08 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 12.7d; rzp pay_p5OCUaqMxtfM8T status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_AUqLTMxhDGYinF` | ₹5,570.58 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 11.9d; rzp pay_AUqLTMxhDGYinF status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_Rg5Gex7MH68dD5` | ₹581.30 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 10.5d; rzp pay_Rg5Gex7MH68dD5 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_PYWfLA9cbmyzyY` | ₹179.37 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 10.1d; rzp pay_PYWfLA9cbmyzyY status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_pTACJmaf3IOoBA` | ₹1,162.73 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_b49cb54e7a62de status=expired amount_paid=0 expected>=116273 for pay_pTACJmaf3IOoBA |
| `pay_4GloMZgnoZmfDm` | ₹933.14 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 9.3d; rzp pay_4GloMZgnoZmfDm status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_YlX0580hdgAB7O` | ₹2,770.94 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 13.7d; rzp pay_YlX0580hdgAB7O status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_0JJPUgJUL8tG7G` | ₹2,381.37 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_92e149eff645d4 status=expired amount_paid=0 expected>=238137 for pay_0JJPUgJUL8tG7G |
| `pay_kOLHaQr3PYsJ0d` | ₹626.96 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_93a12c7a2918d6 status=expired amount_paid=0 expected>=62696 for pay_kOLHaQr3PYsJ0d |
| `pay_H9WDRYAZarVQNt` | ₹6,342.26 | failed_verification | payment_link | 1 | cause mandate_expired; mandate_expired: the mandate cannot be re-presented, only re-authorised; rzp plink_5da743adf3e20d status=expired amount_paid=0 expected>=634226 for pay_H9WDRYAZarVQNt |
| `pay_xxWoTemF3JSXFj` | ₹595.57 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_352fd732f0bdeb status=expired amount_paid=0 expected>=59557 for pay_xxWoTemF3JSXFj |
| `pay_QOIeDcIeeh1A0d` | ₹1,554.50 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_6e0ce08cb96fda status=expired amount_paid=0 expected>=155450 for pay_QOIeDcIeeh1A0d |
| `pay_zwiPSaTan5DjCH` | ₹2,218.99 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 13.9d; rzp pay_zwiPSaTan5DjCH status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_a3Xql3yRAQaky3` | ₹417.06 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 9.9d; rzp pay_a3Xql3yRAQaky3 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_DlYH7Pin7pYbJ7` | ₹2,406.77 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 8.7d old: past nudging, issue a fresh link; rzp plink_1e6b13184d9fc9 status=expired amount_paid=0 expected>=240677 for pay_DlYH7Pin7pYbJ7 |
| `pay_Inbffbw6RWCZRL` | ₹1,886.10 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 13.2d old: past nudging, issue a fresh link; rzp plink_81cdbde40579e4 status=expired amount_paid=0 expected>=188610 for pay_Inbffbw6RWCZRL |
| `pay_ZIk1JjuKz6Ya0g` | ₹4,455.02 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 6.3d; rzp pay_ZIk1JjuKz6Ya0g status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_NfXkAV1OieR9Sv` | ₹3,541.67 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 12.3d; rzp pay_NfXkAV1OieR9Sv status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_e7jZw2lXccsSYi` | ₹565.17 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_7b66ae10580ef0 status=expired amount_paid=0 expected>=56517 for pay_e7jZw2lXccsSYi |
| `pay_TqAS0kpMeiQog9` | ₹461.72 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_TqAS0kpMeiQog9' AND kind = 'escalate' |
| `pay_SETOHsRZ4w21IR` | ₹2,271.24 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_3f1ce059021ca0 status=created amount_paid=0 expected>=227124 for pay_SETOHsRZ4w21IR |
| `pay_nhPDWZMTIrpOOf` | ₹537.16 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 5.4d old: past nudging, issue a fresh link; rzp plink_d9830e739f9e90 status=created amount_paid=0 expected>=53716 for pay_nhPDWZMTIrpOOf |
| `pay_d8euUtQn7ewTWF` | ₹587.61 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 5.7d; rzp pay_d8euUtQn7ewTWF status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_46eeJSkEqKb8FC` | ₹608.46 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_d396347a8adfed status=expired amount_paid=0 expected>=60846 for pay_46eeJSkEqKb8FC |
| `pay_H5pPLbzkHBGxLi` | ₹9,741.86 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_H5pPLbzkHBGxLi' AND kind = 'escalate' |
| `pay_Mt7lEy2VILh2n5` | ₹1,394.01 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 13.3d; rzp pay_Mt7lEy2VILh2n5 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_hkiolUtPsvwTv8` | ₹1,506.97 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_d8b055263b1b43 status=expired amount_paid=0 expected>=150697 for pay_hkiolUtPsvwTv8 |
| `pay_pFmCsZiqbpcjdo` | ₹2,947.93 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_pFmCsZiqbpcjdo' AND kind = 'escalate' |
| `pay_ycnz31CXzyHJPG` | ₹1,573.76 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 5.6d; rzp pay_ycnz31CXzyHJPG status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_ptYCqivvHNEyGF` | ₹1,547.80 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_ptYCqivvHNEyGF' AND kind = 'escalate' |
| `pay_NzJ4MGFw6ZoP4q` | ₹1,209.88 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 5.7d; rzp pay_NzJ4MGFw6ZoP4q status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_HZ0w0YeU1sItZ5` | ₹851.09 | failed_verification | payment_link | 1 | cause mandate_expired; mandate_expired: the mandate cannot be re-presented, only re-authorised; rzp plink_69ce72e4b84664 status=expired amount_paid=0 expected>=85109 for pay_HZ0w0YeU1sItZ5 |
| `pay_NFp8xWrEzUAnIR` | ₹1,607.05 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 11.3d; rzp pay_NFp8xWrEzUAnIR status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_aBsvV1W2eFUT38` | ₹1,301.57 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_d18f88f1c12c56 status=expired amount_paid=0 expected>=130157 for pay_aBsvV1W2eFUT38 |
| `pay_6RYV7F1nmotIEE` | ₹776.81 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 2.8d; rzp pay_6RYV7F1nmotIEE status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_FHdKObHEWd6iEN` | ₹1,136.40 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_f6cdebceef7209 status=expired amount_paid=0 expected>=113640 for pay_FHdKObHEWd6iEN |
| `pay_7TZVpBXKzAlPci` | ₹320.67 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 9.6d; rzp pay_7TZVpBXKzAlPci status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_EXSprkbegqWgib` | ₹6,236.70 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 5.1d; rzp pay_EXSprkbegqWgib status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_rXeW9n2Hf2modc` | ₹467.13 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_c126632a139571 status=expired amount_paid=0 expected>=46713 for pay_rXeW9n2Hf2modc |
| `pay_BxzFPKK3wOBFFM` | ₹781.35 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_c031b0dfd415d2 status=expired amount_paid=0 expected>=78135 for pay_BxzFPKK3wOBFFM |
| `pay_cdymzdaA5N0cuf` | ₹320.89 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_cdymzdaA5N0cuf' AND kind = 'escalate' |
| `pay_BTws1qdTEombEx` | ₹1,678.95 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 10.0d; rzp pay_BTws1qdTEombEx status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_grTylZOXyrW3ci` | ₹6,209.64 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_cd16cbdbd99b51 status=expired amount_paid=0 expected>=620964 for pay_grTylZOXyrW3ci |
| `pay_VwPCC9OT26SmYR` | ₹834.21 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 4.7d; rzp pay_VwPCC9OT26SmYR status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_kasaFgywWNuxN2` | ₹2,957.67 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 13.1d; rzp pay_kasaFgywWNuxN2 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_InxalQRafdFAVs` | ₹6,725.51 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_c6c3c949e69def status=expired amount_paid=0 expected>=672551 for pay_InxalQRafdFAVs |
| `pay_bxjb2lUY614iIK` | ₹12,253.04 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 4.8d; rzp pay_bxjb2lUY614iIK status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_jh719ezCaFZSfr` | ₹494.52 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 11.3d; rzp pay_jh719ezCaFZSfr status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_Sl1t6V01QfbBFx` | ₹4,012.48 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_Sl1t6V01QfbBFx' AND kind = 'escalate' |
| `pay_4xquOcz75JqiZK` | ₹6,263.37 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 8.0d; rzp pay_4xquOcz75JqiZK status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_7pKLLSsrkaMEfp` | ₹563.23 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 7.8d; rzp pay_7pKLLSsrkaMEfp status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_301baT8LJR50U0` | ₹542.64 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_36c0582e19df54 status=expired amount_paid=0 expected>=54264 for pay_301baT8LJR50U0 |
| `pay_E46BmOFzcOLTnl` | ₹1,653.55 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_E46BmOFzcOLTnl' AND kind = 'escalate' |
| `pay_Iii3rKpF8aczsb` | ₹1,452.40 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_Iii3rKpF8aczsb' AND kind = 'escalate' |
| `pay_XdEnqJitG01DPF` | ₹3,409.01 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_9c3ce3ba58609d status=expired amount_paid=0 expected>=340901 for pay_XdEnqJitG01DPF |
| `pay_yNDN739fHq3aAQ` | ₹868.19 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 1.1d old: past nudging, issue a fresh link; rzp plink_ac222a8b2b0a68 status=created amount_paid=0 expected>=86819 for pay_yNDN739fHq3aAQ |
| `pay_WxFBfnyilER8bk` | ₹587.67 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_WxFBfnyilER8bk' AND kind = 'escalate' |
| `pay_XZ3Q8396PylM9o` | ₹2,163.39 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_f000116f313be0 status=expired amount_paid=0 expected>=216339 for pay_XZ3Q8396PylM9o |
| `pay_fUiCFqEiKWw3cU` | ₹968.14 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 3.3d; rzp pay_fUiCFqEiKWw3cU status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_GmyPq3HIeU69bx` | ₹724.71 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 5.9d; rzp pay_GmyPq3HIeU69bx status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_7zkjAXQmEhXeZG` | ₹484.77 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_24eadb3f251dd0 status=expired amount_paid=0 expected>=48477 for pay_7zkjAXQmEhXeZG |
| `pay_8mdnhr6AT2DwBo` | ₹341.19 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_b1803d57406d26 status=expired amount_paid=0 expected>=34119 for pay_8mdnhr6AT2DwBo |
| `pay_UJISrjHxfIyyN6` | ₹4,478.62 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 12.3d; rzp pay_UJISrjHxfIyyN6 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_QGfvJa9dX03XHn` | ₹11,920.64 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 6.2d; rzp pay_QGfvJa9dX03XHn status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_Fn9TMXpqcaYNTH` | ₹1,492.72 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_a4c313fa72f21f status=created amount_paid=0 expected>=149272 for pay_Fn9TMXpqcaYNTH |
| `pay_qX4ySEioNCeCtm` | ₹1,771.57 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_586d4b1e99b7c1 status=expired amount_paid=0 expected>=177157 for pay_qX4ySEioNCeCtm |
| `pay_nidWr5F1jukqno` | ₹6,799.52 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 12.2d; rzp pay_nidWr5F1jukqno status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_e4PPqOPPMgIqe1` | ₹1,552.22 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 5.6d; rzp pay_e4PPqOPPMgIqe1 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_H0wulG7GwsTqZu` | ₹4,445.38 | unresolved | nudge | 1 | cause checkout_dropoff; checkout_dropoff 14h old: remind while the intent is warm; 1 row(s) in attempts where payment_id = 'pay_H0wulG7GwsTqZu' AND kind = 'nudge' |
| `pay_jJDs1p44Opbz23` | ₹1,168.25 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 11.4d; rzp pay_jJDs1p44Opbz23 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_byLsU67UlGZmnV` | ₹3,762.58 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 3.1d; rzp pay_byLsU67UlGZmnV status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_c0S9vYwwiru70l` | ₹1,561.27 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_c0S9vYwwiru70l' AND kind = 'escalate' |
| `pay_zBDLSy17fJ3ohS` | ₹4,330.02 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_3bae3838b93b4f status=expired amount_paid=0 expected>=433002 for pay_zBDLSy17fJ3ohS |
| `pay_Jg3uYdR7wqStex` | ₹14,699.00 | failed_verification | payment_link | 1 | cause mandate_expired; mandate_expired: the mandate cannot be re-presented, only re-authorised; rzp plink_d0146ed9f58c16 status=expired amount_paid=0 expected>=1469900 for pay_Jg3uYdR7wqStex |
| `pay_bTlV87tzEHVHa9` | ₹3,211.65 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_0ae62b6e634426 status=created amount_paid=0 expected>=321165 for pay_bTlV87tzEHVHa9 |
| `pay_llUk4Yu62UsyIx` | ₹1,839.11 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 9.3d; rzp pay_llUk4Yu62UsyIx status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_B0TDQOGb5nOOGk` | ₹135.72 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 12.3d old: past nudging, issue a fresh link; rzp plink_f5946ae90ce271 status=expired amount_paid=0 expected>=13572 for pay_B0TDQOGb5nOOGk |
| `pay_s1rCefoKzSeE2b` | ₹4,013.11 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_290ae85e07591d status=expired amount_paid=0 expected>=401311 for pay_s1rCefoKzSeE2b |
| `pay_3TZeXfMgOeLuh6` | ₹11,798.23 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_9d1664d030ea9c status=created amount_paid=0 expected>=1179823 for pay_3TZeXfMgOeLuh6 |
| `pay_ilAlmvgHNoEGPx` | ₹1,254.88 | unresolved | nudge | 1 | cause checkout_dropoff; checkout_dropoff 16h old: remind while the intent is warm; 1 row(s) in attempts where payment_id = 'pay_ilAlmvgHNoEGPx' AND kind = 'nudge' |
| `pay_OUISqXTkmB2SmQ` | ₹367.28 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_OUISqXTkmB2SmQ' AND kind = 'escalate' |
| `pay_XGmCXgBJVqFwL0` | ₹226.14 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_019c03f224964d status=created amount_paid=0 expected>=22614 for pay_XGmCXgBJVqFwL0 |
| `pay_W9T4wztIhPSNi4` | ₹6,609.94 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_e7115544e13ae8 status=expired amount_paid=0 expected>=660994 for pay_W9T4wztIhPSNi4 |
| `pay_CpW5SaThRpZrSc` | ₹181.08 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_02fab50699c5f6 status=expired amount_paid=0 expected>=18108 for pay_CpW5SaThRpZrSc |
| `pay_OnBFreGd6YiafC` | ₹239.98 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_OnBFreGd6YiafC' AND kind = 'escalate' |
| `pay_kNrKqms6SqY3zv` | ₹268.95 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 1.7d; rzp pay_kNrKqms6SqY3zv status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_Ip4UpL9izGoAlx` | ₹1,582.75 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 11.7d; rzp pay_Ip4UpL9izGoAlx status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_7MCvKuAHWFdVte` | ₹5,657.36 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 9.2d; rzp pay_7MCvKuAHWFdVte status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_YefNQ00rqfjpAb` | ₹1,945.58 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_f2286f046dc109 status=created amount_paid=0 expected>=194558 for pay_YefNQ00rqfjpAb |
| `pay_JppOdN2nqmD2wf` | ₹1,282.14 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_b2bbad988469f4 status=created amount_paid=0 expected>=128214 for pay_JppOdN2nqmD2wf |
| `pay_r5Jn7X2xTIxZVc` | ₹2,519.98 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_e26a7c5b1a61a2 status=expired amount_paid=0 expected>=251998 for pay_r5Jn7X2xTIxZVc |
| `pay_rAz3Wgo5ofveCh` | ₹2,325.97 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_807758f1fb2259 status=expired amount_paid=0 expected>=232597 for pay_rAz3Wgo5ofveCh |
| `pay_Qwvl59SY7SD7T4` | ₹565.43 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 10.7d old: past nudging, issue a fresh link; rzp plink_cf41aa6e7ca5c9 status=expired amount_paid=0 expected>=56543 for pay_Qwvl59SY7SD7T4 |
| `pay_FdX9CLEi7wGhW8` | ₹687.13 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_7599c3bfe75d1a status=expired amount_paid=0 expected>=68713 for pay_FdX9CLEi7wGhW8 |
| `pay_El0BLoUTAAYgZ8` | ₹1,346.08 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 12.0d old: past nudging, issue a fresh link; rzp plink_864dfcd23accfa status=expired amount_paid=0 expected>=134608 for pay_El0BLoUTAAYgZ8 |
| `pay_ec75ZeGugK2CLd` | ₹289.83 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 3.4d; rzp pay_ec75ZeGugK2CLd status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_bbaWw2SsNAqwU9` | ₹2,753.28 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_bbaWw2SsNAqwU9' AND kind = 'escalate' |
| `pay_iUOxwIwaJHQZ9r` | ₹2,279.73 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_9ace70e97f1f20 status=expired amount_paid=0 expected>=227973 for pay_iUOxwIwaJHQZ9r |
| `pay_8d1Yax8urz47gY` | ₹3,842.21 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_99b81e8b95d18d status=expired amount_paid=0 expected>=384221 for pay_8d1Yax8urz47gY |
| `pay_uG613juRg5xNWZ` | ₹34,076.41 | failed_verification | payment_link | 1 | cause card_expired; card_expired: the instrument is dead, only a fresh link can collect; rzp plink_120e0b7bf956ab status=created amount_paid=0 expected>=3407641 for pay_uG613juRg5xNWZ |
| `pay_oz3X9YtzWaWVZ0` | ₹2,069.05 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_1731187f0a840c status=expired amount_paid=0 expected>=206905 for pay_oz3X9YtzWaWVZ0 |
| `pay_jqi4A8mZ43kAmZ` | ₹648.28 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_37980946ac55c5 status=expired amount_paid=0 expected>=64828 for pay_jqi4A8mZ43kAmZ |
| `pay_vrgjLnY8e3eRt8` | ₹2,556.33 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_23aea8b559d6aa status=expired amount_paid=0 expected>=255633 for pay_vrgjLnY8e3eRt8 |
| `pay_4qXuG18TVf1uWy` | ₹1,676.56 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 5.0d; rzp pay_4qXuG18TVf1uWy status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_SCo6J5RgryT1F3` | ₹1,267.84 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 14.0d old: past nudging, issue a fresh link; rzp plink_7fd51803babbc0 status=expired amount_paid=0 expected>=126784 for pay_SCo6J5RgryT1F3 |
| `pay_5mwsYea3YTwIQV` | ₹1,526.81 | unresolved | nudge | 1 | cause checkout_dropoff; checkout_dropoff 14h old: remind while the intent is warm; 1 row(s) in attempts where payment_id = 'pay_5mwsYea3YTwIQV' AND kind = 'nudge' |
| `pay_1d6wiWGJVe3FjM` | ₹26,614.63 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_89ad2d8c2232f3 status=expired amount_paid=0 expected>=2661463 for pay_1d6wiWGJVe3FjM |
| `pay_PZZrRWfOaufDVj` | ₹529.79 | failed_verification | payment_link | 1 | cause mandate_expired; mandate_expired: the mandate cannot be re-presented, only re-authorised; rzp plink_8aa7e926ceee45 status=expired amount_paid=0 expected>=52979 for pay_PZZrRWfOaufDVj |
| `pay_GnUqSLQss4ZEyP` | ₹3,406.84 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_GnUqSLQss4ZEyP' AND kind = 'escalate' |
| `pay_59d79lQJfgvI78` | ₹3,083.50 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 6.9d; rzp pay_59d79lQJfgvI78 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_vOAiJfdON1G1io` | ₹6,973.29 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 6.0d; rzp pay_vOAiJfdON1G1io status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_y4ODIohWsNlZIw` | ₹641.08 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_y4ODIohWsNlZIw' AND kind = 'escalate' |
| `pay_z5IazTPBhiNQnK` | ₹558.11 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 8.5d old: past nudging, issue a fresh link; rzp plink_41f24ba082b6c4 status=expired amount_paid=0 expected>=55811 for pay_z5IazTPBhiNQnK |
| `pay_edBb4AnFgtDtHU` | ₹467.89 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 2.0d old: past nudging, issue a fresh link; rzp plink_914470823e66cc status=expired amount_paid=0 expected>=46789 for pay_edBb4AnFgtDtHU |
| `pay_bh9UAY2Fgl0Ul7` | ₹813.83 | failed_verification | retry | 1 | cause insufficient_funds; insufficient_funds held 2.0d, re-presenting at 6.2d; rzp pay_bh9UAY2Fgl0Ul7 status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_5OfSB6Sm2wIY3W` | ₹1,960.75 | failed_verification | retry | 1 | cause bank_down; bank_down is transient: re-present the same instrument at 2.6d; rzp pay_5OfSB6Sm2wIY3W status=failed expected status=captured (amount not independently confirmed in offline mode) |
| `pay_jRSxy7qfYro6uX` | ₹1,563.30 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_b06c1b05f06ec8 status=expired amount_paid=0 expected>=156330 for pay_jRSxy7qfYro6uX |
| `pay_1okcRLOlqPYlob` | ₹2,204.72 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_105a5450cbd065 status=expired amount_paid=0 expected>=220472 for pay_1okcRLOlqPYlob |
| `pay_NrXcTOSQL2Xiyq` | ₹99.00 | unresolved | escalate | 1 | cause risk_blocked; risk_blocked: compliance escalation to a human, never an automated retry; 1 row(s) in attempts where payment_id = 'pay_NrXcTOSQL2Xiyq' AND kind = 'escalate' |
| `pay_UlQseTbAG4FYpC` | ₹266.90 | failed_verification | payment_link | 1 | cause mandate_expired; mandate_expired: the mandate cannot be re-presented, only re-authorised; rzp plink_e0bd658fdda5bb status=expired amount_paid=0 expected>=26690 for pay_UlQseTbAG4FYpC |
| `pay_OQ4saXtJsOxE41` | ₹2,588.04 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 4.0d old: past nudging, issue a fresh link; rzp plink_4d84e6fe25c51e status=created amount_paid=0 expected>=258804 for pay_OQ4saXtJsOxE41 |
| `pay_7W3qE3Q8I3ffLe` | ₹2,588.26 | unresolved | nudge | 1 | cause checkout_dropoff; checkout_dropoff 14h old: remind while the intent is warm; 1 row(s) in attempts where payment_id = 'pay_7W3qE3Q8I3ffLe' AND kind = 'nudge' |
| `pay_mWbrdUNcfnKcTU` | ₹711.85 | failed_verification | payment_link | 1 | cause checkout_dropoff; checkout_dropoff 2.7d old: past nudging, issue a fresh link; rzp plink_aaaac70d5a76ff status=created amount_paid=0 expected>=71185 for pay_mWbrdUNcfnKcTU |
| `pay_tUDb4imvn67tyI` | ₹2,726.21 | failed_verification | payment_link | 1 | cause auth_failed; auth_failed: the customer must re-authenticate, a silent retry cannot fix an OTP; rzp plink_dbaee719b9de33 status=created amount_paid=0 expected>=272621 for pay_tUDb4imvn67tyI |

