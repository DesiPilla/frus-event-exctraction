# Political Text Analysis & Event Extraction
The project will focus on automated ‘text-as-data’ methods for the extrac-tion of discrete political (cooperative and conflictive) interactions (i.e., “who did what to whom, and  where/when”) from a large corpora of political texts. Such extracted events are commonly known as political “event data” in the literature. Examples of already-coded event datasets appear in several of the readings below, as well as here: http://eventdata.utdallas.edu/. These extracted political events are typically assigned a geolocation and a date of occurrence down to the calender-day, along with information on each source/target actor for the event (e.g., SYR-Government→SYR-Rebel) and action type (e.g., express intent to cooperate, or impose curfew, or use chemical weapons, etc.).

This special project’s tasks in this case will entail setting up and modifying a variety of existing open source software (found here
https://github.com/openeventdata/phoenix_pipeline) to fully processes and code a large corpus of U.S. diplomatic cables. 
The specific tasks in this regard will entail that we:
 1. Re-structure the raw U.S. diplomatic cables (currently structured as CSV files) into a MongoDB.
 2. Parse the text of each diplomatic cable via Stanford CoreNLP.
 3. Pass the parsed text to a Python-based event coder, such as PETRARCH or PETRARCH2.
 4. Separately pass the parsed text through automated geolocation extraction software such as Mordacai or CLIFF/CLAVIN.
 5. Combine all final data and code into a single GitHub repository.


## Data
The data were scraped from the US State DEpartment FRUS website using R. The title and subtitle are higher-level grouping terms to disambiguate unique documents. The data includes every foreign-policy related document from President Lincoln to President Ford. Each document includes a title, subtitle, document title, body (text), date, and the corresponding president. Additional descriptive columns computed and added for each document include:
* decade
* number of words
  * Total number of entities after splitting on whitespace
* number of capitalized words
  * Determined using a regular expression `'((?<!^)(?<!\. )[A-Z][a-z]+)'`
* percentage of capitalized words 
* language
  * Computed by the passing in the first 100 characters of a document’s body text into the function `langdetect.detect()`.
* unique ID
  * Integer from 1 to 323,294.

The body text was also cleaned by removing irrelevant information. All matches with the regular expression `r'[([]\s?Page\s\d+\s?[)\]]'` were replaced with an empty string, as the page number was often found in the document body but does not add any significant information to the document.

Some documents had missing or incorrect date information (such as September 31st, 1943 or October 8). These documents were removed from the full set of documents, as there were very few of them (58 documents, ~0.018%). The remaining number of documents was 323,294.

We chose to truncate all documents to 1600 words before being processed. This was also chosen due to hardware limitations and to avoid bottlenecks created by one-off documents with extremely long bodies. This number was chosen empirically, after a few hundred had already been parsed. As such, a few number of documents were processed with longer word counts than the stated 1600. This number is not believed to have significant negative effects on the efficacy of parse results. It is standard practice in existing event extractors to use only the first 6 sentences of a text. Of the documents parsed, the first 44.7 sentences of a document were parsed on average, with only 2.6% of documents falling below the 6 sentence threshold. For these reasons, we are comfortable with this criteria for truncating document text.

### Data Exploration

[ INSERT FIGURE 1 ]

**Figure 1:** The distribution of document length is displayed in the histogram above. The distribution is heavily right-skewed. Note that the word count data was clipped at 3,000, which can be seen by the spike at the right-tail of the figure. This represents the 2.49% of documents with word-counts over 3,000. 

[ INSERT FIGURE 2 ]

**Figure 2:** The figure above shows the number of documents available by decade, on a log scale. Notice how the number of documents is very small before 1860 (less than 200 per decade). These documents are dated from before any of the presidents served in office, yet were still assigned to one of the presidents in our dataset. Beginning in 1860, the number of documents per decade ranged from 10,000 to 100,000. However, this number rapidly declined beginning in 1970. This marks the end of the terms served by presidents in our document. Gradual declines from 1940 are partially due to some documents not yet being declassified by the US Department of State, as they are more recent.

[ INSERT FIGURE 3 ]

**Figure 3:** The above chart displays the median word count for documents by decade. Aside from 1790 (which only contained a few documents), the word count was relatively similar from 1800 to 1920. There was an increase from 1870-1890. In 1920, the document length began rising rapidly. This comes shortly after the design of the typewriter became standardized.

[ INSERT FIGURE 4 ]

**Figure 4:** The above figure shows the most common word types for documents relating to the Taft administration. The most common were IN (preposition), NNP (Proper Noun, singular), NN (noun, singular), DT (determiner), JJ (adjective), NNS (noun, plural). These word tags were assigned using the `nltk.pos_tag` module.


## Methodology
Analyses were limited to only those documents pertaining to Presidents Kennedy, Johnson, Nixon, and Ford (combined as Nixon-Ford). This was again due to computing environment constraints, as well as cost limitations. In total, 39,826 documents were parsed (12.3% of all available documents).

The analysis for this project was carried out in Python and made use of Natural Language Processing modules that are readily available. [`Stanza`](https://github.com/stanfordnlp/stanza) is the official library created by Stanford NLP Group for using the Java Stanford CoreNLP software. It provides a Python interface for accessing the neural pipelines. We chose this package, as it allowed us to load a neural pipeline within the RAM constraints of AWS Lambda functions (which was 3 GB during this course, though has [since been increased to 10 GB](https://aws.amazon.com/about-aws/whats-new/2020/12/aws-lambda-supports-10gb-memory-6-vcpu-cores-lambda-functions/#:~:text=AWS%20Lambda%20customers%20can%20now,previous%20limit%20of%203%2C008%20MB.&text=Since%20Lambda%20allocates%20CPU%20power,to%20up%20to%.)). The neural pipeline in stanza can be accessed using:
```
stanza.Pipeline('en', '.', processors="tokenize, pos, lemma, ner, depparse") 
```
In this pipeline, the `depparse` annotator does not provide adequate information required by Petrach2. However, there were no environments at the time that supported the full Stanford CoreNLP network (8 GB) that could be reasonably scaled. For this reason, we elected to use the smaller pipeline to glean some summary statistics of the parsed documents as an exploratory analysis. 

Two environments were used to conduct the document analysis for this project. Foremostly, a suite of AWS applications hosted most of the computing. The preprocessed documents are stored in an S3 bucket. All documents were pushed to a queue in SQS to prepare for parsing. A Lambda function was tasked with fetching these documents, parsing them, and storing them in the S3 bucket. Object keys were created using the notation `parsed/{president}/{decade}/{uid}.json`. All services were located within the same VPC network and accessed the same EC2 instance. Python packages were stored in an elastic file system

This process was parallelized using *provisioned concurrency*. [Provisioned concurrency](https://lumigo.io/blog/provisioned-concurrency-the-end-of-cold-starts/) essentially creates a virtual machine for a specified number of Lambda functions, each with the initialization code (all lines before the handler function) already run. This eliminates cold starts, which for our Lambda function–specifically version 32–includes loading the neural pipeline. Allocating provisioned concurrency is expensive and must be turned off immediately once all processing is complete. We learned this the hard way, leaving 100 provisioned concurrency running for a week and accumulating a $1,500 bill. The cost for processing the 39,826 documents is roughly $200 when executed properly.

[ INSERT FIGURE 4 ]

*Figure 4:** Example view of documents being processed. The above figures shot snapshots of the SQS queue monitored in AWS CloudWatch. As the number of concurrent workers increases, the rate of document processing increases.

However, there were still many scalability issues. Because of the size of the [EFS](https://aws.amazon.com/blogs/aws/new-a-shared-file-system-for-your-lambda-functions/) (a feature that only recently was given support for Lamba), the *throughput utilization* limited the ability to provision many concurrent states at once. At most, we could provision 5 new concurrent states every 10-20 minutes to remain within the limitations (see Figure 5). Though not as quick as provisioning 100 concurrent states at once, the processing speed gets quite fast when 75 or more concurrent states are running synchronously. 

[ INSERT FIGURE 5 ]

This was only one issue; the second was more dire, creating a bottleneck that limited the overall ability to process documents in parallel. When using provisioned concurrency, the *CPU credit* balance of the EC2 begins to get used. [An EC2 is initially allotted 576 of CPU credit](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-credits-baseline-concepts.html) (for a `t2.medium` EC2 instance). When an EC2 is not in use, any eroded CPU credit slowly regenerates, up to the original 576 (see Figure 6). Larger EC2 instances have higher maximum credit accruals and quicker accrual rates, yet they tend to become expensive. During this project, we used all 576 of CPU credit, essentially eliminating all functionality of the EC2 and, therefore, our AWS setup. The remaining 5,000 documents pertaining to cold war presidents were carried out with much less parallelization. The Lambda function code was transferred to a Google Collab notebook. By making use of the `multiprocessing` python module, up to 2 documents were able to be processed in parallel. By creating multiple copies of this notebook and running them together, higher parallelization was achievable. The approximate document parsing speeds are shown in Table 1. Note that the queue containing unparsed documents was unaffected by the issues presented by the EFS and EC2.

[ INSERT TABLE 1 ]

**Table 1:** Approximate document parsing speeds when parallelizing the Lambda function in Google Collab.


## Results
In total, 39,826 documents from the Kennedy, Johnson, Nixon, and Ford administrations were parsed. Though those administrations took place from 1961–1976, the documents ranged from 1925–1981.

[ INSERT FIGURE 7 ]

**Figure 7:** The above histograms show the lengths of documents parsed. The left figure shows the difference between the word count of the original documents and the truncated documents (that were parsed by `stanza`). The right figure shows the stacked distribution of truncated word count by cold-war-era  president.

Table 2 displays a variety of summary statistics from the Stanford CoreNLP results. Appendix A contains figures related to this table.

[ INSERT TABLE 2 ]

**Table 2:** The above table highlights some statistics of the text parsing. Notable, 16.08% of all cold-war-era documents were truncated. However, the average document had 44.7 sentences parsed, which should be enough to extract the events of the document. *Entities* refers to all words, punctuation, abbreviations, etc. output by stanza. Lastly, nearly 50 unique proper nouns were referenced in the average document.

Across each cold-war-era president, the most common terminology remained relatively unchanged. These included general language such as *president*, *US*, *United (States)*, *U.S.*, etc. However, a few administration-specific terms were noticeably prevalent. Specifically, the terms *Johnson* and *Vietnam* were popular during President Johnson’s term, and the terms *Kissinger* (the Secretary of State at the time) and *Nixon* were habitually used during President Nixon’s term. Table 3 provides a list of the frequently used proper nouns found in the parsed documents. Appendix B provides more comprehensive details of the term frequencies for each president.

[ INSERT TABLE 3 ]

**Table 3:** Most common proper nouns found in documents from each cold-war-era president. Italicized and bolded terms for each president are those that were not among the 10 most common proper nouns across all cold war presidents.

Let’s look at an example of the parse results obtained by `stanza`. Given the following text:
```
Javanese Grand Waffalo Shinzo Abesson has asked the colonial vizarate to look into the alleged spying activities on the Javanese tribes and companies raised by the Wikileaks website in telephone talks with colonial vizar Joel Bowden Wednesday, local media reported.
```
we get the results
```
[	# List of sentences
  [	# List of entities within a sentence
    {	# First entity within sentence 1
      "id": 1,					# Entity ID within the sentence
      "text": "Javanese",				# Original text
      "lemma": "javanese",			# Lemma of the text
      "upos": "ADJ",				# Universal position tag
      "xpos": "JJ",				# Tree-bank specific tag
      "feats": "Degree=Pos",			# Morphological features
      "head": 2,					# ID of parent word
      "deprel": "amod",				# Dependency b/w text and head
      "misc": "start_char=0|end_char=8",	# Location of text
      "ner": "S-NORP"				# Named entity tag
    },
    {	# Second entity within sentence 1
      "id": 2,
      "text": "Grand",
      "lemma": "Grand",
      "upos": "PROPN",
      "xpos": "NNP",
      "feats": "Number=Sing",
      "head": 3,
      "deprel": "compound",
      "misc": "start_char=9|end_char=14",
      "ner": "O"
    },
  ...	# Remaining entities within sentence 1
  ],
...	# Remaining sentences within text
]
```

The parse result for this document needed in order to pass the document into an event encoder pipeline such as [`Petrach2`](https://github.com/openeventdata/petrarch2/tree/master/petrarch2) is shown in Appendix C.


