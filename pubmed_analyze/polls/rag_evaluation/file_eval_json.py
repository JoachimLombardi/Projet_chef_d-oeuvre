queries = ["""What were the key findings regarding sex-related differences in disease-modifying treatment (DMT) strategies for people with Multiple Sclerosis (pwMS) 
            based on the study conducted using data from the Austrian Multiple Sclerosis Treatment Registry?""",
         """What is the potential role of microRNAs (miRNAs) in stem cell therapy for treating Multiple Sclerosis (MS), and how do they contribute to the development of new 
            therapeutic strategies?""",
         """What demographic and clinical factors were found to influence long-term disability progression in Latvian Multiple Sclerosis (MS) patients?""",
         """What role do CD11c+ B cells play in the context of Multiple Sclerosis (MS), and how are they affected by anti-CD20 therapy?""",
         """What did the Mendelian randomization study reveal about the causal effects of gut microbiota on Multiple Sclerosis (MS)?""",
         """How do paramagnetic rim lesions (PRLs) and choroid plexus (CP) enlargement relate to cognitive impairment and fatigue in patients with Multiple Sclerosis (MS)?""",
         """What role does autotaxin play in the pathogenesis of Multiple Sclerosis (MS), and how might it serve as a therapeutic target?""",
         """How can artificial intelligence (AI) and machine learning (ML) improve the diagnosis and prediction of Multiple Sclerosis (MS), and what challenges are associated 
            with their implementation?""",
         """What were the findings regarding newly appearing lesions in Multiple Sclerosis (MS) and their evolution into slowly expanding lesions (SELs) in the context of fingolimod 
            treatment?""",
         """What were the key findings of the qualitative study exploring patients' experiences and understanding of Multiple Sclerosis (MS)?"""]
expected_abstracts = ["""Background:Individual disease-modifying treatment (DMT) decisions might differ between female and male people with MS (pwMS). 
                     Objective:To identify sex-related differences in DMT strategies over the past decades in a real-world setting. 
                     Methods:In this cohort study, data from the Austrian Multiple Sclerosis Treatment Registry (AMSTR), a nationwide prospectively collected registry mandatory 
                     for reimbursement, were retrospectively analyzed. Of 4840 pwMS, those with relapsing-remitting MS, aged at least 18 years, who started DMT and had at least 
                     two clinical visits, were identified. At baseline, demographics, Expanded Disability Status Scale (EDSS) score, annualized relapse rate (ARR) in the prior 12 
                     months and MRI lesion load were assessed. At follow-up, ARR, EDSS scores, and DMT were determined. Results:A total of 4224 pwMS were included into the study and
                     had a median of 10 (IQR 5-18) clinical visits over an observation period of 3.5 (IQR 1.5-6.1) years. Multivariable Cox regression analysis revealed that the 
                     probability of DMT escalation due to relapse activity was lower in female than male pwMS (HR 4.1 vs. 8.3 per ARR). 
                     Probability of discontinuing moderate-effective DMT was higher in female pwMS when they were younger (HR 1.03 per year), and lower in male pwMS at higher age 
                     (HR 0.92). Similarly, female pwMS were more likely to stop highly effective DMT than male pwMS (HR 1.7). Among others, the most frequent reason for DMT 
                     discontinuation was family planning in female pwMS. All sex-related effects were independent of disease activity, such as MRI lesion load, baseline ARR or EDSS. 
                     Conclusions:Real-world treatment decisions are influenced by sex-related aspects. Awareness of these associations should prevent unwarranted differences in MS 
                     care.""",
                     """Multiple Sclerosis (MS) is an autoimmune disease of the central nervous system (CNS) characterized by inflammation and demyelination of CNS neurons. 
                     Up to now, there are many therapeutic strategies for MS but they are only being able to reduce progression of diseases and have not got any effect on repair and 
                     remyelination. Stem cell therapy is an appropriate method for regeneration but has limitations and problems. So recently, researches were used of exosomes that 
                     facilitate intercellular communication and transfer cell-to-cell biological information. MicroRNAs (miRNAs) are a class of short non-coding RNAs that we can used 
                     to their dysregulation in order to diseases diagnosis. The miRNAs of microvesicles obtained stem cells may change the fate of transplanted cells based on received 
                     signals of injured regions. The miRNAs existing in MSCs may be displayed the cell type and their biological activities. Current studies show also that the miRNAs 
                     create communication between stem cells and tissue-injured cells. In the present review, firstly we discuss the role of miRNAs dysregulation in MS patients and 
                     miRNAs expression by stem cells. Finally, in this study was confirmed the relationship of microRNAs involved in MS and miRNAs expressed by stem cells and 
                     interaction between them in order to find appropriate treatment methods in future for limit to disability progression.""",
                     """There is wide variation in the time from the onset to secondary progressive multiple sclerosis (MS) and some controversy regarding the clinical 
                     characteristics of the courses (phenotypes) of MS. The present study aimed to characterize demographic and clinical factors that potentially influence 
                     long-term disability progression in the cohort of Latvian MS patients. A descriptive longitudinal incidence study was conducted using a cohort of 288 MS 
                     patients beginning in 2011 (disease duration from 1 to 51 years). Socio-demographic and clinical information from the first visit to 15/20 years was analysed 
                     in groups stratified by gender and visits at five-time points (the first visit; after a year or 2; after 5 ± 1 year; after 10 ± 2 years; after 15-20 years). 
                     Our study was dominated by patients from urban areas and non-smokers. The female/male ratio was 2.4:1; the distribution of clinical courses at the first visit 
                     was consistent with most European studies. The most common symptom at presentation in our study was optic manifestations, followed by sensory disturbances and 
                     motor deficits. In the Latvian study, gender was not a significant influencing factor on the rate of disease progression; however, patient age was statistically 
                     significantly associated with EDSS (Expanded Disability Status Scale) value at the first visit. Early clinical features of MS are important in predicting the 
                     disability accumulation of patients. Despite the small differences regarding the first MS symptoms, the disability outcomes in the cohort of Latvian patients 
                     are similar to other regions of the world.""",
                     """Objectives:B cells are important in the pathogenesis of multiple sclerosis. It is yet unknown which subsets may be involved, but atypical B cells have been proposed as mediators of autoimmunity. 
                     In this study, we investigated differences in B-cell subsets between controls and patients with untreated and anti-CD20-treated multiple sclerosis. Methods:We recruited 
                     155 participants for an exploratory cohort comprising peripheral blood and cerebrospinal fluid, and a validation cohort comprising peripheral blood. 
                     Flow cytometry was used to characterize B-cell phenotypes and effector functions of CD11c+atypical B cells. Results:There were no differences in circulating B cells between 
                     controls and untreated multiple sclerosis. As expected, anti-CD20-treated patients had a markedly lower B-cell count. Of B cells remaining after treatment, we observed higher 
                     proportions of CD11c+B cells and plasmablasts. CD11c+B cells were expanded in cerebrospinal fluid compared to peripheral blood in controls and untreated multiple sclerosis. 
                     Surprisingly, the proportion of CD11c+cerebrospinal fluid B cells was higher in controls and after anti-CD20 therapy than in untreated multiple sclerosis. 
                     Apart from the presence of plasmablasts, the cerebrospinal fluid B-cell composition after anti-CD20 therapy resembled that of controls. CD11c+B cells demonstrated a high 
                     potential for both proinflammatory and regulatory cytokine production. Interpretation:The study demonstrates that CD11c+B cells and plasmablasts are less efficiently depleted 
                     by anti-CD20 therapy, and that CD11c+B cells comprise a phenotypically and functionally distinct, albeit heterogenous, B-cell subset with the capacity of exerting both 
                     proinflammatory and regulatory functions.""",
                     """Background:Gut microbiota alterations in multiple sclerosis (MS) patients have been reported in observational studies, but whether these associations are 
                     causal is unclear. Objective:We performed a Mendelian randomization study (MR) to assess the causal effects of gut microbiota on MS. Methods:Independent genetic 
                     variants associated with 211 gut microbiota phenotypes were selected as instrumental variables from the largest genome-wide association studies (GWAS) previously 
                     published by the MiBioGen study. GWAS data for MS were obtained from the International Multiple Sclerosis Genetics Consortium (IMSGC) for primary analysis and 
                     the FinnGen consortium for replication and collaborative analysis. Sensitivity analyses were conducted to evaluate heterogeneity and pleiotropy. 
                     Results:After inverse-variance-weighted and sensitivity analysis filtering, seven gut microbiota with potential causal effects on MS were identified from the 
                     IMSGC. Only five metabolites remained significant associations with MS when combined with the FinnGen consortium, including genus Anaerofilum id.2053 
                     (odds ratio [OR] = 1.141, 95% confidence interval [CI]: 1.021-1.276, p = .021), Ruminococcus2 id.11374 (OR = 1.190, 95% CI: 1.007-1.406, p = .042), 
                     Ruminococcaceae UCG003 id.11361 (OR = 0.822, 95% CI: 0.688-0.982, p = .031), Ruminiclostridium5 id.11355 (OR = 0.724, 95% CI: 0.585-0.895, p = .003), 
                     Anaerotruncus id.2054 (OR = 0.772, 95% CI: 0.634-0.940, p = .010). Conclusion:Our MR analysis reveals a potential causal relationship between gut microbiota 
                     and MS, offering promising avenues for advancing mechanistic understanding and clinical investigation of microbiota-mediated MS.""",
                     """Background and objectives:Chronic inflammation may contribute to cognitive dysfunction and fatigue in patients with multiple sclerosis (MS). 
                     Paramagnetic rim lesions (PRLs) and choroid plexus (CP) enlargement have been proposed as markers of chronic inflammation in MS being associated with a more 
                     severe disease course. However, their relation with cognitive impairment and fatigue has not been fully explored yet. Here, we investigated the contribution of 
                     PRL number and volume and CP enlargement to cognitive impairment and fatigue in patients with MS. Methods:Brain 3T MRI, neurologic evaluation, and 
                     neuropsychological assessment, including the Brief Repeatable Battery of Neuropsychological Tests and Modified Fatigue Impact Scale, were obtained from 129 
                     patients with MS and 73 age-matched and sex-matched healthy controls (HC). PRLs were identified on phase images of susceptibility-weighted imaging, whereas CP 
                     volume was quantified using a fully automatic method on brain three-dimensional T1-weighted and fluid-attenuated inversion recovery MRI sequences. 
                     Predictors of cognitive impairment and fatigue were identified using random forest. Results:Thirty-six (27.9%) patients with MS were cognitively impaired, 
                     and 31/113 (27.4%) patients had fatigue. Fifty-nine (45.7%) patients with MS had ≥1 PRLs (median = 0, interquartile range = 0;2). Compared with HC, patients 
                     with MS showed significantly higher T2-hyperintense white matter lesion (WM) volume; lower normalized brain, thalamic, hippocampal, caudate, cortical, and WM 
                     volumes; and higher normalized CP volume (pfrom <0.001 to 0.040). The predictors of cognitive impairment (relative importance) (out-of-bag area under the curve 
                     [OOB-AUC] = 0.707) were normalized brain volume (100%), normalized caudate volume (89.1%), normalized CP volume (80.3%), normalized cortical volume (70.3%), 
                     number (67.3%) and volume (66.7%) of PRLs, and T2-hyperintense WM lesion volume (64.0%). Normalized CP volume was the only predictor of the presence of fatigue 
                     (OOB-AUC = 0.563). Discussion:Chronic inflammation, with higher number and volume of PRLs and enlarged CP, may contribute to cognitive impairment in MS in 
                     addition to gray matter atrophy. The contribution of enlarged CP in explaining fatigue supports the relevance of immune-related processes in determining this 
                     manifestation independently of disease severity. PRLs and CP enlargement may contribute to the pathophysiology of cognitive impairment and fatigue in MS, and 
                     they may represent clinically relevant therapeutic targets to limit the impact of these clinical manifestations in MS.""",
                     """Multiple sclerosis (MS) is an immune-mediated inflammatory disease of the CNS. A defining characteristic of MS is the ability of autoreactive T 
                     lymphocytes to cross the blood-brain barrier and mediate inflammation within the CNS. Previous work from our lab found the gene Enpp2 to be highly upregulated 
                     in murine encephalitogenic T cells. Enpp2 encodes for the protein autotaxin, a secreted glycoprotein that catalyzes the production of lysophosphatidic acid 
                     and promotes transendothelial migration of T cells from the bloodstream into the lymphatic system. The present study sought to characterize autotaxin 
                     expression in T cells during CNS autoimmune disease and determine its potential therapeutic value. Myelin-activated CD4 T cells upregulated expression of 
                     autotaxin in vitro, and ex vivo analysis of CNS-infiltrating CD4 T cells showed significantly higher autotaxin expression compared with cells from healthy mice. 
                     In addition, inhibiting autotaxin in myelin-specific T cells reduced their encephalitogenicity in adoptive transfer studies and decreased in vitro cell motility. 
                     Importantly, using two mouse models of MS, treatment with an autotaxin inhibitor ameliorated EAE severity, decreased the number of CNS infiltrating T and B cells, 
                     and suppressed relapses, suggesting autotaxin may be a promising therapeutic target in the treatment of MS.""",
                     """Medical research offers potential for disease prediction, like Multiple Sclerosis (MS). This neurological disorder damages nerve cell sheaths, with treatments focusing on 
                     symptom relief. Manual MS detection is time-consuming and error prone. Though MS lesion detection has been studied, limited attention has been paid to clinical analysis and 
                     computational risk factor prediction. Artificial intelligence (AI) techniques and Machine Learning (ML) methods offer accurate and effective alternatives to mapping MS 
                     progression. However, there are challenges in accessing clinical data and interdisciplinary collaboration. By analyzing 103 papers, we recognize the trends, strengths and 
                     weaknesses of AI, ML, and statistical methods applied to MS diagnosis. AI/ML-based approaches are suggested to identify MS risk factors, select significant MS features, and 
                     improve the diagnostic accuracy, such as Rule-based Fuzzy Logic (RBFL), Adaptive Fuzzy Inference System (ANFIS), Artificial Neural Network methods (ANN), 
                     Support Vector Machine (SVM), and Bayesian Networks (BNs). Meanwhile, applications of the Expanded Disability Status Scale (EDSS) and Magnetic Resonance Imaging (MRI) can 
                     enhance MS diagnostic accuracy. By examining established risk factors like obesity, smoking, and education, some research tackled the issue of disease progression. 
                     The performance metrics varied across different aspects of MS studies: Diagnosis: Sensitivity ranged from 60 % to 98 %, specificity from 60 % to 98 %, and accuracy from 61 % 
                     to 97 %. Prediction: Sensitivity ranged from 76 % to 98 %, specificity from 65 % to 98 %, and accuracy from 62 % to 99 %. Segmentation: Accuracy ranged up to 96.7 %. 
                     Classification: Sensitivity ranged from 78 % to 97.34 %, specificity from 65 % to 99.32 %, and accuracy from 71 % to 97.94 %. Furthermore, the literature shows that combining 
                     techniques can improve efficiency, exploiting their strengths for better overall performance.""",
                     """Background and purpose:Newly appearing lesions in multiple sclerosis (MS) may evolve into chronically active, slowly expanding lesions (SELs), 
                     leading to sustained disability progression. The aim of this study was to evaluate the incidence of newly appearing lesions developing into SELs, 
                     and their correlation to clinical evolution and treatment. Methods:A retrospective analysis of a fingolimod trial in primary progressive MS 
                     (PPMS; INFORMS,NCT00731692) was undertaken. Data were available from 324 patients with magnetic resonance imaging scans up to 3 years after screening. 
                     New lesions at year 1 were identified with convolutional neural networks, and SELs obtained through a deformation-based method. Clinical disability was assessed 
                     annually by Expanded Disability Status Scale (EDSS), Nine-Hole Peg Test, Timed 25-Foot Walk, and Paced Auditory Serial Addition Test. Linear, logistic, 
                     and mixed-effect models were used to assess the relationship between the Jacobian expansion in new lesions and SELs, disability scores, and treatment status. 
                     Results:One hundred seventy patients had ≥1 new lesions at year 1 and had a higher lesion count at screening compared to patients with no new lesions 
                     (median = 27 vs. 22, p = 0.007). Among the new lesions (median = 2 per patient), 37% evolved into definite or possible SELs. Higher SEL volume and count were 
                     associated with EDSS worsening and confirmed disability progression. Treated patients had lower volume and count of definite SELs (β = -0.04, 95% confidence 
                     interval [CI] = -0.07 to -0.01, p = 0.015; β = -0.36, 95% CI = -0.67 to -0.06, p = 0.019, respectively). Conclusions:Incident chronic active lesions are common 
                     in PPMS, and fingolimod treatment can reduce their number.""",
                     """Introduction:Multiple sclerosis (MS), a leading cause of disability in young adults worldwide, including in Iran, affects their whole life so common care 
                     is no longer effective. In this regard, context-based approaches should be considered for a holistic care delivery that accords with the patients' inputs. 
                     We aimed to explore patients' understanding of MS and their personal experiences of living with this disease. Methods:A qualitative descriptive study was 
                     conducted. The data were collected through in-depth, semi-structured interviews with 17 patients. These patients were selected using a purposive sampling method, 
                     and the data were analyzed using a conventional content analysis approach. Findings:Three main categories and nine subcategories were identified: Thunder and 
                     Lightning strike in the form of Displeasure, Social wrong beliefs, Experiences of Constraints, Interference with Life Stages and Dark Spots on the Horizon of the 
                     Future; Subtle Beam consisting of Extrinsic Light Radiation, Reflection of Individual Effort and Formation of a Rainbow by Resilience and Hope for a Bright Future. 
                     Conclusion:By offering multidimensional support, patients reported a shift from fear to a vibrant life. Although research often focuses on the negative aspects of MS, 
                     this study recognizes both positive and negative aspects. These findings can contribute to future interventional research. Patient or public contribution:During the 
                     explanation of research goals and consent acquisition, participants were reminded that sharing their experiences could provide valuable insights benefiting others 
                     coping with or at risk of the same disease. Additionally, during data analysis, codes extracted were reviewed and improved with active participant involvement."""]